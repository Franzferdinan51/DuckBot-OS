#!/usr/bin/env python3
"""
Comprehensive Evaluation Metrics for Distilled Models
Implements advanced evaluation methods for knowledge distillation quality and model performance
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
from typing import Dict, List, Optional, Any, Tuple, Union, Callable
from dataclasses import dataclass
from enum import Enum
import logging
import json
from pathlib import Path
from sklearn.metrics import accuracy_score, precision_recall_fscore_support, confusion_matrix
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
from scipy.stats import entropy, wasserstein_distance, ks_2samp
import matplotlib.pyplot as plt
import seaborn as sns
from collections import defaultdict
import time
import psutil
import GPUtil
from datetime import datetime
import traceback


class EvaluationMetric(Enum):
    """Types of evaluation metrics"""
    ACCURACY = "accuracy"
    PERPLEXITY = "perplexity"
    BLEU = "bleu"
    ROUGE = "rouge"
    DISTILLATION_QUALITY = "distillation_quality"
    KNOWLEDGE_RETENTION = "knowledge_retention"
    EFFICIENCY = "efficiency"
    CALIBRATION = "calibration"
    DIVERSITY = "diversity"
    ROBUSTNESS = "robustness"
    TRANSFERABILITY = "transferability"


class TaskType(Enum):
    """Types of tasks for evaluation"""
    CLASSIFICATION = "classification"
    GENERATION = "generation"
    REGRESSION = "regression"
    SEQUENCE_LABELING = "sequence_labeling"
    QUESTION_ANSWERING = "question_answering"
    SUMMARIZATION = "summarization"


@dataclass
class EvaluationConfig:
    """Configuration for model evaluation"""
    metrics: List[EvaluationMetric]
    task_type: TaskType
    batch_size: int = 32
    max_samples: Optional[int] = None
    compute_efficiency: bool = True
    compute_calibration: bool = True
    compute_diversity: bool = True
    compute_robustness: bool = True
    save_detailed_results: bool = True
    visualization: bool = True
    comparison_with_teacher: bool = True


class DistillationQualityMetrics:
    """Metrics specifically for evaluating distillation quality"""

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)

    def compute_kl_divergence(self, teacher_probs: torch.Tensor, student_probs: torch.Tensor) -> float:
        """Compute KL divergence between teacher and student distributions"""
        kl_div = F.kl_div(
            torch.log(student_probs + 1e-8),
            teacher_probs,
            reduction='batchmean'
        ).item()
        return kl_div

    def compute_js_divergence(self, teacher_probs: torch.Tensor, student_probs: torch.Tensor) -> float:
        """Compute Jensen-Shannon divergence"""
        avg_probs = 0.5 * (teacher_probs + student_probs)
        js_div = 0.5 * (
            F.kl_div(torch.log(teacher_probs + 1e-8), avg_probs, reduction='batchmean') +
            F.kl_div(torch.log(student_probs + 1e-8), avg_probs, reduction='batchmean')
        ).item()
        return js_div

    def compute_wasserstein_distance(self, teacher_probs: torch.Tensor, student_probs: torch.Tensor) -> float:
        """Compute Wasserstein distance between distributions"""
        teacher_np = teacher_probs.cpu().numpy()
        student_np = student_probs.cpu().numpy()

        distances = []
        for i in range(teacher_np.shape[0]):
            distance = wasserstein_distance(teacher_np[i], student_np[i])
            distances.append(distance)

        return np.mean(distances)

    def compute_cosine_similarity(self, teacher_logits: torch.Tensor, student_logits: torch.Tensor) -> float:
        """Compute cosine similarity between teacher and student logits"""
        similarities = F.cosine_similarity(teacher_logits, student_logits, dim=-1)
        return similarities.mean().item()

    def compute_attention_similarity(self, teacher_attention: List[torch.Tensor],
                                  student_attention: List[torch.Tensor]) -> Dict[str, float]:
        """Compute similarity between attention patterns"""
        if not teacher_attention or not student_attention:
            return {"attention_similarity": 0.0}

        similarities = []
        num_layers = min(len(teacher_attention), len(student_attention))

        for i in range(num_layers):
            teacher_att = teacher_attention[i]
            student_att = student_attention[i]

            # Normalize attention matrices
            teacher_norm = F.normalize(teacher_att, p=2, dim=-1)
            student_norm = F.normalize(student_att, p=2, dim=-1)

            # Compute similarity
            similarity = F.cosine_similarity(teacher_norm.flatten(), student_norm.flatten(), dim=0)
            similarities.append(similarity.item())

        return {
            "attention_similarity": np.mean(similarities),
            "attention_similarity_std": np.std(similarities),
            "layer_wise_similarities": similarities
        }

    def compute_feature_similarity(self, teacher_features: torch.Tensor, student_features: torch.Tensor) -> float:
        """Compute similarity between hidden features"""
        if teacher_features.shape != student_features.shape:
            # Resize if needed
            if teacher_features.size(-1) != student_features.size(-1):
                # Use simple projection
                teacher_features = F.adaptive_avg_pool1d(teacher_features, student_features.shape[-1])

        similarity = F.cosine_similarity(teacher_features.flatten(), student_features.flatten(), dim=0)
        return similarity.item()

    def compute_distillation_quality(self, teacher_outputs: Dict[str, torch.Tensor],
                                    student_outputs: Dict[str, torch.Tensor]) -> Dict[str, float]:
        """Compute comprehensive distillation quality metrics"""
        quality_metrics = {}

        # Logit-level metrics
        teacher_logits = teacher_outputs.get('logits')
        student_logits = student_outputs.get('logits')

        if teacher_logits is not None and student_logits is not None:
            teacher_probs = F.softmax(teacher_logits, dim=-1)
            student_probs = F.softmax(student_logits, dim=-1)

            quality_metrics.update({
                "kl_divergence": self.compute_kl_divergence(teacher_probs, student_probs),
                "js_divergence": self.compute_js_divergence(teacher_probs, student_probs),
                "wasserstein_distance": self.compute_wasserstein_distance(teacher_probs, student_probs),
                "cosine_similarity": self.compute_cosine_similarity(teacher_logits, student_logits)
            })

        # Attention-level metrics
        teacher_attention = teacher_outputs.get('attentions', [])
        student_attention = student_outputs.get('attentions', [])
        attention_metrics = self.compute_attention_similarity(teacher_attention, student_attention)
        quality_metrics.update(attention_metrics)

        # Feature-level metrics
        teacher_hidden = teacher_outputs.get('hidden_states', [])
        student_hidden = student_outputs.get('hidden_states', [])

        if teacher_hidden and student_hidden:
            # Use last hidden state
            teacher_features = teacher_hidden[-1]
            student_features = student_hidden[-1]
            quality_metrics["feature_similarity"] = self.compute_feature_similarity(teacher_features, student_features)

        return quality_metrics


class EfficiencyMetrics:
    """Metrics for evaluating model efficiency"""

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)

    def measure_inference_time(self, model: nn.Module, input_data: torch.Tensor,
                              num_runs: int = 100) -> Dict[str, float]:
        """Measure inference time and throughput"""
        model.eval()

        # Warm-up
        with torch.no_grad():
            for _ in range(10):
                _ = model(input_data[:1])

        # Measure inference time
        times = []
        with torch.no_grad():
            for _ in range(num_runs):
                start_time = time.time()
                _ = model(input_data[:1])
                end_time = time.time()
                times.append(end_time - start_time)

        return {
            "mean_inference_time_ms": np.mean(times) * 1000,
            "std_inference_time_ms": np.std(times) * 1000,
            "min_inference_time_ms": np.min(times) * 1000,
            "max_inference_time_ms": np.max(times) * 1000,
            "throughput_samples_per_sec": len(input_data) / np.mean(times)
        }

    def measure_memory_usage(self, model: nn.Module, input_data: torch.Tensor) -> Dict[str, float]:
        """Measure memory usage during inference"""
        torch.cuda.empty_cache() if torch.cuda.is_available() else None

        # Baseline memory
        baseline_mem = self._get_memory_usage()

        # Memory during inference
        model.eval()
        with torch.no_grad():
            _ = model(input_data[:1])
            inference_mem = self._get_memory_usage()

        return {
            "baseline_memory_mb": baseline_mem,
            "inference_memory_mb": inference_mem,
            "additional_memory_mb": inference_mem - baseline_mem,
            "peak_memory_mb": max(baseline_mem, inference_mem)
        }

    def _get_memory_usage(self) -> float:
        """Get current memory usage in MB"""
        try:
            if torch.cuda.is_available():
                return torch.cuda.memory_allocated() / 1024 / 1024
            else:
                process = psutil.Process()
                return process.memory_info().rss / 1024 / 1024
        except:
            return 0.0

    def count_parameters(self, model: nn.Module) -> Dict[str, int]:
        """Count model parameters"""
        total_params = sum(p.numel() for p in model.parameters())
        trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)

        return {
            "total_parameters": total_params,
            "trainable_parameters": trainable_params,
            "non_trainable_parameters": total_params - trainable_params
        }

    def estimate_flops(self, model: nn.Module, input_shape: Tuple[int, ...]) -> Dict[str, int]:
        """Estimate FLOPs for model inference"""
        # This is a simplified estimation
        # For accurate FLOPs counting, you might want to use libraries like `fvcore`

        total_flops = 0
        layer_flops = {}

        def hook_fn(module, input, output, name):
            flops = 0

            if isinstance(module, nn.Linear):
                input_dims = input[0].numel()
                output_dims = output.numel()
                flops = input_dims * module.weight.size(1)  # MAC operations

            elif isinstance(module, nn.Conv2d):
                input_dims = np.prod(input[0].shape[1:])
                kernel_dims = np.prod(module.kernel_size)
                output_dims = np.prod(output.shape[1:])
                flops = kernel_dims * input_dims * output_dims

            elif isinstance(module, nn.MultiheadAttention):
                # Simplified attention FLOPs estimation
                seq_len = input[0].size(1)
                embed_dim = module.embed_dim
                flops = 4 * seq_len * seq_len * embed_dim  # Q, K, V projections + attention

            layer_flops[name] = flops
            nonlocal total_flops
            total_flops += flops

        # Register hooks
        hooks = []
        for name, module in model.named_modules():
            if len(list(module.children())) == 0:  # Leaf modules
                hook = module.register_forward_hook(lambda m, i, o, n=name: hook_fn(m, i, o, n))
                hooks.append(hook)

        # Forward pass
        model.eval()
        dummy_input = torch.randn(input_shape)
        with torch.no_grad():
            _ = model(dummy_input)

        # Remove hooks
        for hook in hooks:
            hook.remove()

        return {
            "total_flops": total_flops,
            "layer_flops": layer_flops
        }

    def compute_efficiency_metrics(self, teacher_model: nn.Module, student_model: nn.Module,
                                   input_data: torch.Tensor) -> Dict[str, Any]:
        """Compute comprehensive efficiency metrics"""
        efficiency_metrics = {}

        # Parameter count
        teacher_params = self.count_parameters(teacher_model)
        student_params = self.count_parameters(student_model)

        efficiency_metrics.update({
            "teacher_parameters": teacher_params,
            "student_parameters": student_params,
            "parameter_compression_ratio": 1 - (student_params["total_parameters"] / teacher_params["total_parameters"])
        })

        # Inference time
        teacher_time = self.measure_inference_time(teacher_model, input_data)
        student_time = self.measure_inference_time(student_model, input_data)

        efficiency_metrics.update({
            "teacher_inference_time": teacher_time,
            "student_inference_time": student_time,
            "speedup_ratio": teacher_time["mean_inference_time_ms"] / student_time["mean_inference_time_ms"]
        })

        # Memory usage
        teacher_memory = self.measure_memory_usage(teacher_model, input_data)
        student_memory = self.measure_memory_usage(student_model, input_data)

        efficiency_metrics.update({
            "teacher_memory_usage": teacher_memory,
            "student_memory_usage": student_memory,
            "memory_compression_ratio": 1 - (student_memory["inference_memory_mb"] / teacher_memory["inference_memory_mb"])
        })

        # FLOPs estimation
        input_shape = tuple(input_data.shape)
        teacher_flops = self.estimate_flops(teacher_model, input_shape)
        student_flops = self.estimate_flops(student_model, input_shape)

        efficiency_metrics.update({
            "teacher_flops": teacher_flops,
            "student_flops": student_flops,
            "flops_compression_ratio": 1 - (student_flops["total_flops"] / teacher_flops["total_flops"])
        })

        return efficiency_metrics


class CalibrationMetrics:
    """Metrics for evaluating model calibration"""

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)

    def compute_expected_calibration_error(self, confidences: np.ndarray, accuracies: np.ndarray,
                                         n_bins: int = 10) -> Dict[str, float]:
        """Compute Expected Calibration Error (ECE)"""
        bin_boundaries = np.linspace(0, 1, n_bins + 1)
        bin_lowers = bin_boundaries[:-1]
        bin_uppers = bin_boundaries[1:]

        ece = 0.0
        bin_accuracies = []
        bin_confidences = []
        bin_counts = []

        for bin_lower, bin_upper in zip(bin_lowers, bin_uppers):
            # Find samples in this bin
            in_bin = (confidences > bin_lower) & (confidences <= bin_upper)
            bin_count = np.sum(in_bin)

            if bin_count > 0:
                bin_accuracy = np.mean(accuracies[in_bin])
                bin_confidence = np.mean(confidences[in_bin])
                bin_weight = bin_count / len(confidences)

                ece += bin_weight * np.abs(bin_accuracy - bin_confidence)

                bin_accuracies.append(bin_accuracy)
                bin_confidences.append(bin_confidence)
                bin_counts.append(bin_count)

        return {
            "ece": ece,
            "bin_accuracies": bin_accuracies,
            "bin_confidences": bin_confidences,
            "bin_counts": bin_counts
        }

    def compute_reliability_diagram(self, confidences: np.ndarray, accuracies: np.ndarray,
                                   n_bins: int = 10) -> Dict[str, np.ndarray]:
        """Compute reliability diagram for calibration analysis"""
        bin_boundaries = np.linspace(0, 1, n_bins + 1)

        bin_accs = []
        bin_confs = []
        bin_counts = []

        for i in range(n_bins):
            bin_lower = bin_boundaries[i]
            bin_upper = bin_boundaries[i + 1]

            in_bin = (confidences > bin_lower) & (confidences <= bin_upper)
            bin_count = np.sum(in_bin)

            if bin_count > 0:
                bin_acc = np.mean(accuracies[in_bin])
                bin_conf = np.mean(confidences[in_bin])
            else:
                bin_acc = 0.0
                bin_conf = 0.0

            bin_accs.append(bin_acc)
            bin_confs.append(bin_conf)
            bin_counts.append(bin_count)

        return {
            "bin_accuracies": np.array(bin_accs),
            "bin_confidences": np.array(bin_confs),
            "bin_counts": np.array(bin_counts),
            "bin_boundaries": bin_boundaries
        }

    def compute_brier_score(self, probs: np.ndarray, labels: np.ndarray) -> float:
        """Compute Brier score"""
        one_hot_labels = np.zeros_like(probs)
        one_hot_labels[np.arange(len(labels)), labels] = 1

        brier_score = np.mean((probs - one_hot_labels) ** 2)
        return brier_score

    def compute_negative_log_likelihood(self, probs: np.ndarray, labels: np.ndarray) -> float:
        """Compute negative log likelihood"""
        selected_probs = probs[np.arange(len(labels)), labels]
        nll = -np.mean(np.log(selected_probs + 1e-8))
        return nll

    def compute_calibration_metrics(self, model: nn.Module, data_loader,
                                   device: torch.device) -> Dict[str, float]:
        """Compute comprehensive calibration metrics"""
        model.eval()
        all_probs = []
        all_labels = []
        all_confidences = []

        with torch.no_grad():
            for batch in data_loader:
                inputs, labels = batch
                inputs, labels = inputs.to(device), labels.to(device)

                outputs = model(inputs)
                probs = F.softmax(outputs, dim=-1)

                # Get predictions and confidences
                predictions = torch.argmax(probs, dim=-1)
                confidences = torch.max(probs, dim=-1)[0]

                all_probs.append(probs.cpu().numpy())
                all_labels.append(labels.cpu().numpy())
                all_confidences.append(confidences.cpu().numpy())

        # Concatenate all results
        all_probs = np.concatenate(all_probs)
        all_labels = np.concatenate(all_labels)
        all_confidences = np.concatenate(all_confidences)

        # Compute accuracy
        predictions = np.argmax(all_probs, axis=-1)
        accuracies = (predictions == all_labels).astype(float)

        # Compute calibration metrics
        ece_metrics = self.compute_expected_calibration_error(all_confidences, accuracies)
        brier_score = self.compute_brier_score(all_probs, all_labels)
        nll = self.compute_negative_log_likelihood(all_probs, all_labels)

        return {
            "ece": ece_metrics["ece"],
            "brier_score": brier_score,
            "negative_log_likelihood": nll,
            "mean_confidence": np.mean(all_confidences),
            "mean_accuracy": np.mean(accuracies),
            "confidence_std": np.std(all_confidences)
        }


class RobustnessMetrics:
    """Metrics for evaluating model robustness"""

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)

    def compute_adversarial_robustness(self, model: nn.Module, data_loader,
                                      attack_fn: Callable, device: torch.device) -> Dict[str, float]:
        """Compute adversarial robustness metrics"""
        model.eval()
        clean_accuracy = 0.0
        adversarial_accuracy = 0.0
        total_samples = 0

        for batch in data_loader:
            inputs, labels = batch
            inputs, labels = inputs.to(device), labels.to(device)

            # Clean accuracy
            with torch.no_grad():
                outputs = model(inputs)
                predictions = torch.argmax(outputs, dim=-1)
                clean_accuracy += (predictions == labels).sum().item()

            # Adversarial accuracy
            adversarial_inputs = attack_fn(model, inputs, labels)
            with torch.no_grad():
                adv_outputs = model(adversarial_inputs)
                adv_predictions = torch.argmax(adv_outputs, dim=-1)
                adversarial_accuracy += (adv_predictions == labels).sum().item()

            total_samples += inputs.size(0)

        clean_accuracy /= total_samples
        adversarial_accuracy /= total_samples
        robustness_drop = clean_accuracy - adversarial_accuracy

        return {
            "clean_accuracy": clean_accuracy,
            "adversarial_accuracy": adversarial_accuracy,
            "robustness_drop": robustness_drop,
            "robustness_ratio": adversarial_accuracy / clean_accuracy if clean_accuracy > 0 else 0
        }

    def compute_noise_robustness(self, model: nn.Module, data_loader,
                                 noise_levels: List[float], device: torch.device) -> Dict[str, float]:
        """Compute robustness to input noise"""
        model.eval()
        results = {}

        for noise_level in noise_levels:
            noisy_accuracy = 0.0
            total_samples = 0

            for batch in data_loader:
                inputs, labels = batch
                inputs, labels = inputs.to(device), labels.to(device)

                # Add noise
                noise = torch.randn_like(inputs) * noise_level
                noisy_inputs = inputs + noise

                with torch.no_grad():
                    outputs = model(noisy_inputs)
                    predictions = torch.argmax(outputs, dim=-1)
                    noisy_accuracy += (predictions == labels).sum().item()

                total_samples += inputs.size(0)

            noisy_accuracy /= total_samples
            results[f"noise_{noise_level}"] = noisy_accuracy

        return results

    def compute_distribution_shift_robustness(self, model: nn.Module,
                                           clean_loader: torch.utils.data.DataLoader,
                                           shifted_loader: torch.utils.data.DataLoader,
                                           device: torch.device) -> Dict[str, float]:
        """Compute robustness to distribution shift"""
        model.eval()

        # Clean accuracy
        clean_accuracy = self._compute_accuracy(model, clean_loader, device)

        # Shifted accuracy
        shifted_accuracy = self._compute_accuracy(model, shifted_loader, device)

        shift_drop = clean_accuracy - shifted_accuracy

        return {
            "clean_accuracy": clean_accuracy,
            "shifted_accuracy": shifted_accuracy,
            "shift_drop": shift_drop,
            "shift_robustness": shifted_accuracy / clean_accuracy if clean_accuracy > 0 else 0
        }

    def _compute_accuracy(self, model: nn.Module, data_loader: torch.utils.data.DataLoader,
                         device: torch.device) -> float:
        """Compute accuracy on a dataset"""
        correct = 0
        total = 0

        with torch.no_grad():
            for batch in data_loader:
                inputs, labels = batch
                inputs, labels = inputs.to(device), labels.to(device)

                outputs = model(inputs)
                predictions = torch.argmax(outputs, dim=-1)
                correct += (predictions == labels).sum().item()
                total += inputs.size(0)

        return correct / total


class DistillationEvaluator:
    """Main evaluator for distilled models"""

    def __init__(self, config: EvaluationConfig):
        self.config = config
        self.logger = logging.getLogger(self.__class__.__name__)

        # Initialize metric computers
        self.quality_metrics = DistillationQualityMetrics()
        self.efficiency_metrics = EfficiencyMetrics()
        self.calibration_metrics = CalibrationMetrics()
        self.robustness_metrics = RobustnessMetrics()

        # Results storage
        self.results = {}

    def evaluate_distilled_model(self, teacher_model: nn.Module, student_model: nn.Module,
                                data_loader: torch.utils.data.DataLoader,
                                device: torch.device) -> Dict[str, Any]:
        """Comprehensive evaluation of distilled model"""
        self.logger.info("Starting comprehensive evaluation of distilled model...")

        evaluation_results = {
            "evaluation_timestamp": datetime.now().isoformat(),
            "model_comparison": {}
        }

        # Evaluate basic performance
        if EvaluationMetric.ACCURACY in self.config.metrics:
            evaluation_results["accuracy"] = self._evaluate_accuracy(student_model, data_loader, device)

        # Evaluate distillation quality
        if EvaluationMetric.DISTILLATION_QUALITY in self.config.metrics:
            evaluation_results["distillation_quality"] = self._evaluate_distillation_quality(
                teacher_model, student_model, data_loader, device
            )

        # Evaluate efficiency
        if EvaluationMetric.EFFICIENCY in self.config.metrics and self.config.compute_efficiency:
            evaluation_results["efficiency"] = self._evaluate_efficiency(
                teacher_model, student_model, data_loader, device
            )

        # Evaluate calibration
        if EvaluationMetric.CALIBRATION in self.config.metrics and self.config.compute_calibration:
            evaluation_results["calibration"] = self._evaluate_calibration(
                teacher_model, student_model, data_loader, device
            )

        # Evaluate robustness
        if EvaluationMetric.ROBUSTNESS in self.config.metrics and self.config.compute_robustness:
            evaluation_results["robustness"] = self._evaluate_robustness(
                teacher_model, student_model, data_loader, device
            )

        # Compute overall score
        evaluation_results["overall_score"] = self._compute_overall_score(evaluation_results)

        self.logger.info("Evaluation completed successfully")
        return evaluation_results

    def _evaluate_accuracy(self, model: nn.Module, data_loader: torch.utils.data.DataLoader,
                          device: torch.device) -> Dict[str, float]:
        """Evaluate model accuracy"""
        self.logger.info("Evaluating model accuracy...")

        model.eval()
        all_predictions = []
        all_labels = []
        total_loss = 0.0
        num_samples = 0

        loss_fn = nn.CrossEntropyLoss()

        with torch.no_grad():
            for batch_idx, batch in enumerate(data_loader):
                if self.config.max_samples and num_samples >= self.config.max_samples:
                    break

                inputs, labels = batch
                inputs, labels = inputs.to(device), labels.to(device)

                outputs = model(inputs)
                loss = loss_fn(outputs, labels)
                total_loss += loss.item() * inputs.size(0)

                predictions = torch.argmax(outputs, dim=-1)
                all_predictions.extend(predictions.cpu().numpy())
                all_labels.extend(labels.cpu().numpy())

                num_samples += inputs.size(0)

        # Compute metrics
        accuracy = accuracy_score(all_labels, all_predictions)
        precision, recall, f1, _ = precision_recall_fscore_support(
            all_labels, all_predictions, average='weighted'
        )

        avg_loss = total_loss / num_samples

        return {
            "accuracy": accuracy,
            "precision": precision,
            "recall": recall,
            "f1_score": f1,
            "average_loss": avg_loss,
            "num_samples": num_samples
        }

    def _evaluate_distillation_quality(self, teacher_model: nn.Module, student_model: nn.Module,
                                     data_loader: torch.utils.data.DataLoader,
                                     device: torch.device) -> Dict[str, Any]:
        """Evaluate distillation quality metrics"""
        self.logger.info("Evaluating distillation quality...")

        teacher_model.eval()
        student_model.eval()

        all_quality_metrics = []

        with torch.no_grad():
            for batch_idx, batch in enumerate(data_loader):
                if self.config.max_samples and batch_idx * self.config.batch_size >= self.config.max_samples:
                    break

                inputs, _ = batch
                inputs = inputs.to(device)

                # Get teacher outputs
                teacher_outputs = teacher_model(inputs, output_attentions=True, output_hidden_states=True)

                # Get student outputs
                student_outputs = student_model(inputs, output_attentions=True, output_hidden_states=True)

                # Compute quality metrics
                quality_metrics = self.quality_metrics.compute_distillation_quality(
                    teacher_outputs, student_outputs
                )
                all_quality_metrics.append(quality_metrics)

        # Aggregate metrics
        aggregated_metrics = {}
        for key in all_quality_metrics[0].keys():
            if key != "layer_wise_similarities":  # Skip complex nested structures
                values = [metrics[key] for metrics in all_quality_metrics]
                aggregated_metrics[key] = {
                    "mean": np.mean(values),
                    "std": np.std(values),
                    "min": np.min(values),
                    "max": np.max(values)
                }

        return aggregated_metrics

    def _evaluate_efficiency(self, teacher_model: nn.Module, student_model: nn.Module,
                           data_loader: torch.utils.data.DataLoader,
                           device: torch.device) -> Dict[str, Any]:
        """Evaluate model efficiency"""
        self.logger.info("Evaluating model efficiency...")

        # Get sample input for efficiency measurements
        sample_batch = next(iter(data_loader))
        sample_inputs = sample_batch[0][:1].to(device)

        efficiency_metrics = self.efficiency_metrics.compute_efficiency_metrics(
            teacher_model, student_model, sample_inputs
        )

        return efficiency_metrics

    def _evaluate_calibration(self, teacher_model: nn.Module, student_model: nn.Module,
                            data_loader: torch.utils.data.DataLoader,
                            device: torch.device) -> Dict[str, Any]:
        """Evaluate model calibration"""
        self.logger.info("Evaluating model calibration...")

        teacher_calibration = self.calibration_metrics.compute_calibration_metrics(
            teacher_model, data_loader, device
        )

        student_calibration = self.calibration_metrics.compute_calibration_metrics(
            student_model, data_loader, device
        )

        return {
            "teacher_calibration": teacher_calibration,
            "student_calibration": student_calibration,
            "calibration_improvement": teacher_calibration["ece"] - student_calibration["ece"]
        }

    def _evaluate_robustness(self, teacher_model: nn.Module, student_model: nn.Module,
                           data_loader: torch.utils.data.DataLoader,
                           device: torch.device) -> Dict[str, Any]:
        """Evaluate model robustness"""
        self.logger.info("Evaluating model robustness...")

        # Noise robustness
        noise_levels = [0.01, 0.05, 0.1]
        teacher_noise_robustness = self.robustness_metrics.compute_noise_robustness(
            teacher_model, data_loader, noise_levels, device
        )
        student_noise_robustness = self.robustness_metrics.compute_noise_robustness(
            student_model, data_loader, noise_levels, device
        )

        return {
            "teacher_noise_robustness": teacher_noise_robustness,
            "student_noise_robustness": student_noise_robustness,
            "robustness_comparison": {
                level: student_noise_robustness[f"noise_{level}"] / teacher_noise_robustness[f"noise_{level}"]
                for level in noise_levels
            }
        }

    def _compute_overall_score(self, evaluation_results: Dict[str, Any]) -> float:
        """Compute overall evaluation score"""
        score_components = []

        # Performance score (40%)
        if "accuracy" in evaluation_results:
            acc_score = evaluation_results["accuracy"]["accuracy"]
            score_components.append(("accuracy", acc_score * 0.4))

        # Distillation quality score (30%)
        if "distillation_quality" in evaluation_results:
            quality = evaluation_results["distillation_quality"]
            # Use cosine similarity and inverse KL divergence
            cos_sim = quality.get("cosine_similarity", {}).get("mean", 0)
            kl_div = quality.get("kl_divergence", {}).get("mean", float('inf'))
            kl_score = max(0, 1 - min(kl_div, 10) / 10)  # Normalize KL divergence
            quality_score = (cos_sim + kl_score) / 2 * 0.3
            score_components.append(("distillation_quality", quality_score))

        # Efficiency score (20%)
        if "efficiency" in evaluation_results:
            efficiency = evaluation_results["efficiency"]
            speedup = efficiency.get("speedup_ratio", 1)
            param_compression = efficiency.get("parameter_compression_ratio", 0)
            efficiency_score = min(speedup / 2, 1) * 0.1 + param_compression * 0.1
            score_components.append(("efficiency", efficiency_score))

        # Calibration score (10%)
        if "calibration" in evaluation_results:
            calibration = evaluation_results["calibration"]
            ece_improvement = calibration.get("calibration_improvement", 0)
            cal_score = max(0, min(ece_improvement, 0.1) * 100) * 0.1
            score_components.append(("calibration", cal_score))

        # Compute weighted overall score
        overall_score = sum(score for _, score in score_components)

        return {
            "overall_score": overall_score,
            "score_components": score_components
        }

    def save_results(self, results: Dict[str, Any], save_path: str):
        """Save evaluation results"""
        save_path = Path(save_path)
        save_path.mkdir(parents=True, exist_ok=True)

        # Save detailed results
        with open(save_path / "evaluation_results.json", "w") as f:
            json.dump(results, f, indent=2, default=str)

        # Save summary
        summary = {
            "overall_score": results.get("overall_score", 0),
            "accuracy": results.get("accuracy", {}).get("accuracy", 0),
            "parameter_compression": results.get("efficiency", {}).get("parameter_compression_ratio", 0),
            "speedup_ratio": results.get("efficiency", {}).get("speedup_ratio", 1),
            "distillation_quality": results.get("distillation_quality", {}).get("cosine_similarity", {}).get("mean", 0)
        }

        with open(save_path / "evaluation_summary.json", "w") as f:
            json.dump(summary, f, indent=2)

        self.logger.info(f"Evaluation results saved to {save_path}")

    def generate_report(self, results: Dict[str, Any]) -> str:
        """Generate human-readable evaluation report"""
        report = f"""
Distilled Model Evaluation Report
=================================

Overall Score: {results.get('overall_score', {}).get('overall_score', 0):.3f}

Performance Metrics:
- Accuracy: {results.get('accuracy', {}).get('accuracy', 0):.3f}
- F1 Score: {results.get('accuracy', {}).get('f1_score', 0):.3f}

Distillation Quality:
- KL Divergence: {results.get('distillation_quality', {}).get('kl_divergence', {}).get('mean', 0):.4f}
- Cosine Similarity: {results.get('distillation_quality', {}).get('cosine_similarity', {}).get('mean', 0):.3f}
- Attention Similarity: {results.get('distillation_quality', {}).get('attention_similarity', 0):.3f}

Efficiency Metrics:
- Parameter Compression: {results.get('efficiency', {}).get('parameter_compression_ratio', 0):.1%}
- Speedup Ratio: {results.get('efficiency', {}).get('speedup_ratio', 1):.2f}x
- Memory Compression: {results.get('efficiency', {}).get('memory_compression_ratio', 0):.1%}

Calibration:
- ECE: {results.get('calibration', {}).get('student_calibration', {}).get('ece', 0):.4f}
- Brier Score: {results.get('calibration', {}).get('student_calibration', {}).get('brier_score', 0):.4f}

Evaluation Timestamp: {results.get('evaluation_timestamp', 'Unknown')}
"""
        return report


def main():
    """Example usage of distillation evaluation"""
    # Example configuration
    config = EvaluationConfig(
        metrics=[
            EvaluationMetric.ACCURACY,
            EvaluationMetric.DISTILLATION_QUALITY,
            EvaluationMetric.EFFICIENCY,
            EvaluationMetric.CALIBRATION
        ],
        task_type=TaskType.CLASSIFICATION,
        batch_size=32,
        compute_efficiency=True,
        compute_calibration=True
    )

    # Create evaluator
    evaluator = DistillationEvaluator(config)

    print("Distillation evaluation module initialized successfully")
    print(f"Configuration: {config}")


if __name__ == "__main__":
    main()