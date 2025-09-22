#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DuckBot API Key Configuration Manager
Comprehensive system for managing API keys across all DuckBot v4.2 services
"""

import os
import json
import re
import logging
import requests
from pathlib import Path
from typing import Dict, Optional, List, Tuple, Any
from dataclasses import dataclass, asdict
from enum import Enum
import hashlib
import secrets
import yaml

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class APIKeyStatus(Enum):
    """API key validation status"""
    VALID = "valid"
    INVALID = "invalid"
    MISSING = "missing"
    EXPIRED = "expired"
    RATE_LIMITED = "rate_limited"

@dataclass
class APIKeyConfig:
    """Configuration for a single API key"""
    name: str
    env_var: str
    description: str
    required: bool = False
    service_url: Optional[str] = None
    validation_endpoint: Optional[str] = None
    validation_headers: Optional[Dict[str, str]] = None
    validation_method: str = "GET"
    format_validation: Optional[str] = None  # Regex pattern for format validation
    min_length: int = 10
    max_length: int = 500
    masked_value: str = "••••••••"
    provider_website: Optional[str] = None
    setup_instructions: Optional[str] = None

@dataclass
class APIKeyValidation:
    """Validation result for an API key"""
    key_name: str
    status: APIKeyStatus
    value: str
    error_message: Optional[str] = None
    response_time: Optional[float] = None
    last_validated: Optional[str] = None

class APIKeyManager:
    """Main API key management system"""

    def __init__(self, config_dir: Path = None):
        self.config_dir = config_dir or Path(__file__).parent / "config"
        self.env_file = self.config_dir / ".env"
        self.backup_file = self.config_dir / ".env.backup"
        self.config_file = self.config_dir / "api_keys_config.yaml"

        # Initialize API key configurations
        self.api_configs = self._initialize_api_configs()

        # Load existing configuration
        self._load_configuration()

        logger.info("API Key Manager initialized")

    def _initialize_api_configs(self) -> Dict[str, APIKeyConfig]:
        """Initialize all API key configurations"""
        configs = {
            "discord": APIKeyConfig(
                name="Discord Bot Token",
                env_var="DISCORD_TOKEN",
                description="Discord bot token for Discord integration",
                required=False,
                format_validation=r"^[A-Za-z0-9_-]{50,100}$",
                min_length=50,
                max_length=100,
                provider_website="https://discord.com/developers/applications",
                setup_instructions="""
1. Go to https://discord.com/developers/applications
2. Create a New Application
3. Go to Bot tab and click "Add Bot"
4. Under bot, click "Reset Token" to get your token
5. Enable Privileged Gateway Intents:
   - Message Content Intent
   - Server Members Intent
6. Copy the bot token
                """
            ),

            "openrouter": APIKeyConfig(
                name="OpenRouter API Key",
                env_var="OPENROUTER_API_KEY",
                description="OpenRouter API key for AI model access (Qwen, Claude, etc.)",
                required=True,
                service_url="https://openrouter.ai/api/v1",
                validation_endpoint="https://openrouter.ai/api/v1/models",
                validation_headers={"Authorization": "Bearer {key}"},
                format_validation=r"^sk-or-v1-[A-Za-z0-9_-]{40,100}$",
                min_length=50,
                max_length=150,
                provider_website="https://openrouter.ai/keys",
                setup_instructions="""
1. Go to https://openrouter.ai/keys
2. Sign up or log in
3. Create a new API key
4. Copy the key (starts with 'sk-or-v1-')
5. Free tier available with rate limits
                """
            ),

            "anthropic": APIKeyConfig(
                name="Anthropic Claude API Key",
                env_var="ANTHROPIC_API_KEY",
                description="Anthropic Claude API key for Claude model access",
                required=False,
                service_url="https://api.anthropic.com",
                validation_endpoint="https://api.anthropic.com/v1/messages",
                validation_headers={
                    "x-api-key": "{key}",
                    "anthropic-version": "2023-06-01"
                },
                validation_method="POST",
                validation_body='{"model": "claude-3-haiku-20240307", "max_tokens": 10, "messages": [{"role": "user", "content": "test"}]}',
                format_validation=r"^sk-ant-api03-[A-Za-z0-9_-]{80,120}$",
                min_length=90,
                max_length=140,
                provider_website="https://console.anthropic.com",
                setup_instructions="""
1. Go to https://console.anthropic.com
2. Sign up or log in
3. Go to API Keys section
4. Create a new API key
5. Copy the key (starts with 'sk-ant-api03-')
                """
            ),

            "openai": APIKeyConfig(
                name="OpenAI API Key",
                env_var="OPENAI_API_KEY",
                description="OpenAI API key for GPT model access",
                required=False,
                service_url="https://api.openai.com/v1",
                validation_endpoint="https://api.openai.com/v1/models",
                validation_headers={"Authorization": "Bearer {key}"},
                format_validation=r"^sk-[A-Za-z0-9_-]{40,60}$",
                min_length=45,
                max_length=70,
                provider_website="https://platform.openai.com/api-keys",
                setup_instructions="""
1. Go to https://platform.openai.com/api-keys
2. Sign up or log in
3. Create a new API key
4. Copy the key (starts with 'sk-')
                """
            ),

            "zai": APIKeyConfig(
                name="ZAI API Key",
                env_var="ZAI_API_KEY",
                description="ZAI API key for Claude Code ZAI integration",
                required=False,
                format_validation=r"^[A-Za-z0-9_-]{20,100}$",
                min_length=20,
                max_length=100,
                provider_website="https://z.ai/",
                setup_instructions="""
1. Go to https://z.ai/
2. Sign up or log in
3. Go to API section
4. Generate or copy your API key
                """
            ),

            "github": APIKeyConfig(
                name="GitHub Personal Access Token",
                env_var="GITHUB_TOKEN",
                description="GitHub token for repository operations",
                required=False,
                service_url="https://api.github.com",
                validation_endpoint="https://api.github.com/user",
                validation_headers={"Authorization": "token {key}"},
                format_validation=r"^ghp_[A-Za-z0-9_-]{30,50}$",
                min_length=35,
                max_length=60,
                provider_website="https://github.com/settings/tokens",
                setup_instructions="""
1. Go to https://github.com/settings/tokens
2. Click "Generate new token"
3. Select required scopes (repo, workflow, etc.)
4. Copy the token (starts with 'ghp_')
                """
            ),

            "google": APIKeyConfig(
                name="Google AI API Key",
                env_var="GOOGLE_API_KEY",
                description="Google AI API key for Gemini models",
                required=False,
                format_validation=r"^AIza[0-9A-Za-z_-]{30,40}$",
                min_length=35,
                max_length=45,
                provider_website="https://aistudio.google.com/app/apikey",
                setup_instructions="""
1. Go to https://aistudio.google.com/app/apikey
2. Sign up or log in
3. Create a new API key
4. Copy the key (starts with 'AIza')
                """
            ),

            "groq": APIKeyConfig(
                name="Groq API Key",
                env_var="GROQ_API_KEY",
                description="Groq API key for fast LLM inference",
                required=False,
                service_url="https://api.groq.com",
                validation_endpoint="https://api.groq.com/openai/v1/models",
                validation_headers={"Authorization": "Bearer {key}"},
                format_validation=r"^gsk_[A-Za-z0-9_-]{40,60}$",
                min_length=45,
                max_length=65,
                provider_website="https://console.groq.com",
                setup_instructions="""
1. Go to https://console.groq.com
2. Sign up or log in
3. Go to API Keys section
4. Create a new API key
5. Copy the key (starts with 'gsk_')
                """
            )
        }
        return configs

    def _load_configuration(self):
        """Load existing configuration from files"""
        # Load .env file if it exists
        if self.env_file.exists():
            with open(self.env_file, 'r', encoding='utf-8') as f:
                self.env_content = f.read()
        else:
            self.env_content = ""

        # Load API key config if it exists
        if self.config_file.exists():
            with open(self.config_file, 'r', encoding='utf-8') as f:
                self.api_key_config = yaml.safe_load(f) or {}
        else:
            self.api_key_config = {}

    def get_api_key(self, key_name: str) -> Optional[str]:
        """Get API key value from environment"""
        return os.getenv(self.api_configs[key_name].env_var)

    def set_api_key(self, key_name: str, value: str) -> bool:
        """Set API key value in .env file"""
        if key_name not in self.api_configs:
            logger.error(f"Unknown API key: {key_name}")
            return False

        config = self.api_configs[key_name]

        # Validate format
        if config.format_validation and not re.match(config.format_validation, value):
            logger.error(f"Invalid format for {key_name}")
            return False

        # Validate length
        if not (config.min_length <= len(value) <= config.max_length):
            logger.error(f"Invalid length for {key_name}")
            return False

        # Create backup
        if self.env_file.exists():
            with open(self.backup_file, 'w', encoding='utf-8') as f:
                f.write(self.env_content)

        # Update .env file
        env_var = config.env_var
        pattern = rf"^{env_var}=.*$"
        replacement = f"{env_var}={value}"

        if re.search(pattern, self.env_content, re.MULTILINE):
            self.env_content = re.sub(pattern, replacement, self.env_content, flags=re.MULTILINE)
        else:
            if self.env_content and not self.env_content.endswith('\n'):
                self.env_content += '\n'
            self.env_content += f"{replacement}\n"

        with open(self.env_file, 'w', encoding='utf-8') as f:
            f.write(self.env_content)

        # Update environment
        os.environ[env_var] = value

        logger.info(f"Updated {key_name} API key")
        return True

    def validate_api_key(self, key_name: str) -> APIKeyValidation:
        """Validate an API key"""
        if key_name not in self.api_configs:
            return APIKeyValidation(
                key_name=key_name,
                status=APIKeyStatus.INVALID,
                value="",
                error_message="Unknown API key"
            )

        config = self.api_configs[key_name]
        value = self.get_api_key(key_name)

        if not value:
            return APIKeyValidation(
                key_name=key_name,
                status=APIKeyStatus.MISSING,
                value="",
                error_message="API key not found"
            )

        # Format validation
        if config.format_validation and not re.match(config.format_validation, value):
            return APIKeyValidation(
                key_name=key_name,
                status=APIKeyStatus.INVALID,
                value=value,
                error_message="Invalid format"
            )

        # Live validation if validation endpoint is available
        if config.validation_endpoint:
            try:
                headers = {}
                if config.validation_headers:
                    for key, template in config.validation_headers.items():
                        headers[key] = template.format(key=value)

                start_time = time.time()

                if config.validation_method == "POST":
                    response = requests.post(
                        config.validation_endpoint,
                        headers=headers,
                        json=json.loads(getattr(config, 'validation_body', '{}')),
                        timeout=10
                    )
                else:
                    response = requests.get(
                        config.validation_endpoint,
                        headers=headers,
                        timeout=10
                    )

                response_time = time.time() - start_time

                if response.status_code == 200:
                    return APIKeyValidation(
                        key_name=key_name,
                        status=APIKeyStatus.VALID,
                        value=value,
                        response_time=response_time,
                        last_validated=datetime.now().isoformat()
                    )
                elif response.status_code == 401:
                    return APIKeyValidation(
                        key_name=key_name,
                        status=APIKeyStatus.INVALID,
                        value=value,
                        error_message="Unauthorized - Invalid API key"
                    )
                elif response.status_code == 429:
                    return APIKeyValidation(
                        key_name=key_name,
                        status=APIKeyStatus.RATE_LIMITED,
                        value=value,
                        error_message="Rate limit exceeded"
                    )
                else:
                    return APIKeyValidation(
                        key_name=key_name,
                        status=APIKeyStatus.INVALID,
                        value=value,
                        error_message=f"HTTP {response.status_code}: {response.text[:100]}"
                    )

            except requests.RequestException as e:
                return APIKeyValidation(
                    key_name=key_name,
                    status=APIKeyStatus.INVALID,
                    value=value,
                    error_message=f"Connection error: {str(e)}"
                )

        # If no live validation, just check format and length
        return APIKeyValidation(
            key_name=key_name,
            status=APIKeyStatus.VALID,
            value=value,
            last_validated=datetime.now().isoformat()
        )

    def validate_all_keys(self) -> Dict[str, APIKeyValidation]:
        """Validate all configured API keys"""
        results = {}
        for key_name in self.api_configs:
            results[key_name] = self.validate_api_key(key_name)
        return results

    def get_required_keys_status(self) -> Dict[str, bool]:
        """Get status of required API keys"""
        status = {}
        for key_name, config in self.api_configs.items():
            if config.required:
                value = self.get_api_key(key_name)
                status[key_name] = bool(value)
        return status

    def get_setup_instructions(self, key_name: str) -> str:
        """Get setup instructions for an API key"""
        if key_name not in self.api_configs:
            return "Unknown API key"

        config = self.api_configs[key_name]
        instructions = f"# {config.name} Setup Instructions\n\n"
        instructions += f"Environment Variable: `{config.env_var}`\n\n"
        instructions += f"Description: {config.description}\n\n"

        if config.setup_instructions:
            instructions += config.setup_instructions

        if config.provider_website:
            instructions += f"\nProvider Website: {config.provider_website}\n"

        return instructions

    def mask_api_key(self, key_value: str, key_name: str = None) -> str:
        """Mask an API key for display"""
        if key_name and key_name in self.api_configs:
            config = self.api_configs[key_name]
            return config.masked_value

        # Generic masking
        if len(key_value) > 8:
            return key_value[:4] + "•" * (len(key_value) - 8) + key_value[-4:]
        return "•" * len(key_value)

    def get_configuration_summary(self) -> Dict[str, Any]:
        """Get a summary of current configuration"""
        summary = {
            "config_file": str(self.env_file),
            "total_keys": len(self.api_configs),
            "required_keys": sum(1 for config in self.api_configs.values() if config.required),
            "configured_keys": 0,
            "valid_keys": 0,
            "keys": {}
        }

        validations = self.validate_all_keys()

        for key_name, validation in validations.items():
            config = self.api_configs[key_name]
            masked_value = self.mask_api_key(validation.value, key_name) if validation.value else ""

            summary["keys"][key_name] = {
                "name": config.name,
                "required": config.required,
                "configured": validation.status != APIKeyStatus.MISSING,
                "valid": validation.status == APIKeyStatus.VALID,
                "status": validation.status.value,
                "masked_value": masked_value,
                "provider_website": config.provider_website
            }

            if validation.status != APIKeyStatus.MISSING:
                summary["configured_keys"] += 1
            if validation.status == APIKeyStatus.VALID:
                summary["valid_keys"] += 1

        return summary

# Import required modules
import time
from datetime import datetime

# Global instance
_api_key_manager = None

def get_api_key_manager() -> APIKeyManager:
    """Get global API key manager instance"""
    global _api_key_manager
    if _api_key_manager is None:
        _api_key_manager = APIKeyManager()
    return _api_key_manager

if __name__ == "__main__":
    # Test the API key manager
    manager = get_api_key_manager()
    summary = manager.get_configuration_summary()
    print(json.dumps(summary, indent=2))