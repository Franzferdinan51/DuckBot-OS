#!/usr/bin/env python3
"""
Test suite for the Hugging Face model downloader
"""

import os
import sys
import json
import tempfile
import shutil
import unittest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import logging

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from huggingface_downloader import (
    ModelDownloader,
    ModelDownloadConfig,
    DownloadStatus,
    ModelFormat,
    HuggingFaceAuth,
    ModelCacheManager,
    GGUFConverter,
    ConfigManager
)

class TestModelDownloadConfig(unittest.TestCase):
    """Test ModelDownloadConfig dataclass"""

    def test_default_config(self):
        """Test default configuration values"""
        config = ModelDownloadConfig(model_id="test/model")

        self.assertEqual(config.model_id, "test/model")
        self.assertIsNone(config.revision)
        self.assertIsNone(config.token)
        self.assertFalse(config.local_files_only)
        self.assertTrue(config.resume_download)
        self.assertFalse(config.force_download)
        self.assertFalse(config.convert_to_gguf)

    def test_config_with_values(self):
        """Test configuration with custom values"""
        config = ModelDownloadConfig(
            model_id="test/model",
            revision="main",
            token="test_token",
            convert_to_gguf=True,
            gguf_quantization="q4_0",
            max_workers=8
        )

        self.assertEqual(config.model_id, "test/model")
        self.assertEqual(config.revision, "main")
        self.assertEqual(config.token, "test_token")
        self.assertTrue(config.convert_to_gguf)
        self.assertEqual(config.gguf_quantization, "q4_0")
        self.assertEqual(config.max_workers, 8)

class TestHuggingFaceAuth(unittest.TestCase):
    """Test Hugging Face authentication"""

    def setUp(self):
        """Set up test fixtures"""
        self.auth = HuggingFaceAuth()

    def test_init_without_token(self):
        """Test initialization without token"""
        auth = HuggingFaceAuth()
        self.assertIsNone(auth.token)
        self.assertIsNotNone(auth.api)

    def test_init_with_token(self):
        """Test initialization with token"""
        auth = HuggingFaceAuth("test_token")
        self.assertEqual(auth.token, "test_token")

    @patch('huggingface_downloader.whoami')
    def test_get_user_info_with_token(self, mock_whoami):
        """Test getting user info with valid token"""
        mock_whoami.return_value = {"name": "test_user", "email": "test@example.com"}

        auth = HuggingFaceAuth("test_token")
        user_info = auth.get_user_info()

        self.assertEqual(user_info["name"], "test_user")
        self.assertEqual(user_info["email"], "test@example.com")

    def test_get_user_info_without_token(self):
        """Test getting user info without token"""
        auth = HuggingFaceAuth()
        user_info = auth.get_user_info()

        self.assertIsNone(user_info)

    @patch('huggingface_downloader.model_info')
    def test_has_access_to_model_public(self, mock_model_info):
        """Test access check for public model"""
        mock_info = Mock()
        mock_info.gated = False
        mock_model_info.return_value = mock_info

        auth = HuggingFaceAuth()
        has_access = auth.has_access_to_model("public/model")

        self.assertTrue(has_access)

    @patch('huggingface_downloader.model_info')
    def test_has_access_to_model_private_no_token(self, mock_model_info):
        """Test access check for private model without token"""
        mock_info = Mock()
        mock_info.gated = True
        mock_model_info.return_value = mock_info

        auth = HuggingFaceAuth()
        has_access = auth.has_access_to_model("private/model")

        self.assertFalse(has_access)

class TestModelCacheManager(unittest.TestCase):
    """Test model cache management"""

    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        self.cache_manager = ModelCacheManager(self.temp_dir)

    def tearDown(self):
        """Clean up test fixtures"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_initialization(self):
        """Test cache manager initialization"""
        self.assertTrue(self.cache_manager.cache_dir.exists())
        self.assertTrue(self.cache_manager.metadata_file.exists())
        self.assertIsInstance(self.cache_manager.metadata, dict)

    def test_add_to_cache(self):
        """Test adding model to cache"""
        # Create a fake model directory
        model_dir = Path(self.temp_dir) / "test_model"
        model_dir.mkdir()
        (model_dir / "config.json").write_text('{"model_type": "test"}')

        self.cache_manager.add_to_cache("test/model", "main", model_dir, "huggingface")

        # Check if metadata was saved
        cache_key = "test/model_main"
        self.assertIn(cache_key, self.cache_manager.metadata)

        metadata = self.cache_manager.metadata[cache_key]
        self.assertEqual(metadata["model_id"], "test/model")
        self.assertEqual(metadata["revision"], "main")
        self.assertEqual(metadata["format"], "huggingface")

    def test_get_cached_model_path(self):
        """Test getting cached model path"""
        # Add model to cache
        model_dir = Path(self.temp_dir) / "test_model"
        model_dir.mkdir()
        (model_dir / "config.json").write_text('{"model_type": "test"}')

        self.cache_manager.add_to_cache("test/model", "main", model_dir, "huggingface")

        # Get cached path
        cached_path = self.cache_manager.get_cached_model_path("test/model", "main")
        self.assertEqual(cached_path, model_dir)

    def test_get_cached_model_path_not_found(self):
        """Test getting cached model path for non-existent model"""
        cached_path = self.cache_manager.get_cached_model_path("nonexistent/model", "main")
        self.assertIsNone(cached_path)

    def test_list_cached_models(self):
        """Test listing cached models"""
        # Add test models
        for i in range(3):
            model_dir = Path(self.temp_dir) / f"model_{i}"
            model_dir.mkdir()
            (model_dir / "config.json").write_text('{"model_type": "test"}')

            self.cache_manager.add_to_cache(
                f"test/model_{i}", "main", model_dir, "huggingface"
            )

        # List models
        cached_models = self.cache_manager.list_cached_models()
        self.assertEqual(len(cached_models), 3)

        for model in cached_models:
            self.assertIn("model_id", model)
            self.assertIn("path", model)
            self.assertIn("format", model)

    def test_clear_cache_all(self):
        """Test clearing all cache"""
        # Add test models
        for i in range(3):
            model_dir = Path(self.temp_dir) / f"model_{i}"
            model_dir.mkdir()
            self.cache_manager.add_to_cache(
                f"test/model_{i}", "main", model_dir, "huggingface"
            )

        # Clear all cache
        self.cache_manager.clear_cache()

        # Check if cache is empty
        self.assertEqual(len(self.cache_manager.metadata), 0)
        cached_models = self.cache_manager.list_cached_models()
        self.assertEqual(len(cached_models), 0)

    def test_clear_cache_specific(self):
        """Test clearing specific model cache"""
        # Add test models
        model_dirs = []
        for i in range(3):
            model_dir = Path(self.temp_dir) / f"model_{i}"
            model_dir.mkdir()
            model_dirs.append(model_dir)
            self.cache_manager.add_to_cache(
                f"test/model_{i}", "main", model_dir, "huggingface"
            )

        # Clear specific model
        self.cache_manager.clear_cache("test/model_1")

        # Check if only specific model was removed
        self.assertEqual(len(self.cache_manager.metadata), 2)
        cached_models = self.cache_manager.list_cached_models()
        self.assertEqual(len(cached_models), 2)

        # Verify correct model was removed
        model_ids = [m["model_id"] for m in cached_models]
        self.assertNotIn("test/model_1", model_ids)

class TestGGUFConverter(unittest.TestCase):
    """Test GGUF conversion functionality"""

    def setUp(self):
        """Set up test fixtures"""
        self.converter = GGUFConverter()

    def test_initialization(self):
        """Test converter initialization"""
        self.assertIsNotNone(self.converter)
        # Without llama.cpp installed, can_convert should return False
        self.assertFalse(self.converter.can_convert())

    def test_find_llama_cpp(self):
        """Test llama.cpp path finding"""
        # Should return None if llama.cpp is not installed
        path = self.converter._find_llama_cpp()
        self.assertIsNone(path)

class TestModelDownloader(unittest.TestCase):
    """Test model downloader functionality"""

    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        self.config = ModelDownloadConfig(
            model_id="test/model",
            cache_dir=self.temp_dir
        )
        self.downloader = ModelDownloader(self.config)

    def tearDown(self):
        """Clean up test fixtures"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_initialization(self):
        """Test downloader initialization"""
        self.assertIsNotNone(self.downloader.config)
        self.assertIsNotNone(self.downloader.auth)
        self.assertIsNotNone(self.downloader.cache_manager)
        self.assertIsInstance(self.downloader.download_progress, dict)
        self.assertIsInstance(self.downloader.active_downloads, dict)

    def test_get_download_progress_nonexistent(self):
        """Test getting progress for non-existent download"""
        progress = self.downloader.get_download_progress("nonexistent/model")
        self.assertIsNone(progress)

    def test_list_active_downloads_empty(self):
        """Test listing active downloads when none are active"""
        active_downloads = self.downloader.list_active_downloads()
        self.assertEqual(len(active_downloads), 0)

    def test_cancel_download_nonexistent(self):
        """Test canceling non-existent download"""
        result = self.downloader.cancel_download("nonexistent/model")
        self.assertFalse(result)

    def test_get_cached_models(self):
        """Test getting cached models"""
        cached_models = self.downloader.get_cached_models()
        self.assertIsInstance(cached_models, list)

    def test_clear_cache(self):
        """Test clearing cache"""
        # Should not raise an exception
        self.downloader.clear_cache()
        self.downloader.clear_cache("test/model")

class TestConfigManager(unittest.TestCase):
    """Test configuration management"""

    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        self.config_path = Path(self.temp_dir) / "test_config.json"
        self.config_manager = ConfigManager(str(self.config_path))

    def tearDown(self):
        """Clean up test fixtures"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_initialization(self):
        """Test config manager initialization"""
        self.assertIsNotNone(self.config_manager.config)
        self.assertIsInstance(self.config_manager.config.huggingface, object)
        self.assertIsInstance(self.config_manager.config.download, object)

    def test_save_and_load_config(self):
        """Test saving and loading configuration"""
        # Modify config
        self.config_manager.config.huggingface.max_workers = 8
        self.config_manager.config.conversion.convert_to_gguf = True

        # Save config
        self.config_manager.save_config()

        # Create new config manager and load
        new_config_manager = ConfigManager(str(self.config_path))

        # Verify loaded values
        self.assertEqual(new_config_manager.config.huggingface.max_workers, 8)
        self.assertTrue(new_config_manager.config.conversion.convert_to_gguf)

    def test_get_huggingface_token(self):
        """Test getting Hugging Face token"""
        # Test with token in config
        self.config_manager.config.huggingface.token = "test_token"
        token = self.config_manager.get_huggingface_token()
        self.assertEqual(token, "test_token")

        # Test with token in environment
        self.config_manager.config.huggingface.token = None
        with patch.dict(os.environ, {self.config_manager.config.security.token_env_var: "env_token"}):
            token = self.config_manager.get_huggingface_token()
            self.assertEqual(token, "env_token")

    def test_get_cache_dir(self):
        """Test getting cache directory"""
        cache_dir = self.config_manager.get_cache_dir()
        self.assertIsInstance(cache_dir, str)
        self.assertTrue(len(cache_dir) > 0)

    def test_is_valid_quantization(self):
        """Test quantization validation"""
        # Test valid quantization
        self.assertTrue(self.config_manager.is_valid_quantization("q4_0"))
        self.assertTrue(self.config_manager.is_valid_quantization("Q4_0"))  # Case insensitive

        # Test invalid quantization
        self.assertFalse(self.config_manager.is_valid_quantization("invalid"))

    def test_get_supported_quantizations(self):
        """Test getting supported quantizations"""
        quantizations = self.config_manager.get_supported_quantizations()
        self.assertIsInstance(quantizations, list)
        self.assertIn("q4_0", quantizations)
        self.assertIn("f16", quantizations)

    def test_validate_config(self):
        """Test configuration validation"""
        # Test with valid config
        issues = self.config_manager.validate_config()
        self.assertEqual(len(issues), 0)

        # Test with invalid config
        self.config_manager.config.huggingface.max_workers = 0
        self.config_manager.config.download.chunk_size = 500

        issues = self.config_manager.validate_config()
        self.assertGreater(len(issues), 0)

    def test_get_download_config_for_model(self):
        """Test getting download config for specific model"""
        download_config = self.config_manager.get_download_config_for_model("test/model")

        self.assertEqual(download_config["model_id"], "test/model")
        self.assertIn("token", download_config)
        self.assertIn("cache_dir", download_config)
        self.assertIn("revision", download_config)
        self.assertIn("max_workers", download_config)

    def test_get_download_config_for_model_with_overrides(self):
        """Test getting download config with overrides"""
        overrides = {
            "revision": "custom",
            "max_workers": 16,
            "convert_to_gguf": True
        }

        download_config = self.config_manager.get_download_config_for_model(
            "test/model", overrides
        )

        self.assertEqual(download_config["revision"], "custom")
        self.assertEqual(download_config["max_workers"], 16)
        self.assertTrue(download_config["convert_to_gguf"])

class TestIntegration(unittest.TestCase):
    """Integration tests for the model downloader"""

    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up test fixtures"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    @patch('huggingface_downloader.snapshot_download')
    def test_download_model_success(self, mock_snapshot_download):
        """Test successful model download"""
        # Mock successful download
        mock_download_path = Path(self.temp_dir) / "test_model"
        mock_download_path.mkdir()
        (mock_download_path / "config.json").write_text('{"model_type": "test"}')
        mock_snapshot_download.return_value = str(mock_download_path)

        # Create downloader and download
        config = ModelDownloadConfig(
            model_id="test/model",
            cache_dir=self.temp_dir
        )
        downloader = ModelDownloader(config)

        result = downloader.download_model("test/model")

        # Verify result
        self.assertIsNotNone(result)
        self.assertTrue(result.exists())
        self.assertTrue((result / "config.json").exists())

    def test_download_model_with_conversion(self):
        """Test model download with GGUF conversion"""
        # This test would require actual llama.cpp installation
        # For now, we'll test the configuration
        config = ModelDownloadConfig(
            model_id="test/model",
            cache_dir=self.temp_dir,
            convert_to_gguf=True,
            gguf_quantization="q4_0"
        )

        self.assertTrue(config.convert_to_gguf)
        self.assertEqual(config.gguf_quantization, "q4_0")

    def test_search_models(self):
        """Test model search functionality"""
        config = ModelDownloadConfig(model_id="test/model")
        downloader = ModelDownloader(config)

        # Mock the search to avoid API calls
        with patch.object(downloader, 'search_models') as mock_search:
            mock_search.return_value = [
                {"id": "test/model1", "downloads": 1000},
                {"id": "test/model2", "downloads": 500}
            ]

            results = downloader.search_models("test")
            self.assertEqual(len(results), 2)
            self.assertEqual(results[0]["id"], "test/model1")

class TestErrorHandling(unittest.TestCase):
    """Test error handling scenarios"""

    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up test fixtures"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_download_model_invalid_token(self):
        """Test download with invalid token"""
        config = ModelDownloadConfig(
            model_id="private/model",
            token="invalid_token",
            cache_dir=self.temp_dir
        )
        downloader = ModelDownloader(config)

        # Mock authentication failure
        with patch.object(downloader.auth, 'has_access_to_model', return_value=False):
            result = downloader.download_model("private/model")
            self.assertIsNone(result)

    def test_download_model_network_error(self):
        """Test download with network error"""
        config = ModelDownloadConfig(
            model_id="test/model",
            cache_dir=self.temp_dir
        )
        downloader = ModelDownloader(config)

        # Mock network error
        with patch('huggingface_downloader.snapshot_download', side_effect=Exception("Network error")):
            result = downloader.download_model("test/model")
            self.assertIsNone(result)

if __name__ == '__main__':
    # Configure logging for tests
    logging.basicConfig(level=logging.DEBUG)

    # Run tests
    unittest.main(verbosity=2)