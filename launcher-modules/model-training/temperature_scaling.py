#!/usr/bin/env python3
"""
Temperature Scaling and Soft Target Computation Module
Implements advanced temperature scaling techniques for knowledge distillation
Supports adaptive temperature, calibration, and optimal temperature search
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
from typing import Dict, List, Optional, Tuple, Union, Callable
from dataclasses import dataclass
from enum import Enum
import logging
from pathlib import Path
import json
import matplotlib.pyplot as plt
from sklearn.calibration import calibration_curve
from sklearn.metrics import log_loss, brier_score_loss

class TemperatureMethod(Enum):
    """Temperature scaling methods"""
    FIXED = "fixed"  # Fixed temperature parameter
    ADAPTIVE = "adaptive"  # Adaptive temperature based on input
    LAYER_WISE = "layer_wise"  # Different temperature per layer
    TOKEN_WISE = "token_wise"  # Different temperature per token
    LEARNED = "learned"  # Learn temperature as a parameter
    CALIBRATED = "calibrated"  # Calibrated using validation data

@dataclass
class TemperatureConfig:
    """Configuration for temperature scaling"""
    method: TemperatureMethod = TemperatureMethod.FIXED
    initial_temperature: float = 2.0
    min_temperature: float = 0.1
    max_temperature: float = 10.0
    num_temperature_layers: int = 12  # For layer-wise temperature
    calibration_epochs: int = 10
    calibration_lr: float = 0.01
    temperature_schedule: str = "constant"  # constant, linear, cosine
    use_soft_targets: bool = True
    confidence_threshold: float = 0.9
    entropy_weight: float = 0.1

class TemperatureScaler:
    """Temperature scaling for knowledge distillation"""

    def __init__(self, config: TemperatureConfig):
        self.config = config
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.logger = logging.getLogger('DuckBot.TemperatureScaler')

        # Initialize temperature parameters
        self.temperature_params = None
        self._initialize_temperature()

        # Calibration data
        self.calibration_logits = []
        self.calibration_labels = []

        self.logger.info("TemperatureScaler initialized")

    def _initialize_temperature(self):
        """Initialize temperature parameters based on method"""
        if self.config.method == TemperatureMethod.FIXED:
            self.temperature_params = nn.Parameter(
                torch.tensor(self.config.initial_temperature, device=self.device),
                requires_grad=self.config.method == TemperatureMethod.LEARNED
            )
        elif self.config.method == TemperatureMethod.LAYER_WISE:
            self.temperature_params = nn.Parameter(
                torch.full(
                    (self.config.num_temperature_layers,),
                    self.config.initial_temperature,
                    device=self.device
                ),
                requires_grad=self.config.method == TemperatureMethod.LEARNED
            )
        elif self.config.method == TemperatureMethod.TOKEN_WISE:
            # Token-wise temperature will be computed dynamically
            self.temperature_params = None
        elif self.config.method == TemperatureMethod.ADAPTIVE:
            # Adaptive temperature will have a small network to predict temperature
            self.temperature_params = nn.Parameter(
                torch.tensor(self.config.initial_temperature, device=self.device),
                requires_grad=True
            )
        elif self.config.method == TemperatureMethod.LEARNED:
            self.temperature_params = nn.Parameter(
                torch.tensor(self.config.initial_temperature, device=self.device),
                requires_grad=True
            )
        elif self.config.method == TemperatureMethod.CALIBRATED:
            # Temperature will be calibrated on validation data
            self.temperature_params = nn.Parameter(
                torch.tensor(self.config.initial_temperature, device=self.device),
                requires_grad=False
            )

    def get_temperature(self, logits: Optional[torch.Tensor] = None, layer_idx: Optional[int] = None) -> torch.Tensor:
        """Get temperature value(s)"""
        if self.config.method == TemperatureMethod.FIXED:
            return self.temperature_params
        elif self.config.method == TemperatureMethod.LAYER_WISE:
            if layer_idx is not None:
                return self.temperature_params[layer_idx]
            else:
                return self.temperature_params.mean()
        elif self.config.method == TemperatureMethod.TOKEN_WISE:
            return self._compute_token_wise_temperature(logits)
        elif self.config.method == TemperatureMethod.ADAPTIVE:
            return self._compute_adaptive_temperature(logits)
        elif self.config.method == TemperatureMethod.LEARNED:
            return self.temperature_params
        elif self.config.method == TemperatureMethod.CALIBRATED:
            return self.temperature_params
        else:
            return torch.tensor(self.config.initial_temperature, device=self.device)

    def _compute_token_wise_temperature(self, logits: torch.Tensor) -> torch.Tensor:
        """Compute token-wise temperature based on entropy"""
        if logits is None:
            return torch.tensor(self.config.initial_temperature, device=self.device)

        # Compute entropy for each token
        probs = F.softmax(logits, dim=-1)
        entropy = -torch.sum(probs * torch.log(probs + 1e-8), dim=-1)

        # Normalize entropy to [0, 1]
        max_entropy = torch.log(torch.tensor(logits.size(-1), device=self.device))
        normalized_entropy = entropy / max_entropy

        # Map entropy to temperature range
        # High entropy -> Low temperature (more smoothing)
        # Low entropy -> High temperature (less smoothing)
        temperature = self.config.min_temperature + (self.config.max_temperature - self.config.min_temperature) * (1 - normalized_entropy)

        return temperature.unsqueeze(-1)  # Add dimension for broadcasting

    def _compute_adaptive_temperature(self, logits: torch.Tensor) -> torch.Tensor:
        """Compute adaptive temperature based on input statistics"""
        if logits is None:
            return self.temperature_params

        # Compute statistics of logits
        logits_std = torch.std(logits, dim=-1)
        logits_max = torch.max(logits, dim=-1)[0]
        logits_min = torch.min(logits, dim=-1)[0]
        logits_range = logits_max - logits_min

        # Adaptive temperature based on statistics
        # High variance/low confidence -> Lower temperature
        # Low variance/high confidence -> Higher temperature
        confidence_factor = 1.0 / (1.0 + logits_std)
        range_factor = logits_range / (logits_range + 1.0)

        adaptive_temp = self.temperature_params * confidence_factor * range_factor
        adaptive_temp = torch.clamp(adaptive_temp, self.config.min_temperature, self.config.max_temperature)

        return adaptive_temp

    def apply_temperature_scaling(self, logits: torch.Tensor, temperature: Optional[torch.Tensor] = None, layer_idx: Optional[int] = None) -> torch.Tensor:
        """Apply temperature scaling to logits"""
        if temperature is None:
            temperature = self.get_temperature(logits, layer_idx)

        # Apply temperature scaling
        scaled_logits = logits / temperature

        return scaled_logits

    def compute_soft_targets(self, logits: torch.Tensor, temperature: Optional[torch.Tensor] = None, layer_idx: Optional[int] = None) -> torch.Tensor:
        """Compute soft targets using temperature scaling"""
        if not self.config.use_soft_targets:
            return F.softmax(logits, dim=-1)

        # Apply temperature scaling
        scaled_logits = self.apply_temperature_scaling(logits, temperature, layer_idx)

        # Compute soft targets
        soft_targets = F.softmax(scaled_logits, dim=-1)

        return soft_targets

    def compute_soft_labels(self, logits: torch.Tensor, temperature: Optional[torch.Tensor] = None, layer_idx: Optional[int] = None) -> torch.Tensor:
        """Compute soft labels (log probabilities)"""
        soft_targets = self.compute_soft_targets(logits, temperature, layer_idx)
        soft_labels = torch.log(soft_targets + 1e-8)

        return soft_labels

    def add_calibration_data(self, logits: torch.Tensor, labels: torch.Tensor):
        """Add calibration data for temperature calibration"""
        self.calibration_logits.append(logits.cpu().detach())
        self.calibration_labels.append(labels.cpu().detach())

    def calibrate_temperature(self, validation_logits: List[torch.Tensor], validation_labels: List[torch.Tensor]) -> float:
        """Calibrate temperature using validation data"""
        self.logger.info("Calibrating temperature...")

        # Concatenate all validation data
        all_logits = torch.cat(validation_logits, dim=0)
        all_labels = torch.cat(validation_labels, dim=0)

        # Optimize temperature on validation set
        if self.config.method == TemperatureMethod.CALIBRATED:
            return self._optimize_temperature_validation(all_logits, all_labels)
        else:
            return self._optimize_temperature_nll(all_logits, all_labels)

    def _optimize_temperature_validation(self, logits: torch.Tensor, labels: torch.Tensor) -> float:
        """Optimize temperature using validation set calibration"""
        best_temperature = self.config.initial_temperature
        best_score = float('inf')

        # Grid search for optimal temperature
        temperatures = torch.linspace(self.config.min_temperature, self.config.max_temperature, 100)

        for temp in temperatures:
            # Apply temperature scaling
            scaled_logits = logits / temp

            # Compute calibration metrics
            probs = F.softmax(scaled_logits, dim=-1)

            # Expected Calibration Error (ECE)
            ece = self._compute_ece(probs, labels)

            # Negative Log Likelihood
            nll = F.cross_entropy(scaled_logits, labels)

            # Combined score
            score = ece + 0.1 * nll

            if score < best_score:
                best_score = score
                best_temperature = temp.item()

        # Update temperature parameter
        if self.temperature_params is not None:
            self.temperature_params.data.fill_(best_temperature)

        self.logger.info(f"Optimal temperature found: {best_temperature:.4f}")
        return best_temperature

    def _optimize_temperature_nll(self, logits: torch.Tensor, labels: torch.Tensor) -> float:
        """Optimize temperature using NLL minimization"""
        # Create temperature parameter for optimization
        temp_param = nn.Parameter(torch.tensor(self.config.initial_temperature, device=self.device))

        # Setup optimizer
        optimizer = torch.optim.LBFGS([temp_param], lr=self.config.calibration_lr)

        # Define optimization objective
        def closure():
            optimizer.zero_grad()

            # Apply temperature scaling
            scaled_logits = logits / temp_param

            # Compute NLL
            nll = F.cross_entropy(scaled_logits, labels)

            # Add regularization
            reg = 0.01 * (temp_param - self.config.initial_temperature) ** 2

            loss = nll + reg
            loss.backward()

            return loss

        # Run optimization
        for epoch in range(self.config.calibration_epochs):
            optimizer.step(closure)

            if epoch % 10 == 0:
                with torch.no_grad():
                    scaled_logits = logits / temp_param
                    nll = F.cross_entropy(scaled_logits, labels)
                    self.logger.info(f"Epoch {epoch}, Temperature: {temp_param.item():.4f}, NLL: {nll:.4f}")

        # Update temperature parameter
        if self.temperature_params is not None:
            self.temperature_params.data.fill_(temp_param.item())

        optimal_temp = temp_param.item()
        self.logger.info(f"Optimal temperature found: {optimal_temp:.4f}")

        return optimal_temp

    def _compute_ece(self, probs: torch.Tensor, labels: torch.Tensor, n_bins: int = 10) -> float:
        """Compute Expected Calibration Error (ECE)"""
        # Convert to numpy for sklearn
        probs_np = probs.cpu().numpy()
        labels_np = labels.cpu().numpy()

        # Get confidence (max probability)
        confidence = np.max(probs_np, axis=1)

        # Get accuracy
        predictions = np.argmax(probs_np, axis=1)
        accuracy = (predictions == labels_np).astype(float)

        # Compute ECE
        ece = 0.0
        bin_boundaries = np.linspace(0, 1, n_bins + 1)

        for i in range(n_bins):
            # Get samples in this bin
            bin_mask = (confidence >= bin_boundaries[i]) & (confidence < bin_boundaries[i + 1])

            if np.sum(bin_mask) > 0:
                # Compute accuracy and confidence in this bin
                bin_accuracy = np.mean(accuracy[bin_mask])
                bin_confidence = np.mean(confidence[bin_mask])
                bin_count = np.sum(bin_mask) / len(confidence)

                # Add to ECE
                ece += bin_count * np.abs(bin_accuracy - bin_confidence)

        return ece

    def compute_temperature_schedule(self, step: int, total_steps: int) -> float:
        """Compute temperature based on schedule"""
        if self.config.temperature_schedule == "constant":
            return self.config.initial_temperature
        elif self.config.temperature_schedule == "linear":
            # Linear decay from initial to min temperature
            progress = step / total_steps
            return self.config.initial_temperature * (1 - progress) + self.config.min_temperature * progress
        elif self.config.temperature_schedule == "cosine":
            # Cosine annealing
            progress = step / total_steps
            return self.config.min_temperature + (self.config.initial_temperature - self.config.min_temperature) * 0.5 * (1 + np.cos(np.pi * progress))
        else:
            return self.config.initial_temperature

    def compute_distillation_temperature(self, step: int, total_steps: int, logits: Optional[torch.Tensor] = None) -> torch.Tensor:
        """Compute temperature for distillation based on configuration"""
        if self.config.method == TemperatureMethod.FIXED:
            temperature = self.compute_temperature_schedule(step, total_steps)
        elif self.config.method == TemperatureMethod.ADAPTIVE:
            temperature = self.get_temperature(logits)
        elif self.config.method == TemperatureMethod.TOKEN_WISE:
            temperature = self.get_temperature(logits)
        elif self.config.method == TemperatureMethod.LAYER_WISE:
            temperature = self.get_temperature(layer_idx=0)  # Use first layer as default
        else:
            temperature = self.temperature_params

        return temperature

    def save_temperature_config(self, save_path: str):
        """Save temperature configuration"""
        save_dict = {
            "method": self.config.method.value,
            "temperature_value": self.temperature_params.item() if self.temperature_params is not None else None,
            "config": self.config.__dict__
        }

        with open(save_path, "w") as f:
            json.dump(save_dict, f, indent=2)

        self.logger.info(f"Temperature configuration saved to {save_path}")

    def load_temperature_config(self, load_path: str):
        """Load temperature configuration"""
        with open(load_path, "r") as f:
            load_dict = json.load(f)

        if load_dict["temperature_value"] is not None and self.temperature_params is not None:
            self.temperature_params.data.fill_(load_dict["temperature_value"])

        self.logger.info(f"Temperature configuration loaded from {load_path}")

    def analyze_temperature_effects(self, logits: torch.Tensor, labels: torch.Tensor) -> Dict[str, float]:
        """Analyze the effects of temperature scaling"""
        results = {}

        # Original predictions
        original_probs = F.softmax(logits, dim=-1)
        original_predictions = torch.argmax(original_probs, dim=-1)
        original_accuracy = (original_predictions == labels).float().mean().item()

        # Compute entropy
        original_entropy = -torch.sum(original_probs * torch.log(original_probs + 1e-8), dim=-1).mean().item()

        # Test different temperatures
        test_temperatures = [0.1, 0.5, 1.0, 2.0, 5.0, 10.0]

        for temp in test_temperatures:
            scaled_logits = logits / temp
            scaled_probs = F.softmax(scaled_logits, dim=-1)
            scaled_predictions = torch.argmax(scaled_probs, dim=-1)
            scaled_accuracy = (scaled_predictions == labels).float().mean().item()

            # Compute entropy
            scaled_entropy = -torch.sum(scaled_probs * torch.log(scaled_probs + 1e-8), dim=-1).mean().item()

            # Compute KL divergence from original
            kl_div = F.kl_div(
                torch.log(scaled_probs + 1e-8),
                original_probs,
                reduction='batchmean'
            ).item()

            results[f"temp_{temp}"] = {
                "accuracy": scaled_accuracy,
                "entropy": scaled_entropy,
                "kl_divergence": kl_div
            }

        # Add original results
        results["original"] = {
            "accuracy": original_accuracy,
            "entropy": original_entropy,
            "kl_divergence": 0.0
        }

        return results

class SoftTargetGenerator:
    """Generate soft targets for knowledge distillation"""

    def __init__(self, temperature_scaler: TemperatureScaler):
        self.temperature_scaler = temperature_scaler
        self.logger = logging.getLogger('DuckBot.SoftTargetGenerator')

    def generate_soft_targets(
        self,
        teacher_logits: torch.Tensor,
        student_logits: Optional[torch.Tensor] = None,
        labels: Optional[torch.Tensor] = None,
        confidence_threshold: Optional[float] = None
    ) -> Dict[str, torch.Tensor]:
        """Generate various types of soft targets"""
        if confidence_threshold is None:
            confidence_threshold = self.temperature_scaler.config.confidence_threshold

        results = {}

        # Standard soft targets
        soft_targets = self.temperature_scaler.compute_soft_targets(teacher_logits)
        results["soft_targets"] = soft_targets

        # Soft labels (log probabilities)
        soft_labels = self.temperature_scaler.compute_soft_labels(teacher_logits)
        results["soft_labels"] = soft_labels

        # Confidence-based masking
        confidence = torch.max(soft_targets, dim=-1)[0]
        high_confidence_mask = confidence > confidence_threshold
        results["confidence_mask"] = high_confidence_mask

        # Masked soft targets
        masked_soft_targets = soft_targets * high_confidence_mask.unsqueeze(-1)
        results["masked_soft_targets"] = masked_soft_targets

        # Temperature-varying soft targets
        temperatures = [0.5, 1.0, 2.0, 5.0]
        for temp in temperatures:
            temp_scaled_logits = teacher_logits / temp
            temp_soft_targets = F.softmax(temp_scaled_logits, dim=-1)
            results[f"soft_targets_temp_{temp}"] = temp_soft_targets

        # Ensemble soft targets (if student logits provided)
        if student_logits is not None:
            student_soft_targets = self.temperature_scaler.compute_soft_targets(student_logits)
            ensemble_soft_targets = 0.5 * (soft_targets + student_soft_targets)
            results["ensemble_soft_targets"] = ensemble_soft_targets

        # Label smoothing soft targets (if labels provided)
        if labels is not None:
            label_smoothed_targets = self._compute_label_smoothed_targets(labels, teacher_logits.size(-1))
            results["label_smoothed_targets"] = label_smoothed_targets

        return results

    def _compute_label_smoothed_targets(self, labels: torch.Tensor, num_classes: int, smoothing: float = 0.1) -> torch.Tensor:
        """Compute label smoothed targets"""
        # Convert labels to one-hot
        one_hot = F.one_hot(labels, num_classes=num_classes).float()

        # Apply label smoothing
        smoothed_targets = one_hot * (1 - smoothing) + smoothing / num_classes

        return smoothed_targets

    def generate_multi_teacher_soft_targets(
        self,
        teacher_logits_list: List[torch.Tensor],
        teacher_weights: Optional[List[float]] = None
    ) -> torch.Tensor:
        """Generate soft targets from multiple teachers"""
        if teacher_weights is None:
            teacher_weights = [1.0 / len(teacher_logits_list)] * len(teacher_logits_list)

        # Normalize weights
        teacher_weights = torch.tensor(teacher_weights, device=self.temperature_scaler.device)
        teacher_weights = teacher_weights / teacher_weights.sum()

        # Generate soft targets for each teacher
        all_soft_targets = []
        for teacher_logits in teacher_logits_list:
            soft_targets = self.temperature_scaler.compute_soft_targets(teacher_logits)
            all_soft_targets.append(soft_targets)

        # Weighted ensemble
        ensemble_soft_targets = sum(w * st for w, st in zip(teacher_weights, all_soft_targets))

        return ensemble_soft_targets

def main():
    """Example usage of temperature scaling module"""
    # Example configuration
    config = TemperatureConfig(
        method=TemperatureMethod.ADAPTIVE,
        initial_temperature=2.0,
        min_temperature=0.1,
        max_temperature=10.0,
        use_soft_targets=True
    )

    # Create temperature scaler
    scaler = TemperatureScaler(config)

    # Example logits (batch_size=4, seq_len=10, vocab_size=1000)
    logits = torch.randn(4, 10, 1000)

    # Apply temperature scaling
    scaled_logits = scaler.apply_temperature_scaling(logits)

    # Compute soft targets
    soft_targets = scaler.compute_soft_targets(logits)

    print(f"Original logits shape: {logits.shape}")
    print(f"Scaled logits shape: {scaled_logits.shape}")
    print(f"Soft targets shape: {soft_targets.shape}")
    print(f"Temperature: {scaler.get_temperature(logits)}")

if __name__ == "__main__":
    main()