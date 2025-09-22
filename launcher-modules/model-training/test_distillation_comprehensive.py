#!/usr/bin/env python3
"""
Comprehensive Testing and Validation for Knowledge Distillation
Implements unit tests, integration tests, and performance benchmarks for all distillation components
"""

import unittest
import pytest
import torch
import torch.nn as nn
import numpy as np
import json
import tempfile
import shutil
from pathlib import Path
from typing import Dict, List, Any, Optional
import logging
import sys
import os

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Import distillation modules
from knowledge_distillation import KnowledgeDistiller, DistillationConfig, DistillationMethod
from temperature_scaling import TemperatureScaler, TemperatureConfig, TemperatureMethod
from distillation_loss_functions import (
    DistillationLossType, LossWeights, ComposedDistillationLoss,
    KLDivergenceLoss, AttentionTransferLoss, FeatureMatchingLoss,
    create_distillation_loss
)
from teacher_student_models import (
    TeacherStudentManager, TeacherStudentConfig, ModelType, ArchitectureStrategy
)
from model_compression import (
    ModelCompressor, CompressionConfig, CompressionType, PruningType,
    MagnitudePruner, ModelQuantizer, LowRankDecomposer
)
from distillation_evaluation import (
    DistillationEvaluator, EvaluationConfig, EvaluationMetric, TaskType,
    DistillationQualityMetrics, EfficiencyMetrics, CalibrationMetrics
)
from enhanced_distillation_trainer import EnhancedDistillationTrainer, EnhancedDistillationConfig


class TestModels:
    """Test models for unit testing"""

    @staticmethod
    def create_simple_teacher_model(vocab_size: int = 1000, hidden_size: int = 256, num_layers: int = 4):
        """Create a simple teacher model for testing"""
        class SimpleTeacherModel(nn.Module):
            def __init__(self, vocab_size, hidden_size, num_layers):
                super().__init__()
                self.embedding = nn.Embedding(vocab_size, hidden_size)
                self.layers = nn.ModuleList([
                    nn.TransformerEncoderLayer(d_model=hidden_size, nhead=8, dim_feedforward=hidden_size*4)
                    for _ in range(num_layers)
                ])
                self.output = nn.Linear(hidden_size, vocab_size)

            def forward(self, input_ids, attention_mask=None, output_attentions=False, output_hidden_states=False):
                # Embedding
                x = self.embedding(input_ids)

                # Transformer layers
                hidden_states = [x] if output_hidden_states else None
                attentions = []

                for layer in self.layers:
                    x, attention_weights = layer(x, return_attn_weights=True)
                    if output_hidden_states:
                        hidden_states.append(x)
                    if output_attentions:
                        attentions.append(attention_weights)

                # Output
                logits = self.output(x)

                outputs = {'logits': logits}
                if output_attentions:
                    outputs['attentions'] = attentions
                if output_hidden_states:
                    outputs['hidden_states'] = hidden_states

                return outputs

        return SimpleTeacherModel(vocab_size, hidden_size, num_layers)

    @staticmethod
    def create_simple_student_model(vocab_size: int = 1000, hidden_size: int = 128, num_layers: int = 2):
        """Create a simple student model for testing"""
        class SimpleStudentModel(nn.Module):
            def __init__(self, vocab_size, hidden_size, num_layers):
                super().__init__()
                self.embedding = nn.Embedding(vocab_size, hidden_size)
                self.layers = nn.ModuleList([
                    nn.TransformerEncoderLayer(d_model=hidden_size, nhead=4, dim_feedforward=hidden_size*4)
                    for _ in range(num_layers)
                ])
                self.output = nn.Linear(hidden_size, vocab_size)

            def forward(self, input_ids, attention_mask=None, output_attentions=False, output_hidden_states=False):
                # Embedding
                x = self.embedding(input_ids)

                # Transformer layers
                hidden_states = [x] if output_hidden_states else None
                attentions = []

                for layer in self.layers:
                    x, attention_weights = layer(x, return_attn_weights=True)
                    if output_hidden_states:
                        hidden_states.append(x)
                    if output_attentions:
                        attentions.append(attention_weights)

                # Output
                logits = self.output(x)

                outputs = {'logits': logits}
                if output_attentions:
                    outputs['attentions'] = attentions
                if output_hidden_states:
                    outputs['hidden_states'] = hidden_states

                return outputs

        return SimpleStudentModel(vocab_size, hidden_size, num_layers)


class TestKnowledgeDistillation(unittest.TestCase):
    """Test cases for knowledge distillation functionality"""

    def setUp(self):
        """Set up test fixtures"""
        self.teacher_model = TestModels.create_simple_teacher_model()
        self.student_model = TestModels.create_simple_student_model()
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

        # Move models to device
        self.teacher_model.to(self.device)
        self.student_model.to(self.device)

        # Create test data
        self.batch_size = 4
        self.seq_len = 32
        self.vocab_size = 1000
        self.input_ids = torch.randint(0, self.vocab_size, (self.batch_size, self.seq_len)).to(self.device)

    def test_knowledge_distiller_initialization(self):
        """Test KnowledgeDistiller initialization"""
        config = DistillationConfig(
            teacher_model_path="test_teacher",
            student_model_path="test_student",
            output_dir="./test_output",
            epochs=1,
            batch_size=2
        )

        distiller = KnowledgeDistiller(config)
        self.assertIsNotNone(distiller)
        self.assertEqual(distiller.config.temperature, 2.0)
        self.assertEqual(distiller.config.alpha, 0.5)

    def test_temperature_scaling(self):
        """Test temperature scaling functionality"""
        config = TemperatureConfig(method=TemperatureMethod.FIXED, initial_temperature=2.0)
        scaler = TemperatureScaler(config)

        # Test temperature application
        logits = torch.randn(self.batch_size, self.seq_len, self.vocab_size).to(self.device)
        scaled_logits = scaler.apply_temperature_scaling(logits)

        self.assertEqual(scaled_logits.shape, logits.shape)
        self.assertTrue(torch.allclose(scaled_logits, logits / 2.0))

        # Test soft targets
        soft_targets = scaler.compute_soft_targets(logits)
        self.assertEqual(soft_targets.shape, logits.shape[:-1] + (logits.shape[-1],))

    def test_distillation_loss_functions(self):
        """Test various distillation loss functions"""
        # Get model outputs
        teacher_outputs = self.teacher_model(self.input_ids, output_attentions=True, output_hidden_states=True)
        student_outputs = self.student_model(self.input_ids, output_attentions=True, output_hidden_states=True)

        # Test KL divergence loss
        kl_loss = KLDivergenceLoss(temperature=2.0, alpha=0.5)
        loss_value = kl_loss.compute_loss(teacher_outputs, student_outputs)
        self.assertIsInstance(loss_value, torch.Tensor)
        self.assertGreaterEqual(loss_value.item(), 0)

        # Test attention transfer loss
        attn_loss = AttentionTransferLoss(temperature=2.0, alpha=0.5)
        loss_value = attn_loss.compute_loss(teacher_outputs, student_outputs)
        self.assertIsInstance(loss_value, torch.Tensor)
        self.assertGreaterEqual(loss_value.item(), 0)

        # Test feature matching loss
        feature_loss = FeatureMatchingLoss(temperature=2.0, alpha=0.5)
        loss_value = feature_loss.compute_loss(teacher_outputs, student_outputs)
        self.assertIsInstance(loss_value, torch.Tensor)
        self.assertGreaterEqual(loss_value.item(), 0)

        # Test composed loss
        loss_weights = LossWeights(kl_weight=1.0, attention_weight=0.5, feature_weight=0.3)
        composed_loss = ComposedDistillationLoss(temperature=2.0, alpha=0.5, loss_weights=loss_weights)
        loss_value = composed_loss.compute_loss(teacher_outputs, student_outputs)
        self.assertIsInstance(loss_value, torch.Tensor)
        self.assertGreaterEqual(loss_value.item(), 0)

    def test_teacher_student_generation(self):
        """Test teacher-student model generation"""
        config = TeacherStudentConfig(
            teacher_model_path="test_teacher",
            model_type=ModelType.GPT2,
            architecture_strategy=ArchitectureStrategy.SCALING,
            scaling_factor=0.5
        )

        manager = TeacherStudentManager()
        teacher_model = TestModels.create_simple_teacher_model()
        student_model = manager.student_generator.create_student_model(teacher_model, config.scaling_factor, config)

        self.assertIsNotNone(student_model)
        # Student should be smaller than teacher
        teacher_params = sum(p.numel() for p in teacher_model.parameters())
        student_params = sum(p.numel() for p in student_model.parameters())
        self.assertLess(student_params, teacher_params)

    def test_model_compression(self):
        """Test model compression techniques"""
        # Test magnitude pruning
        pruner = MagnitudePruner(self.student_model, compression_ratio=0.3)
        stats = pruner.prune_model()

        self.assertIn("compression_ratio", stats)
        self.assertGreaterEqual(stats["compression_ratio"], 0)
        self.assertLessEqual(stats["compression_ratio"], 1)

        # Test quantization
        quantizer = ModelQuantizer(self.student_model)
        quantized_model = quantizer.quantize_model()

        self.assertIsNotNone(quantized_model)

        # Test low-rank decomposition
        decomposer = LowRankDecomposer(self.student_model, rank_ratio=0.5)
        stats = decomposer.decompose_model()

        self.assertIn("compression_ratio", stats)

    def test_distillation_evaluation(self):
        """Test distillation evaluation metrics"""
        # Create evaluation config
        config = EvaluationConfig(
            metrics=[EvaluationMetric.ACCURACY, EvaluationMetric.DISTILLATION_QUALITY],
            task_type=TaskType.CLASSIFICATION
        )

        evaluator = DistillationEvaluator(config)
        self.assertIsNotNone(evaluator)

        # Test quality metrics
        quality_metrics = DistillationQualityMetrics()
        teacher_outputs = self.teacher_model(self.input_ids, output_attentions=True, output_hidden_states=True)
        student_outputs = self.student_model(self.input_ids, output_attentions=True, output_hidden_states=True)

        quality_results = quality_metrics.compute_distillation_quality(teacher_outputs, student_outputs)

        self.assertIn("kl_divergence", quality_results)
        self.assertIn("cosine_similarity", quality_results)

        # Test efficiency metrics
        efficiency_metrics = EfficiencyMetrics()
        param_count = efficiency_metrics.count_parameters(self.student_model)

        self.assertIn("total_parameters", param_count)
        self.assertGreater(param_count["total_parameters"], 0)

    def test_enhanced_distillation_trainer(self):
        """Test enhanced distillation trainer"""
        config = EnhancedDistillationConfig(
            teacher_model_path="test_teacher",
            model_type=ModelType.GPT2,
            architecture_strategy=ArchitectureStrategy.SCALING,
            scaling_factor=0.5,
            epochs=1,
            batch_size=2,
            output_dir="./test_output"
        )

        trainer = EnhancedDistillationTrainer(config)
        self.assertIsNotNone(trainer)

        # Test model loading
        trainer.teacher_model = self.teacher_model
        trainer.student_model = self.student_model

        # Test data preparation (create dummy dataset)
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            dummy_data = [
                {"text": "This is a test sentence for training."},
                {"text": "Another test sentence for evaluation."},
                {"text": "Third test sentence for validation."}
            ]
            json.dump(dummy_data, f)
            dataset_path = f.name

        try:
            train_loader, val_loader = trainer.prepare_data(dataset_path)
            self.assertIsNotNone(train_loader)
            self.assertIsNotNone(val_loader)
        finally:
            os.unlink(dataset_path)


class TestDistillationIntegration(unittest.TestCase):
    """Integration tests for distillation components"""

    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        self.output_dir = Path(self.temp_dir) / "distillation_test"
        self.output_dir.mkdir()

    def tearDown(self):
        """Clean up test fixtures"""
        shutil.rmtree(self.temp_dir)

    def test_end_to_end_distillation(self):
        """Test end-to-end distillation pipeline"""
        # Create models
        teacher_model = TestModels.create_simple_teacher_model(vocab_size=500, hidden_size=128, num_layers=2)
        student_model = TestModels.create_simple_student_model(vocab_size=500, hidden_size=64, num_layers=1)

        # Create dummy dataset
        dataset_path = self.output_dir / "dummy_dataset.json"
        dummy_data = [
            {"text": f"This is test sentence {i} for knowledge distillation training."}
            for i in range(20)
        ]
        with open(dataset_path, 'w') as f:
            json.dump(dummy_data, f)

        # Create enhanced distillation config
        config = EnhancedDistillationConfig(
            teacher_model_path="dummy_teacher",
            model_type=ModelType.GPT2,
            architecture_strategy=ArchitectureStrategy.MANUAL,
            scaling_factor=0.5,
            distillation_method=DistillationMethod.STANDARD,
            loss_type=DistillationLossType.KL_DIVERGENCE,
            temperature=2.0,
            alpha=0.5,
            epochs=1,
            learning_rate=1e-4,
            batch_size=2,
            output_dir=str(self.output_dir),
            enable_compression=True,
            compression_type=CompressionType.PRUNING,
            compression_ratio=0.2
        )

        # Create trainer
        trainer = EnhancedDistillationTrainer(config)
        trainer.teacher_model = teacher_model
        trainer.student_model = student_model

        # Test training preparation
        try:
            train_loader, val_loader = trainer.prepare_data(str(dataset_path))
            self.assertIsNotNone(train_loader)

            # Test single training step
            optimizer = torch.optim.Adam(trainer.student_model.parameters(), lr=1e-4)
            trainer.student_model.train()
            trainer.teacher_model.eval()

            for batch in train_loader:
                if len(batch) > 0:
                    # Move batch to device
                    device = next(trainer.student_model.parameters()).device
                    batch = {k: v.to(device) for k, v in batch.items()}

                    # Forward pass
                    with torch.no_grad():
                        teacher_outputs = trainer.teacher_model(
                            input_ids=batch['input_ids'],
                            attention_mask=batch['attention_mask'],
                            output_attentions=True,
                            output_hidden_states=True
                        )

                    student_outputs = trainer.student_model(
                        input_ids=batch['input_ids'],
                        attention_mask=batch['attention_mask'],
                        output_attentions=True,
                        output_hidden_states=True
                    )

                    # Compute loss
                    loss = trainer.distillation_loss.compute_loss(
                        trainer._format_outputs(teacher_outputs),
                        trainer._format_outputs(student_outputs),
                        labels=batch.get('labels')
                    )

                    self.assertIsInstance(loss, torch.Tensor)
                    self.assertGreaterEqual(loss.item(), 0)
                    break

        except Exception as e:
            self.fail(f"End-to-end test failed: {e}")

    def test_temperature_scaling_integration(self):
        """Test temperature scaling integration with distillation"""
        config = TemperatureConfig(
            method=TemperatureMethod.ADAPTIVE,
            initial_temperature=2.0,
            min_temperature=0.1,
            max_temperature=10.0
        )

        scaler = TemperatureScaler(config)

        # Test with different input patterns
        batch_size, seq_len, vocab_size = 4, 16, 100
        logits_low_confidence = torch.randn(batch_size, seq_len, vocab_size) * 0.1
        logits_high_confidence = torch.randn(batch_size, seq_len, vocab_size) * 2.0

        temp_low = scaler.get_temperature(logits_low_confidence)
        temp_high = scaler.get_temperature(logits_high_confidence)

        self.assertIsInstance(temp_low, torch.Tensor)
        self.assertIsInstance(temp_high, torch.Tensor)

    def test_loss_function_composition(self):
        """Test composition of multiple loss functions"""
        loss_weights = LossWeights(
            kl_weight=1.0,
            attention_weight=0.5,
            feature_weight=0.3,
            relationship_weight=0.2
        )

        composed_loss = ComposedDistillationLoss(
            temperature=2.0,
            alpha=0.5,
            loss_weights=loss_weights
        )

        self.assertIsNotNone(composed_loss)
        self.assertEqual(composed_loss.alpha, 0.5)

    def test_model_compression_integration(self):
        """Test model compression integration with distillation"""
        model = TestModels.create_simple_student_model()

        compression_config = CompressionConfig(
            compression_type=CompressionType.PRUNING,
            target_ratio=0.3,
            pruning_type=PruningType.MAGNITUDE
        )

        compressor = ModelCompressor(model, compression_config)
        compressed_model, stats = compressor.compress_model()

        self.assertIsNotNone(compressed_model)
        self.assertIn("compression_ratio", stats)
        self.assertGreater(stats["compression_ratio"], 0)


class TestDistillationPerformance(unittest.TestCase):
    """Performance benchmarks for distillation components"""

    def setUp(self):
        """Set up performance test fixtures"""
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.teacher_model = TestModels.create_simple_teacher_model(vocab_size=1000, hidden_size=256, num_layers=4).to(self.device)
        self.student_model = TestModels.create_simple_student_model(vocab_size=1000, hidden_size=128, num_layers=2).to(self.device)

        # Create larger test data
        self.batch_size = 16
        self.seq_len = 64
        self.vocab_size = 1000
        self.input_ids = torch.randint(0, self.vocab_size, (self.batch_size, self.seq_len)).to(self.device)

    def test_distillation_loss_performance(self):
        """Test performance of distillation loss computation"""
        import time

        loss_types = [
            DistillationLossType.KL_DIVERGENCE,
            DistillationLossType.ATTENTION_TRANSFER,
            DistillationLossType.FEATURE_MATCHING
        ]

        performance_results = {}

        for loss_type in loss_types:
            loss_fn = create_distillation_loss(loss_type, temperature=2.0, alpha=0.5)

            # Warm up
            for _ in range(10):
                teacher_outputs = self.teacher_model(self.input_ids, output_attentions=True, output_hidden_states=True)
                student_outputs = self.student_model(self.input_ids, output_attentions=True, output_hidden_states=True)
                loss_fn.compute_loss(teacher_outputs, student_outputs)

            # Benchmark
            start_time = time.time()
            for _ in range(100):
                teacher_outputs = self.teacher_model(self.input_ids, output_attentions=True, output_hidden_states=True)
                student_outputs = self.student_model(self.input_ids, output_attentions=True, output_hidden_states=True)
                loss = loss_fn.compute_loss(teacher_outputs, student_outputs)
            end_time = time.time()

            avg_time = (end_time - start_time) / 100
            performance_results[loss_type.value] = avg_time

        # Log performance results
        for loss_type, avg_time in performance_results.items():
            print(f"{loss_type}: {avg_time:.4f}s per forward pass")

        # Verify all loss types complete within reasonable time
        for loss_type, avg_time in performance_results.items():
            self.assertLess(avg_time, 1.0, f"{loss_type} too slow: {avg_time:.4f}s")

    def test_temperature_scaling_performance(self):
        """Test performance of temperature scaling"""
        import time

        config = TemperatureConfig(method=TemperatureMethod.ADAPTIVE, initial_temperature=2.0)
        scaler = TemperatureScaler(config)

        # Warm up
        for _ in range(10):
            scaled_logits = scaler.apply_temperature_scaling(self.input_ids.float())

        # Benchmark
        start_time = time.time()
        for _ in range(1000):
            scaled_logits = scaler.apply_temperature_scaling(self.input_ids.float())
        end_time = time.time()

        avg_time = (end_time - start_time) / 1000
        print(f"Temperature scaling: {avg_time:.6f}s per operation")
        self.assertLess(avg_time, 0.001, "Temperature scaling too slow")

    def test_model_compression_performance(self):
        """Test performance of model compression"""
        import time

        # Test pruning performance
        pruner = MagnitudePruner(self.student_model, compression_ratio=0.3)

        start_time = time.time()
        stats = pruner.prune_model()
        end_time = time.time()

        pruning_time = end_time - start_time
        print(f"Model pruning: {pruning_time:.4f}s")
        self.assertLess(pruning_time, 5.0, "Model pruning too slow")

        # Test quantization performance
        quantizer = ModelQuantizer(self.student_model)

        start_time = time.time()
        quantized_model = quantizer.quantize_model()
        end_time = time.time()

        quantization_time = end_time - start_time
        print(f"Model quantization: {quantization_time:.4f}s")
        self.assertLess(quantization_time, 10.0, "Model quantization too slow")

    def test_memory_usage(self):
        """Test memory usage of distillation components"""
        if not torch.cuda.is_available():
            self.skipTest("CUDA not available for memory testing")

        import gc
        torch.cuda.empty_cache()
        gc.collect()

        initial_memory = torch.cuda.memory_allocated()

        # Load models and test memory usage
        teacher_outputs = self.teacher_model(self.input_ids, output_attentions=True, output_hidden_states=True)
        student_outputs = self.student_model(self.input_ids, output_attentions=True, output_hidden_states=True)

        # Compute distillation loss
        loss_fn = KLDivergenceLoss(temperature=2.0, alpha=0.5)
        loss = loss_fn.compute_loss(teacher_outputs, student_outputs)

        peak_memory = torch.cuda.memory_allocated()
        memory_increase = peak_memory - initial_memory

        print(f"Memory increase during distillation: {memory_increase / 1024**2:.2f} MB")

        # Memory should not increase excessively
        self.assertLess(memory_increase, 500 * 1024**2, "Memory usage too high")  # Less than 500MB increase


def create_test_suite():
    """Create comprehensive test suite"""
    suite = unittest.TestSuite()

    # Add unit tests
    suite.addTest(unittest.makeSuite(TestKnowledgeDistillation))

    # Add integration tests
    suite.addTest(unittest.makeSuite(TestDistillationIntegration))

    # Add performance tests
    suite.addTest(unittest.makeSuite(TestDistillationPerformance))

    return suite


def run_comprehensive_tests():
    """Run comprehensive test suite"""
    print("Running Comprehensive Knowledge Distillation Tests")
    print("=" * 60)

    # Configure logging
    logging.basicConfig(level=logging.INFO)

    # Create test suite
    suite = create_test_suite()

    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Print summary
    print("\n" + "=" * 60)
    print("Test Summary:")
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")

    if result.failures:
        print("\nFailures:")
        for test, traceback in result.failures:
            print(f"- {test}: {traceback}")

    if result.errors:
        print("\nErrors:")
        for test, traceback in result.errors:
            print(f"- {test}: {traceback}")

    success_rate = (result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100
    print(f"\nSuccess Rate: {success_rate:.1f}%")

    return result.wasSuccessful()


def benchmark_distillation_components():
    """Benchmark individual distillation components"""
    print("\nKnowledge Distillation Component Benchmarks")
    print("=" * 60)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Using device: {device}")

    # Create test models
    teacher_model = TestModels.create_simple_teacher_model(vocab_size=2000, hidden_size=512, num_layers=6).to(device)
    student_model = TestModels.create_simple_student_model(vocab_size=2000, hidden_size=256, num_layers=3).to(device)

    # Create test data
    batch_size = 32
    seq_len = 128
    input_ids = torch.randint(0, 2000, (batch_size, seq_len)).to(device)

    print(f"\nModel Parameters:")
    print(f"Teacher: {sum(p.numel() for p in teacher_model.parameters()):,}")
    print(f"Student: {sum(p.numel() for p in student_model.parameters()):,}")
    print(f"Compression ratio: {1 - (sum(p.numel() for p in student_model.parameters()) / sum(p.numel() for p in teacher_model.parameters())):.2%}")

    # Benchmark loss functions
    print(f"\nLoss Function Benchmarks:")
    loss_types = [
        DistillationLossType.KL_DIVERGENCE,
        DistillationLossType.ATTENTION_TRANSFER,
        DistillationLossType.FEATURE_MATCHING,
        DistillationLossType.RELATIONSHIP
    ]

    for loss_type in loss_types:
        loss_fn = create_distillation_loss(loss_type, temperature=2.0, alpha=0.5)

        # Warm up
        for _ in range(10):
            teacher_outputs = teacher_model(input_ids, output_attentions=True, output_hidden_states=True)
            student_outputs = student_model(input_ids, output_attentions=True, output_hidden_states=True)
            loss_fn.compute_loss(teacher_outputs, student_outputs)

        # Benchmark
        start_time = time.time()
        for _ in range(100):
            teacher_outputs = teacher_model(input_ids, output_attentions=True, output_hidden_states=True)
            student_outputs = student_model(input_ids, output_attentions=True, output_hidden_states=True)
            loss = loss_fn.compute_loss(teacher_outputs, student_outputs)
        end_time = time.time()

        avg_time = (end_time - start_time) / 100
        print(f"  {loss_type.value}: {avg_time:.4f}s per forward pass")

    # Benchmark temperature scaling
    print(f"\nTemperature Scaling Benchmarks:")
    temp_methods = [
        TemperatureMethod.FIXED,
        TemperatureMethod.ADAPTIVE,
        TemperatureMethod.TOKEN_WISE
    ]

    for method in temp_methods:
        config = TemperatureConfig(method=method, initial_temperature=2.0)
        scaler = TemperatureScaler(config)

        # Warm up
        for _ in range(100):
            temp = scaler.get_temperature(input_ids.float())

        # Benchmark
        start_time = time.time()
        for _ in range(1000):
            temp = scaler.get_temperature(input_ids.float())
        end_time = time.time()

        avg_time = (end_time - start_time) / 1000
        print(f"  {method.value}: {avg_time:.6f}s per computation")

    # Benchmark model compression
    print(f"\nModel Compression Benchmarks:")

    # Pruning benchmark
    pruner = MagnitudePruner(student_model, compression_ratio=0.3)
    start_time = time.time()
    stats = pruner.prune_model()
    end_time = time.time()
    print(f"  Magnitude Pruning: {end_time - start_time:.4f}s (compression: {stats['compression_ratio']:.1%})")

    # Quantization benchmark
    quantizer = ModelQuantizer(student_model)
    start_time = time.time()
    quantized_model = quantizer.quantize_model()
    end_time = time.time()
    print(f"  Quantization: {end_time - start_time:.4f}s")

    print(f"\nBenchmark completed successfully!")


def main():
    """Main test runner"""
    print("Knowledge Distillation Comprehensive Testing Suite")
    print("=" * 60)

    # Run unit and integration tests
    test_success = run_comprehensive_tests()

    # Run performance benchmarks
    try:
        benchmark_distillation_components()
    except Exception as e:
        print(f"\nBenchmark failed: {e}")

    print("\n" + "=" * 60)
    if test_success:
        print("✅ All tests passed! Knowledge distillation implementation is working correctly.")
    else:
        print("❌ Some tests failed. Please check the output above for details.")

    return test_success


if __name__ == "__main__":
    import time
    success = main()
    sys.exit(0 if success else 1)