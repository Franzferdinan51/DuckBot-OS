#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DuckBot Enterprise Ecosystem Startup Script
Launches: DuckBot, ComfyUI, n8n, Open Notebook
Enterprise Features: Logging, Failovers, Health Monitoring, Auto-Recovery
"""

import os
import sys
import time
import subprocess
import threading
import signal
import json
import requests
import psutil
import shutil
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import logging
import asyncio
from dataclasses import dataclass
from enum import Enum
import sqlite3
from datetime import datetime, timedelta
import yaml

# Improve Windows console Unicode handling
if os.name == 'nt':
    try:
        if hasattr(sys.stdout, 'reconfigure'):
            sys.stdout.reconfigure(encoding='utf-8')
        if hasattr(sys.stderr, 'reconfigure'):
            sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

# Import required modules with fallbacks
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    def load_dotenv():
        pass

from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
import concurrent.futures

# --- Enterprise Logging Configuration ---
class LogLevel(Enum):
    DEBUG = logging.DEBUG
    INFO = logging.INFO
    WARNING = logging.WARNING
    ERROR = logging.ERROR
    CRITICAL = logging.CRITICAL

class EnterpriseLogger:
    def __init__(self, log_dir: Path = None):
        self.log_dir = log_dir or Path(__file__).parent / "logs"
        self.log_dir.mkdir(exist_ok=True)
        
        # Create multiple loggers for different purposes
        self.setup_loggers()
    
    def setup_loggers(self):
        """Setup enterprise-grade logging with multiple handlers"""
        
        # Main application logger
        self.logger = logging.getLogger('DuckBot.Ecosystem')
        self.logger.setLevel(logging.DEBUG)
        
        # Performance logger
        self.perf_logger = logging.getLogger('DuckBot.Performance')
        self.perf_logger.setLevel(logging.INFO)
        
        # Security logger
        self.security_logger = logging.getLogger('DuckBot.Security')
        self.security_logger.setLevel(logging.WARNING)
        
        # Create formatters
        detailed_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - [PID:%(process)d] - %(message)s'
        )
        
        simple_formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s'
        )
        
        # Main log file - rotating by size
        main_handler = RotatingFileHandler(
            self.log_dir / 'ecosystem_main.log',
            maxBytes=10*1024*1024,  # 10MB
            backupCount=10,
            encoding='utf-8'
        )
        main_handler.setFormatter(detailed_formatter)
        main_handler.setLevel(logging.DEBUG)
        
        # Error log file - rotating by time
        error_handler = TimedRotatingFileHandler(
            self.log_dir / 'ecosystem_errors.log',
            when='midnight',
            interval=1,
            backupCount=30,
            encoding='utf-8'
        )
        error_handler.setFormatter(detailed_formatter)
        error_handler.setLevel(logging.ERROR)
        
        # Performance log file
        perf_handler = RotatingFileHandler(
            self.log_dir / 'ecosystem_performance.log',
            maxBytes=5*1024*1024,
            backupCount=5,
            encoding='utf-8'
        )
        perf_handler.setFormatter(detailed_formatter)
        
        # Console handler with color support
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(simple_formatter)
        console_handler.setLevel(logging.INFO)
        
        # Add handlers to loggers
        self.logger.addHandler(main_handler)
        self.logger.addHandler(error_handler)
        self.logger.addHandler(console_handler)
        
        self.perf_logger.addHandler(perf_handler)
        self.security_logger.addHandler(error_handler)
        
        # Create audit trail
        audit_handler = RotatingFileHandler(
            self.log_dir / 'ecosystem_audit.log',
            maxBytes=20*1024*1024,
            backupCount=50,
            encoding='utf-8'
        )
        audit_handler.setFormatter(detailed_formatter)
        self.security_logger.addHandler(audit_handler)

# Initialize enterprise logger
enterprise_logger = EnterpriseLogger()
logger = enterprise_logger.logger
perf_logger = enterprise_logger.perf_logger
security_logger = enterprise_logger.security_logger

@dataclass
class ServiceConfig:
    name: str
    port: int
    health_endpoint: str
    startup_delay: int
    restart_attempts: int = 3
    restart_delay: int = 30
    timeout: int = 60
    critical: bool = False
    dependencies: List[str] = None
    # Additional optional fields supported by ecosystem_config.yaml
    optional: bool = False
    skip_if_unavailable: bool = False
    local_paths: List[str] = None

class ServiceStatus(Enum):
    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    FAILED = "failed"
    RESTARTING = "restarting"

class EcosystemManager:
    def __init__(self):
        self.processes: Dict[str, subprocess.Popen] = {}
        self.service_status: Dict[str, ServiceStatus] = {}
        self.restart_counts: Dict[str, int] = {}
        self.last_restart: Dict[str, datetime] = {}
        self.base_dir = Path(__file__).parent
        self.shutdown_requested = False
        self.config_file = self.base_dir / "ecosystem_config.yaml"
        
        # Performance monitoring
        self.start_time = datetime.now()
        self.service_metrics: Dict[str, Dict] = {}
        
        # Database for persistent state
        self.db_path = self.base_dir / "ecosystem_state.db"
        self.init_database()
        
        # Load configuration
        self.load_configuration()
        
        logger.info(f"[LAUNCH] DuckBot Enterprise Ecosystem Manager initialized")
        security_logger.info(f"Ecosystem manager started by user: {os.getenv('USERNAME', 'unknown')}")

    def init_database(self):
        """Initialize SQLite database for persistent state"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS service_history (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        service_name TEXT NOT NULL,
                        status TEXT NOT NULL,
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                        details TEXT
                    )
                ''')
                
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS performance_metrics (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        service_name TEXT NOT NULL,
                        metric_name TEXT NOT NULL,
                        metric_value REAL NOT NULL,
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                ''')

                conn.execute('''
                    CREATE TABLE IF NOT EXISTS projects (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                ''')

                conn.execute('''
                    CREATE TABLE IF NOT EXISTS tasks (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        project_id INTEGER NOT NULL,
                        title TEXT NOT NULL,
                        status TEXT NOT NULL DEFAULT 'todo',
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY(project_id) REFERENCES projects(id)
                    )
                ''')
                
                conn.commit()
                logger.debug("[OK] Database initialized successfully")
        except Exception as e:
            logger.error(f"[FAIL] Failed to initialize database: {e}")

    def log_service_event(self, service_name: str, status: str, details: str = None):
        """Log service events to database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    "INSERT INTO service_history (service_name, status, details) VALUES (?, ?, ?)",
                    (service_name, status, details)
                )
                conn.commit()
        except Exception as e:
            logger.error(f"Failed to log service event: {e}")

    def load_configuration(self):
        """Load service configuration from YAML file"""
        default_config = {
            'services': {
                'comfyui': {
                    'name': 'ComfyUI',
                    'port': 8188,
                    'health_endpoint': 'http://localhost:8188',
                    'startup_delay': 15,
                    'restart_attempts': 5,
                    'restart_delay': 45,
                    'timeout': 120,
                    'critical': True,
                    'dependencies': []
                },
                'n8n': {
                    'name': 'n8n',
                    'port': 5678,
                    'health_endpoint': 'http://localhost:5678/healthz',
                    'startup_delay': 20,
                    'restart_attempts': 3,
                    'restart_delay': 30,
                    'timeout': 90,
                    'critical': False,
                    'dependencies': []
                },
                'open_notebook': {
                    'name': 'Open Notebook',
                    'port': 8502,
                    'health_endpoint': 'http://localhost:8502/health',
                    'startup_delay': 25,
                    'restart_attempts': 3,
                    'restart_delay': 40,
                    'timeout': 100,
                    'critical': False,
                    'dependencies': []
                },
                'jupyter': {
                    'name': 'Jupyter',
                    'port': 8889,
                    'health_endpoint': 'http://localhost:8889',
                    'startup_delay': 10,
                    'restart_attempts': 2,
                    'restart_delay': 20,
                    'timeout': 60,
                    'critical': False,
                    'dependencies': []
                },
                'duckbot': {
                    'name': 'DuckBot',
                    'port': 0,
                    'health_endpoint': '',
                    'startup_delay': 5,
                    'restart_attempts': 5,
                    'restart_delay': 30,
                    'timeout': 30,
                    'critical': True,
                    'dependencies': ['comfyui']
                },
                'qwen3_omni_ui': {
                    'name': 'Qwen3-Omni-UI',
                    'port': 8788,
                    'health_endpoint': 'http://localhost:8788/health',
                    'startup_delay': 10,
                    'restart_attempts': 3,
                    'restart_delay': 30,
                    'timeout': 60,
                    'critical': False,
                    'dependencies': []
                },
                'open-webui': {
                    'name': 'Open WebUI',
                    'port': 8080,
                    'health_endpoint': 'http://localhost:8080',
                    'startup_delay': 20,
                    'restart_attempts': 3,
                    'restart_delay': 30,
                    'timeout': 90,
                    'critical': False,
                    'dependencies': []
                }
            },
            'monitoring': {
                'health_check_interval': 30,
                'performance_log_interval': 60,
                'restart_cooldown': 300
            }
        }
        
        if not self.config_file.exists():
            # Create default config
            with open(self.config_file, 'w') as f:
                yaml.safe_dump(default_config, f, default_flow_style=False)
            logger.info("[OK] Created default configuration file")
        
        try:
            with open(self.config_file, 'r') as f:
                config = yaml.safe_load(f)
            
            self.services = {}
            for service_id, service_config in config['services'].items():
                self.services[service_id] = ServiceConfig(**service_config)
            
            self.monitoring_config = config.get('monitoring', {})
            logger.info(f"[OK] Loaded configuration for {len(self.services)} services")
            
        except Exception as e:
            logger.error(f"[FAIL] Failed to load configuration: {e}")
            # Fall back to default config
            self.services = {k: ServiceConfig(**v) for k, v in default_config['services'].items()}
            self.monitoring_config = default_config['monitoring']

    def install_python_package(self, package_name: str, retries: int = 3) -> bool:
        """Install Python package with retry logic"""
        for attempt in range(retries):
            try:
                logger.info(f"[PACKAGE] Installing {package_name} (attempt {attempt + 1}/{retries})")
                result = subprocess.run([
                    sys.executable, '-m', 'pip', 'install', package_name, '--upgrade'
                ], check=True, capture_output=True, text=True, timeout=300)
                
                logger.info(f"[OK] {package_name} installed successfully")
                return True
                
            except subprocess.TimeoutExpired:
                logger.warning(f"⏳ Package installation timeout for {package_name}")
                if attempt < retries - 1:
                    time.sleep(10)
                    continue
                    
            except subprocess.CalledProcessError as e:
                logger.warning(f"[FAIL] Attempt {attempt + 1} failed for {package_name}: {e.stderr}")
                if attempt < retries - 1:
                    time.sleep(5)
                    continue
                    
            except Exception as e:
                logger.error(f"[FAIL] Unexpected error installing {package_name}: {e}")
                return False
        
        logger.error(f"[FAIL] Failed to install {package_name} after {retries} attempts")
        return False

    def install_nodejs(self) -> bool:
        """Install Node.js with platform-specific logic"""
        logger.info("[PACKAGE] Attempting Node.js installation...")
        
        if sys.platform == "win32":
            # Check if winget is available
            try:
                subprocess.run(['winget', '--version'], capture_output=True, check=True)
                logger.info("[EMOJI] Found winget, attempting Node.js installation...")
                subprocess.run(['winget', 'install', 'OpenJS.NodeJS'], check=True, timeout=600)
                logger.info("[OK] Node.js installed via winget")
                return True
            except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
                # Check if chocolatey is available
                try:
                    subprocess.run(['choco', '--version'], capture_output=True, check=True)
                    logger.info("[EMOJI] Found Chocolatey, attempting Node.js installation...")
                    subprocess.run(['choco', 'install', 'nodejs', '-y'], check=True, timeout=600)
                    logger.info("[OK] Node.js installed via Chocolatey")
                    return True
                except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
                    logger.error("[FAIL] Please install Node.js manually from https://nodejs.org/")
                    return False
                    
        elif sys.platform == "darwin":  # macOS
            try:
                subprocess.run(['brew', '--version'], capture_output=True, check=True)
                subprocess.run(['brew', 'install', 'node'], check=True, timeout=600)
                logger.info("[OK] Node.js installed via Homebrew")
                return True
            except Exception:
                logger.error("[FAIL] Please install Node.js manually or install Homebrew first")
                return False
                
        else:  # Linux
            # Try multiple package managers
            package_managers = [
                (['sudo', 'apt-get', 'update'], ['sudo', 'apt-get', 'install', '-y', 'nodejs', 'npm']),
                (['sudo', 'yum', 'install', '-y', 'nodejs', 'npm'],),
                (['sudo', 'dnf', 'install', '-y', 'nodejs', 'npm'],),
                (['sudo', 'pacman', '-S', '--noconfirm', 'nodejs', 'npm'],),
            ]
            
            for commands in package_managers:
                try:
                    for cmd in commands:
                        subprocess.run(cmd, check=True, timeout=300)
                    logger.info(f"[OK] Node.js installed via {commands[0][1]}")
                    return True
                except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
                    continue
            
            logger.error("[FAIL] Could not install Node.js automatically")
            return False

    def check_and_install_dependencies(self) -> bool:
        """Enterprise dependency management with comprehensive error handling"""
        logger.info("[EMOJI] Starting enterprise dependency check...")
        start_time = time.time()
        
        all_success = True
        failed_packages = []
        
        # Create/check .env file
        env_file = self.base_dir / '.env'
        if not env_file.exists():
            logger.warning("[WARN] .env file not found")
            try:
                print("\n=== DuckBot API Configuration ===")
                discord_token = input("Please enter your DISCORD_TOKEN (or press Enter to skip): ").strip()
                openrouter_key = input("Please enter your OPENROUTER_API_KEY (or press Enter to skip): ").strip()

                with open(env_file, 'w') as f:
                    if discord_token:
                        f.write(f"DISCORD_TOKEN={discord_token}\n")
                    if openrouter_key:
                        f.write(f"OPENROUTER_API_KEY={openrouter_key}\n")
                    f.write(f"ECOSYSTEM_LOG_LEVEL=INFO\n")
                    f.write(f"MAX_RESTART_ATTEMPTS=3\n")
                    f.write(f"HEALTH_CHECK_INTERVAL=30\n")
                    f.write(f"AI_CONFIDENCE_MIN=0.75\n")
                    f.write(f"AI_LOCAL_CONF_MIN=0.68\n")

                logger.info("[OK] .env file created with default settings")
                load_dotenv()

            except Exception as e:
                logger.error(f"[FAIL] Failed to create .env file: {e}")
                return False

        # Python package dependencies with proper import mapping
        python_deps = {
            'discord.py': 'discord',
            'aiohttp': 'aiohttp', 
            'requests': 'requests',
            'torch': 'torch',
            'opencv-python': 'cv2',
            'Pillow': 'PIL',
            'python-dotenv': 'dotenv',
            'psutil': 'psutil',
            'websockets': 'websockets',
            'neo4j': 'neo4j',
            'SpeechRecognition': 'speech_recognition',
            'pyttsx3': 'pyttsx3',
            'watchdog': 'watchdog',
            'PyYAML': 'yaml',
            'beautifulsoup4': 'bs4'
        }
        
        optional_deps = {
            'jupyter': 'jupyter',
            'streamlit': 'streamlit'
        }
        
        # Install required packages
        logger.info("[PACKAGE] Checking required Python packages...")
        for pkg, import_name in python_deps.items():
            try:
                __import__(import_name)
                logger.debug(f"[OK] {pkg} already installed")
            except ImportError:
                logger.info(f"[PACKAGE] Installing required package: {pkg}")
                if not self.install_python_package(pkg):
                    logger.error(f"[FAIL] Failed to install critical package: {pkg}")
                    failed_packages.append(pkg)
                    all_success = False
        
        # Install optional packages
        logger.info("[PACKAGE] Checking optional Python packages...")
        for pkg, import_name in optional_deps.items():
            try:
                __import__(import_name)
                logger.debug(f"[OK] {pkg} already installed")
            except ImportError:
                logger.info(f"[PACKAGE] Installing optional package: {pkg}")
                if not self.install_python_package(pkg):
                    logger.warning(f"[WARN] Failed to install optional package: {pkg}")

        # Node.js and n8n installation
        logger.info("[PACKAGE] Checking Node.js and n8n...")
        node_installed = False
        
        try:
            result = subprocess.run(['node', '--version'], capture_output=True, check=True, text=True)
            version = result.stdout.strip()
            logger.info(f"[OK] Node.js already installed: {version}")
            node_installed = True
            
            # Log version info for security audit
            security_logger.info(f"Node.js version detected: {version}")
            
        except (subprocess.CalledProcessError, FileNotFoundError):
            logger.warning("[WARN] Node.js not found, attempting installation...")
            if self.install_nodejs():
                node_installed = True
            else:
                logger.error("[FAIL] Node.js installation failed")
        
        # Install n8n if Node.js is available
        if node_installed:
            n8n_installed = False
            
            # Check multiple possible n8n locations (Windows-aware)
            n8n_paths = [
                'n8n',  # Try PATH first
                r'C:\Users\Duck1\AppData\Roaming\npm\n8n.cmd',  # Windows npm global
                os.path.expanduser('~/AppData/Roaming/npm/n8n.cmd')  # User npm global
            ]
            
            for n8n_path in n8n_paths:
                try:
                    # Check if n8n is installed with timeout
                    result = subprocess.run([n8n_path, '--version'], capture_output=True, check=True, text=True, timeout=10)
                    logger.info(f"[OK] n8n already installed at {n8n_path}: {result.stdout.strip()}")
                    n8n_installed = True
                    break
                except subprocess.TimeoutExpired:
                    logger.debug(f"[WARN] n8n version check timed out for {n8n_path}")
                    continue
                except (subprocess.CalledProcessError, FileNotFoundError):
                    continue  # Try next path
            
            if not n8n_installed:
                logger.debug("[EMOJI] n8n not found in standard locations")
            
            # Only install if n8n is not already working
            if not n8n_installed:
                logger.info("[PACKAGE] Installing n8n...")
                try:
                    # Try to find npm executable
                    npm_cmd = 'npm'
                    
                    # Check if npm is in PATH
                    try:
                        subprocess.run(['npm', '--version'], capture_output=True, check=True)
                    except (subprocess.CalledProcessError, FileNotFoundError):
                        # Try to find npm in common Node.js installation paths
                        npm_paths = []
                        
                        if sys.platform == "win32":
                            npm_paths = [
                                Path(os.path.expanduser("~")) / "AppData" / "Roaming" / "npm" / "npm.cmd",
                                Path("C:/Program Files/nodejs/npm.cmd"),
                                Path("C:/Program Files (x86)/nodejs/npm.cmd"),
                            ]
                        else:
                            npm_paths = [
                                Path("/usr/local/bin/npm"),
                                Path("/usr/bin/npm"),
                                Path(os.path.expanduser("~")) / ".npm-global" / "bin" / "npm",
                            ]
                        
                        npm_found = False
                        for npm_path in npm_paths:
                            if npm_path.exists():
                                npm_cmd = str(npm_path)
                                npm_found = True
                                logger.info(f"[OK] Found npm at: {npm_path}")
                                break
                        
                        if not npm_found:
                            logger.warning("[WARN] npm not found in common paths, trying default")
                    
                    # Install n8n
                    logger.info(f"[PACKAGE] Installing n8n using: {npm_cmd}")
                    result = subprocess.run([npm_cmd, 'install', '-g', 'n8n'], 
                                          check=True, timeout=300, 
                                          capture_output=True, text=True)
                    logger.info("[OK] n8n installed successfully")
                    
                except subprocess.TimeoutExpired:
                    logger.warning("[WARN] n8n installation timeout - will try to use existing installation")
                except subprocess.CalledProcessError as e:
                    logger.warning(f"[WARN] Failed to install n8n globally: {e.stderr if hasattr(e, 'stderr') and e.stderr else str(e)}")
                    logger.info("[EMOJI] You may need to install n8n manually: npm install -g n8n")
                except FileNotFoundError as e:
                    logger.warning(f"[WARN] npm command not found: {e}")
                    logger.info("[EMOJI] Please ensure Node.js and npm are properly installed and in PATH")
                except Exception as e:
                    logger.warning(f"[WARN] Unexpected error installing n8n: {e}")

        # Git dependency check
        try:
            result = subprocess.run(['git', '--version'], capture_output=True, check=True, text=True)
            logger.info(f"[OK] Git available: {result.stdout.strip()}")
        except (subprocess.CalledProcessError, FileNotFoundError):
            logger.warning("[WARN] Git not found - some features may not work")
            
        # Docker dependency check (for open-notebook)
        try:
            result = subprocess.run(['docker', '--version'], capture_output=True, check=True, text=True)
            logger.info(f"[OK] Docker available: {result.stdout.strip()}")
        except (subprocess.CalledProcessError, FileNotFoundError):
            logger.warning("[WARN] Docker not found - open-notebook will use fallback mode")

        install_time = time.time() - start_time
        perf_logger.info(f"Dependency check completed in {install_time:.2f}s")
        
        if failed_packages:
            logger.error(f"[FAIL] Failed to install critical packages: {failed_packages}")
            security_logger.error(f"Critical dependency installation failed: {failed_packages}")
            return False
        
        logger.info("[OK] All dependencies satisfied")
        return all_success

    def get_npm_executable_path(self, executable_name: str) -> Optional[str]:
        """Find npm global executable with enterprise-grade path resolution"""
        logger.debug(f"[EMOJI] Searching for npm executable: {executable_name}")
        
        # Check PATH first
        try:
            result = subprocess.run([executable_name, '--version'], 
                                  capture_output=True, check=True, text=True)
            logger.debug(f"[OK] Found {executable_name} in PATH")
            return executable_name
        except (subprocess.CalledProcessError, FileNotFoundError):
            pass
        
        # Get npm global path
        try:
            result = subprocess.run(['npm', 'config', 'get', 'prefix'], 
                                  capture_output=True, check=True, text=True)
            npm_prefix = result.stdout.strip()
            
            # Try different possible paths
            possible_paths = [
                Path(npm_prefix) / 'bin' / executable_name,
                Path(npm_prefix) / executable_name,
                Path(npm_prefix) / 'node_modules' / '.bin' / executable_name,
            ]
            
            if sys.platform == "win32":
                possible_paths.extend([
                    Path(npm_prefix) / f'{executable_name}.cmd',
                    Path(npm_prefix) / f'{executable_name}.bat',
                    Path(npm_prefix) / 'bin' / f'{executable_name}.cmd',
                ])
            
            for path in possible_paths:
                if path.exists():
                    logger.debug(f"[OK] Found {executable_name} at: {path}")
                    return str(path)
                    
        except subprocess.CalledProcessError:
            logger.debug("Could not determine npm prefix")
        
        # Check common global installation paths
        common_paths = []
        
        if sys.platform == "win32":
            common_paths = [
                Path(os.path.expanduser("~")) / "AppData" / "Roaming" / "npm" / f"{executable_name}.cmd",
                Path("C:") / "Users" / os.getenv("USERNAME", "") / "AppData" / "Roaming" / "npm" / f"{executable_name}.cmd",
            ]
        else:
            common_paths = [
                Path("/usr/local/bin") / executable_name,
                Path("/usr/bin") / executable_name,
                Path(os.path.expanduser("~")) / ".npm-global" / "bin" / executable_name,
            ]
        
        for path in common_paths:
            if path.exists():
                logger.debug(f"[OK] Found {executable_name} at common path: {path}")
                return str(path)
        
        logger.warning(f"[WARN] Could not find {executable_name}")
        return None

    def install_open_notebook(self) -> bool:
        """Enterprise-grade open-notebook installation with comprehensive error handling"""
        logger.info("[PACKAGE] Checking open-notebook installation...")
        
        open_notebook_dir = self.base_dir / "open-notebook"
        
        # Clone repository if not exists
        if not open_notebook_dir.exists():
            try:
                logger.info("⬇[EMOJI] Cloning open-notebook repository...")
                subprocess.run([
                    'git', 'clone', 
                    'https://github.com/lfnovo/open-notebook.git',
                    str(open_notebook_dir)
                ], check=True, timeout=300)
                
                logger.info("[OK] open-notebook repository cloned successfully")
                self.log_service_event("open_notebook", "repository_cloned")
                
            except subprocess.TimeoutExpired:
                logger.error("[FAIL] Repository clone timeout")
                return False
            except subprocess.CalledProcessError as e:
                logger.error(f"[FAIL] Failed to clone open-notebook: {e}")
                return False
            except Exception as e:
                logger.error(f"[FAIL] Unexpected error during clone: {e}")
                return False

        # Setup environment file
        env_file = open_notebook_dir / '.env'
        if not env_file.exists():
            try:
                logger.info("[SETTINGS] Creating open-notebook .env configuration...")
                
                # Create comprehensive .env file
                env_content = """# Open Notebook Configuration
OPENAI_API_KEY=not_applicable
MODEL_PROVIDER=local
LOCAL_MODEL_URL=http://localhost:1234/v1
DEFAULT_MODEL=local-model
NOTEBOOK_PORT=8502
API_PORT=5055
LOG_LEVEL=INFO
ENABLE_AUTHENTICATION=false
"""
                with open(env_file, 'w') as f:
                    f.write(env_content)
                
                logger.info("[OK] open-notebook .env file created")
                
            except Exception as e:
                logger.error(f"[FAIL] Failed to create .env file: {e}")
                return False

        # Install Python dependencies
        requirements_file = open_notebook_dir / "requirements.txt"
        if requirements_file.exists():
            try:
                logger.info("[PACKAGE] Installing open-notebook Python dependencies...")
                subprocess.run([
                    sys.executable, '-m', 'pip', 'install', 
                    '-r', str(requirements_file)
                ], check=True, timeout=600)
                
                logger.info("[OK] open-notebook dependencies installed")
                
            except subprocess.TimeoutExpired:
                logger.error("[FAIL] Dependency installation timeout")
                return False
            except subprocess.CalledProcessError as e:
                logger.error(f"[FAIL] Failed to install open-notebook dependencies: {e}")
                return False

        logger.info("[OK] open-notebook installation completed")
        return True

    def check_port_available(self, port: int) -> bool:
        """Enterprise port availability check with detailed logging"""
        try:
            connections = psutil.net_connections()
            for conn in connections:
                if hasattr(conn, 'laddr') and conn.laddr and conn.laddr.port == port:
                    logger.debug(f"Port {port} is occupied by PID: {conn.pid}")
                    return False
            return True
        except Exception as e:
            logger.error(f"Error checking port {port}: {e}")
            return False

    def wait_for_service(self, service_name: str, max_retries: int = None) -> bool:
        """Enterprise health check with exponential backoff"""
        service = self.services[service_name]
        max_retries = max_retries or (service.timeout // 2)
        endpoint = service.health_endpoint
        
        if not endpoint:
            logger.info(f"⏩ No health endpoint for {service_name}, assuming ready")
            return True
        
        logger.info(f"⏳ Waiting for {service_name} health check...")
        
        for attempt in range(max_retries):
            try:
                # Exponential backoff: 1, 2, 4, 8, 16, 30, 30, 30...
                delay = min(2 ** attempt, 30)
                
                response = requests.get(endpoint, timeout=10)
                status_code = response.status_code
                
                if status_code < 500:
                    logger.info(f"[OK] {service_name} is healthy! (Status: {status_code})")
                    
                    # Log performance metrics
                    perf_logger.info(f"{service_name} health check succeeded in {attempt + 1} attempts")
                    
                    # Update service status
                    self.service_status[service_name] = ServiceStatus.RUNNING
                    self.log_service_event(service_name, "healthy", f"Status: {status_code}")
                    
                    return True
                else:
                    logger.warning(f"   {service_name} returned status {status_code}")
                    
            except (requests.exceptions.ConnectionError, ConnectionError):
                logger.debug(f"   {service_name} connection refused (attempt {attempt + 1})")
            except requests.exceptions.Timeout:
                logger.warning(f"   {service_name} health check timeout")
            except requests.exceptions.RequestException as e:
                logger.warning(f"   {service_name} health check failed: {e}")
            except Exception as e:
                logger.error(f"   Unexpected error checking {service_name}: {e}")
            
            if attempt % 5 == 4:  # Log progress every 5 attempts
                logger.info(f"   Still waiting for {service_name}... ({attempt + 1}/{max_retries})")
            
            time.sleep(delay)
        
        logger.error(f"[FAIL] {service_name} health check failed after {max_retries} attempts")
        self.service_status[service_name] = ServiceStatus.FAILED
        self.log_service_event(service_name, "health_check_failed")
        return False

    def start_comfyui(self) -> Optional[subprocess.Popen]:
        """Start ComfyUI with enterprise error handling and monitoring"""
        logger.info("[ART] Starting ComfyUI server...")
        
        if not self.check_port_available(8188):
            logger.warning("[WARN] Port 8188 already in use")
            # Try to detect if it's actually ComfyUI running
            try:
                response = requests.get("http://localhost:8188", timeout=5)
                if response.status_code < 500:
                    logger.info("[OK] ComfyUI appears to be already running")
                    return None
            except Exception:
                logger.error("[FAIL] Port 8188 occupied by unknown service")
                return None
        
        self.service_status['comfyui'] = ServiceStatus.STARTING
        
        # Use service detector for intelligent ComfyUI startup
        try:
            from duckbot.service_detector import ServiceDetector
            detector = ServiceDetector()
            
            # Check if already running
            status = detector.detect_service_status('comfyui')
            if status['status'] in ['running_healthy', 'running_unhealthy']:
                logger.info("[OK] ComfyUI already running - connecting to existing instance")
                self.service_status['comfyui'] = ServiceStatus.RUNNING
                return None  # Not our process, but it's running
            
            # Try to start local ComfyUI
            logger.info("[LAUNCH] Starting local ComfyUI installation...")
            success, message = detector.start_local_comfyui()
            if success:
                logger.info(f"[OK] {message}")
                self.service_status['comfyui'] = ServiceStatus.RUNNING
                return None  # Process started but not managed by us directly
            else:
                logger.error(f"[FAIL] Failed to start local ComfyUI: {message}")
                
        except Exception as e:
            logger.error(f"[FAIL] Service detector failed: {e}")
            
        # Fallback: Try local ComfyUI installations directly
        local_comfyui_paths = [
            self.base_dir / "ComfyUI" / "main.py",
            self.base_dir / "ComfyUI_windows_portable_nvidia" / "ComfyUI" / "main.py",
            self.base_dir / "ComfyUI_windows_portable" / "ComfyUI" / "main.py"
        ]
        
        for comfyui_path in local_comfyui_paths:
            if comfyui_path.exists():
                try:
                    logger.info(f"[LAUNCH] Starting ComfyUI from: {comfyui_path}")
                    process = subprocess.Popen(
                        [sys.executable, str(comfyui_path), "--listen", "127.0.0.1", "--port", "8188", "--enable-cors-header"],
                        cwd=str(comfyui_path.parent),
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        creationflags=subprocess.CREATE_NEW_CONSOLE if sys.platform == "win32" else 0,
                        text=True
                    )
                    logger.info(f"[OK] ComfyUI started from {comfyui_path} (PID: {process.pid})")
                    return process
                except Exception as e:
                    logger.error(f"[FAIL] Failed to start ComfyUI from {comfyui_path}: {e}")
                    continue
        
        # Try local batch file
        batch_file = self.base_dir / "launch_ultra_lowvram.bat"
        if batch_file.exists() and sys.platform == "win32":
            try:
                logger.info("[LAUNCH] Starting ComfyUI via local batch file...")
                process = subprocess.Popen(
                    [str(batch_file)],
                    cwd=str(self.base_dir),
                    shell=True,
                    creationflags=subprocess.CREATE_NEW_CONSOLE
                )
                
                logger.info(f"[OK] ComfyUI started via local batch file (PID: {process.pid})")
                return process
                
            except Exception as e:
                logger.error(f"[FAIL] Failed to start ComfyUI via local batch: {e}")
        
        # Fallback to Python execution in common directories
        comfyui_dirs = [
            Path("C:/Users/Duck1/Desktop/DiscordBotAI/ComfyUI_windows_portable_nvidia/ComfyUI_windows_portable"),
            self.base_dir / "ComfyUI",
            self.base_dir / "comfyui", 
            self.base_dir.parent / "ComfyUI",
            Path.home() / "ComfyUI"
        ]
        
        for comfyui_dir in comfyui_dirs:
            main_script = comfyui_dir / "main.py"
            if main_script.exists():
                try:
                    logger.info(f"[LAUNCH] Starting ComfyUI from {comfyui_dir}...")
                    
                    # Enhanced startup arguments - default to localhost for security
                    listen_host = os.getenv("COMFYUI_HOST", "127.0.0.1")  # Default to localhost
                    args = [
                        sys.executable, str(main_script),
                        "--listen", listen_host,
                        "--port", "8188",
                        "--verbose"
                    ]
                    
                    # Security warning if binding to all interfaces
                    if listen_host == "0.0.0.0":
                        security_logger.warning("ComfyUI configured to listen on all interfaces - network accessible")
                    
                    # Add GPU optimization if available
                    if torch_available := self.check_torch_cuda():
                        args.extend(["--gpu-only", "--normalvram"])
                        logger.info("[EMOJI] GPU acceleration enabled")
                    
                    process = subprocess.Popen(
                        args,
                        cwd=str(comfyui_dir),
                        creationflags=subprocess.CREATE_NEW_CONSOLE if sys.platform == "win32" else 0
                    )
                    
                    logger.info(f"[OK] ComfyUI started from {comfyui_dir} (PID: {process.pid})")
                    return process
                    
                except Exception as e:
                    logger.error(f"[FAIL] Failed to start ComfyUI from {comfyui_dir}: {e}")
                    continue
        
        logger.error("[FAIL] Could not find or start ComfyUI")
        self.service_status['comfyui'] = ServiceStatus.FAILED
        return None

    def check_torch_cuda(self) -> bool:
        """Check if PyTorch CUDA is available"""
        try:
            import torch
            return torch.cuda.is_available()
        except ImportError:
            return False

    def start_n8n(self) -> Optional[subprocess.Popen]:
        """Start n8n with enterprise configuration - Desktop terminal method"""
        logger.info("[EMOJI] Starting n8n workflow automation...")
        
        if not self.check_port_available(5678):
            logger.warning("[WARN] Port 5678 already in use")
            return None
        
        self.service_status['n8n'] = ServiceStatus.STARTING
        
        try:
            # Method 1: Try direct n8n command (as user typically does)
            try:
                # First check if n8n is actually available - try multiple paths on Windows
                n8n_paths = [
                    'n8n',  # Try PATH first
                    r'C:\Users\Duck1\AppData\Roaming\npm\n8n.cmd',  # Windows npm global
                    os.path.expanduser('~/AppData/Roaming/npm/n8n.cmd')  # User npm global
                ]
                
                n8n_cmd = None
                for cmd in n8n_paths:
                    try:
                        subprocess.run([cmd, '--version'], capture_output=True, check=True, timeout=10)
                        logger.info(f"[OK] n8n found at: {cmd}")
                        n8n_cmd = cmd
                        break
                    except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
                        continue
                
                if not n8n_cmd:
                    logger.warning("[WARN] n8n command not found in any standard location")
                    raise Exception("n8n not available")
                
                logger.info("[EMOJI] Starting n8n via desktop terminal method...")
                
                # Enhanced n8n configuration
                env = os.environ.copy()
                env.update({
                    'N8N_PORT': '5678',
                    'N8N_HOST': 'localhost',
                    'N8N_PROTOCOL': 'http',
                    'N8N_LOG_LEVEL': 'info',
                    'N8N_BASIC_AUTH_ACTIVE': 'false',
                    'WEBHOOK_URL': 'http://localhost:5678/'
                })
                
                # Use cmd to start n8n in new window (similar to opening terminal on desktop)
                if sys.platform == "win32":
                    # Start n8n in new command window like opening terminal on desktop
                    cmd_args = ['cmd', '/c', 'start', 'cmd', '/k', n8n_cmd]
                    
                    # Add tunnel only if requested
                    tunnel_enabled = os.getenv('N8N_TUNNEL', 'false').lower() == 'true'
                    if tunnel_enabled:
                        cmd_args[-1] += ' --tunnel'
                        logger.info("[GLOBE] n8n tunnel enabled")
                    
                    process = subprocess.Popen(
                        cmd_args,
                        env=env,
                        cwd=str(Path.home() / "Desktop"),  # Start from Desktop like user does
                        shell=True
                    )
                    
                    logger.info(f"[OK] n8n started via desktop terminal method (PID: {process.pid})")
                    return process
                else:
                    # Unix-like systems
                    args = [n8n_cmd]
                    tunnel_enabled = os.getenv('N8N_TUNNEL', 'false').lower() == 'true'
                    if tunnel_enabled:
                        args.append('--tunnel')
                        logger.info("[GLOBE] n8n tunnel enabled")
                    
                    process = subprocess.Popen(
                        args,
                        env=env,
                        cwd=str(Path.home() / "Desktop")
                    )
                    
                    logger.info(f"[OK] n8n started (PID: {process.pid})")
                    return process
                    
            except Exception as e:
                logger.warning(f"[WARN] Desktop terminal method failed: {e}")
        
            # Method 2: Fallback to finding n8n executable path
            logger.info("[EMOJI] Falling back to executable path method...")
            n8n_executable = os.getenv('N8N_PATH') or self.get_npm_executable_path('n8n')
            
            if not n8n_executable:
                logger.error("[FAIL] n8n executable not found in PATH or npm globals")
                self.service_status['n8n'] = ServiceStatus.FAILED
                return None

            # Enhanced n8n configuration
            env = os.environ.copy()
            env.update({
                'N8N_PORT': '5678',
                'N8N_HOST': 'localhost',
                'N8N_PROTOCOL': 'http',
                'N8N_LOG_LEVEL': 'info',
                'N8N_BASIC_AUTH_ACTIVE': 'false',
                'WEBHOOK_URL': 'http://localhost:5678/'
            })
            
            args = [n8n_executable]
            
            # Add tunnel only if requested
            tunnel_enabled = os.getenv('N8N_TUNNEL', 'false').lower() == 'true'
            if tunnel_enabled:
                args.append('--tunnel')
                logger.info("[GLOBE] n8n tunnel enabled")
            
            process = subprocess.Popen(
                args,
                env=env,
                creationflags=subprocess.CREATE_NEW_CONSOLE if sys.platform == "win32" else 0
            )
            
            logger.info(f"[OK] n8n started via executable path (PID: {process.pid})")
            return process
            
        except Exception as e:
            logger.error(f"[FAIL] Failed to start n8n: {e}")
            self.service_status['n8n'] = ServiceStatus.FAILED
            return None

    def start_open_webui(self) -> Optional[subprocess.Popen]:
        """Start Open WebUI with enterprise configuration"""
        logger.info("[GLOBE] Starting Open WebUI...")

        if not self.check_port_available(8080):
            logger.warning("[WARN] Port 8080 already in use")
            return None

        self.service_status['open-webui'] = ServiceStatus.STARTING

        try:
            # Check if open-webui is installed
            try:
                subprocess.run(['open-webui', '--version'], capture_output=True, check=True)
            except (subprocess.CalledProcessError, FileNotFoundError):
                logger.info("[PACKAGE] open-webui not found, installing...")
                self.install_python_package('open-webui')

            listen_host = os.getenv("OPENWEBUI_HOST", "0.0.0.0")
            args = ['open-webui', 'serve', '--host', listen_host, '--port', '8080']

            if listen_host == "0.0.0.0":
                security_logger.warning("Open WebUI configured to listen on all interfaces - network accessible")

            process = subprocess.Popen(
                args,
                creationflags=subprocess.CREATE_NEW_CONSOLE if sys.platform == "win32" else 0
            )

            logger.info(f"[OK] Open WebUI started successfully (PID: {process.pid})")
            return process

        except Exception as e:
            logger.error(f"[FAIL] Failed to start Open WebUI: {e}")
            self.service_status['open-webui'] = ServiceStatus.FAILED
            return None

    def start_open_notebook(self) -> Optional[subprocess.Popen]:
        """Start open-notebook with enterprise Docker support"""
        logger.info("[EMOJI] Starting Open Notebook...")
        
        if not self.check_port_available(8502):
            logger.warning("[WARN] Port 8502 already in use")
            return None
        
        self.service_status['open_notebook'] = ServiceStatus.STARTING
        
        open_notebook_dir = self.base_dir / "open-notebook"
        if not open_notebook_dir.exists():
            logger.error("[FAIL] open-notebook directory not found")
            self.service_status['open_notebook'] = ServiceStatus.FAILED
            return None

        # Try Docker first (preferred method)
        if self.try_docker_start(open_notebook_dir):
            return self.processes.get('open_notebook')
        
        # Fallback to Python execution
        return self.start_open_notebook_python(open_notebook_dir)

    def try_docker_start(self, open_notebook_dir: Path) -> bool:
        """Try to start open-notebook with Docker"""
        try:
            # Check Docker availability
            subprocess.run(['docker', '--version'], capture_output=True, check=True)
            
            # Check for docker-compose file
            compose_file = open_notebook_dir / "docker-compose.yml"
            if not compose_file.exists():
                compose_file = open_notebook_dir / "docker-compose.yaml"
            
            if compose_file.exists():
                logger.info("[EMOJI] Starting open-notebook via Docker Compose...")
                process = subprocess.Popen(
                    ['docker-compose', 'up', '-d'],
                    cwd=str(open_notebook_dir),
                    creationflags=subprocess.CREATE_NEW_CONSOLE if sys.platform == "win32" else 0
                )
                
                self.processes['open_notebook'] = process
                logger.info("[OK] Open Notebook started via Docker Compose")
                return True
            else:
                # Try direct Docker run
                logger.info("[EMOJI] Starting open-notebook via Docker run...")
                docker_cmd = [
                    'docker', 'run', '-d',
                    '--name', 'open-notebook-instance',
                    '-p', '8502:8502',
                    '-p', '5055:5055',
                    '--env-file', str(open_notebook_dir / '.env'),
                    'lfnovo/open_notebook:latest'
                ]
                
                process = subprocess.Popen(docker_cmd)
                self.processes['open_notebook'] = process
                logger.info("[OK] Open Notebook started via Docker")
                return True
                
        except (subprocess.CalledProcessError, FileNotFoundError):
            logger.info("[EMOJI] Docker not available, trying Python fallback...")
            return False
        except Exception as e:
            logger.error(f"[FAIL] Docker start failed: {e}")
            return False

    def start_open_notebook_python(self, open_notebook_dir: Path) -> Optional[subprocess.Popen]:
        """Start open-notebook with Python fallback"""
        logger.info("[EMOJI] Starting open-notebook via Python...")
        
        # Open Notebook uses app_home.py as main entry point
        startup_files = [
            "app_home.py", "main.py", "app.py", "server.py", "run.py", 
            "manage.py", "start.py", "streamlit_app.py"
        ]
        
        for startup_file in startup_files:
            startup_path = open_notebook_dir / startup_file
            if startup_path.exists():
                try:
                    logger.info(f"[LAUNCH] Executing {startup_file}...")
                    
                    # Check if it's a Streamlit app (Open Notebook uses Streamlit)
                    if (startup_file == "streamlit_app.py" or startup_file == "app_home.py" or 
                        "streamlit" in startup_path.read_text(encoding='utf-8', errors='ignore')):
                        args = [sys.executable, '-m', 'streamlit', 'run', str(startup_path), '--server.port', '8502', '--server.headless', 'true']
                    else:
                        args = [sys.executable, str(startup_path)]
                    
                    process = subprocess.Popen(
                        args,
                        cwd=str(open_notebook_dir),
                        creationflags=subprocess.CREATE_NEW_CONSOLE if sys.platform == "win32" else 0
                    )
                    
                    logger.info(f"[OK] Open Notebook started with {startup_file} (PID: {process.pid})")
                    return process
                    
                except Exception as e:
                    logger.error(f"[FAIL] Failed to start with {startup_file}: {e}")
                    continue
        
        logger.error("[FAIL] Could not start open-notebook with any method")
        self.service_status['open_notebook'] = ServiceStatus.FAILED
        return None

    def start_lm_studio(self) -> Optional[subprocess.Popen]:
        """Start LM Studio with local AI model server"""
        logger.info("[AI] Starting LM Studio AI server...")
        
        if not self.check_port_available(1234):
            logger.warning("[WARN] Port 1234 already in use")
            return None
        
        self.service_status['lm_studio'] = ServiceStatus.STARTING
        
        # LM Studio installation paths
        lm_studio_paths = [
            r"C:\Program Files\LM Studio\LM Studio.exe",
            os.path.expanduser(r"~\AppData\Local\Programs\LM Studio\LM Studio.exe"),
            r"C:\Users\Duck1\AppData\Local\Programs\LM Studio\LM Studio.exe"
        ]
        
        lm_studio_path = None
        for path in lm_studio_paths:
            if os.path.exists(path):
                lm_studio_path = path
                break
        
        if not lm_studio_path:
            logger.warning("[WARN] LM Studio executable not found in standard locations")
            self.service_status['lm_studio'] = ServiceStatus.FAILED
            return None
        
        try:
            logger.info(f"[LAUNCH] Starting LM Studio from: {lm_studio_path}")
            
            # Start LM Studio with server mode (headless)
            args = [lm_studio_path, "--server", "--port", "1234"]
            
            process = subprocess.Popen(
                args,
                creationflags=subprocess.CREATE_NEW_CONSOLE if sys.platform == "win32" else 0
            )
            
            logger.info(f"[OK] LM Studio started successfully (PID: {process.pid})")
            return process
            
        except Exception as e:
            logger.error(f"[FAIL] Failed to start LM Studio: {e}")
            self.service_status['lm_studio'] = ServiceStatus.FAILED
            return None

    def start_jupyter(self) -> Optional[subprocess.Popen]:
        """Start Jupyter with enterprise configuration"""
        logger.info("[CHART] Starting Jupyter Notebook server...")
        
        # Check if jupyter is installed
        try:
            subprocess.run(['jupyter', '--version'], capture_output=True, check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            logger.warning("[WARN] Jupyter not installed, skipping")
            return None
        
        if not self.check_port_available(8889):
            logger.warning("[WARN] Port 8889 already in use")
            return None
        
        self.service_status['jupyter'] = ServiceStatus.STARTING
        
        # Setup notebooks directory
        notebooks_dir = self.base_dir / "notebooks"
        notebooks_dir.mkdir(exist_ok=True)
        
        # Create sample notebooks if they don't exist
        self.create_sample_notebooks(notebooks_dir)
        
        try:
            # Enhanced Jupyter configuration
            args = [
                'jupyter', 'notebook',
                f'--port=8889',
                '--no-browser',
                '--allow-root',
                f'--notebook-dir={notebooks_dir}',
                '--ip=localhost',
                '--NotebookApp.token=""',
                '--NotebookApp.password=""',
                '--NotebookApp.open_browser=False'
            ]
            
            process = subprocess.Popen(
                args,
                creationflags=subprocess.CREATE_NEW_CONSOLE if sys.platform == "win32" else 0
            )
            
            logger.info(f"[OK] Jupyter started successfully (PID: {process.pid})")
            return process
            
        except Exception as e:
            logger.error(f"[FAIL] Failed to start Jupyter: {e}")
            self.service_status['jupyter'] = ServiceStatus.FAILED
            return None

    def create_sample_notebooks(self, notebooks_dir: Path):
        """Create sample Jupyter notebooks"""
        try:
            sample_notebooks = {
                "DuckBot_Integration.ipynb": {
                    "cells": [
                        {
                            "cell_type": "markdown",
                            "source": ["# DuckBot Integration Notebook\n", "\n", "This notebook demonstrates how to interact with DuckBot data and services."]
                        },
                        {
                            "cell_type": "code",
                            "source": ["import requests\nimport json\nfrom datetime import datetime\n\n# Example: Check ComfyUI status\nresponse = requests.get('http://localhost:8188', timeout=10)\nprint(f'ComfyUI Status: {response.status_code}')"]
                        }
                    ],
                    "metadata": {"kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"}},
                    "nbformat": 4,
                    "nbformat_minor": 4
                }
            }
            
            for notebook_name, content in sample_notebooks.items():
                notebook_path = notebooks_dir / notebook_name
                if not notebook_path.exists():
                    with open(notebook_path, 'w') as f:
                        json.dump(content, f, indent=2)
                    logger.debug(f"Created sample notebook: {notebook_name}")
                    
        except Exception as e:
            logger.warning(f"Failed to create sample notebooks: {e}")

    def start_qwen3_omni_ui(self) -> Optional[subprocess.Popen]:
        """Start Qwen3-Omni-UI with enterprise configuration"""
        logger.info("[TARGET] Starting Qwen3-Omni-UI...")

        if not self.check_port_available(8788):
            logger.warning("[WARN] Port 8788 already in use")
            return None

        self.service_status['qwen3_omni_ui'] = ServiceStatus.STARTING

        try:
            # Check if Node.js is available
            try:
                subprocess.run(['node', '--version'], capture_output=True, check=True)
            except (subprocess.CalledProcessError, FileNotFoundError):
                logger.error("[FAIL] Node.js not found. Please install Node.js 16+")
                self.service_status['qwen3_omni_ui'] = ServiceStatus.FAILED
                return None

            # Check if desktop-ui directory exists
            desktop_ui_dir = self.base_dir / "desktop-ui"
            if not desktop_ui_dir.exists():
                logger.error("[FAIL] desktop-ui directory not found")
                self.service_status['qwen3_omni_ui'] = ServiceStatus.FAILED
                return None

            # Change to desktop-ui directory
            os.chdir(str(desktop_ui_dir))

            # Check if node_modules exists
            if not (desktop_ui_dir / "node_modules").exists():
                logger.info("[INFO] Installing desktop-ui dependencies...")
                try:
                    subprocess.run(['npm', 'install'], cwd=str(desktop_ui_dir),
                                 capture_output=True, text=True, check=True)
                except subprocess.CalledProcessError as e:
                    logger.error(f"[FAIL] Failed to install dependencies: {e}")
                    self.service_status['qwen3_omni_ui'] = ServiceStatus.FAILED
                    return None

            # Start the Electron app
            logger.info("[LAUNCH] Starting Qwen3-Omni-UI Electron app...")

            # Set environment variables for the UI
            env = os.environ.copy()
            env.update({
                'QWEN3_OMNI_UI_PORT': '8788',
                'QWEN3_OMNI_WS_PORT': '8796',
                'QWEN3_OMNI_WS_PATH': '/ws',
                'NODE_ENV': 'production'
            })

            # Try different startup methods
            startup_methods = [
                # Method 1: npm run
                ['npm', 'run', 'electron:serve'],
                # Method 2: npm start
                ['npm', 'start'],
                # Method 3: Direct electron
                ['npx', 'electron', '.']
            ]

            for method in startup_methods:
                try:
                    process = subprocess.Popen(
                        method,
                        cwd=str(desktop_ui_dir),
                        env=env,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True
                    )

                    logger.info(f"[OK] Qwen3-Omni-UI started with method: {' '.join(method)} (PID: {process.pid})")
                    return process

                except FileNotFoundError:
                    logger.warning(f"[WARN] Method not available: {' '.join(method)}")
                    continue
                except Exception as e:
                    logger.warning(f"[WARN] Method failed: {' '.join(method)} - {e}")
                    continue

            logger.error("[FAIL] Could not start Qwen3-Omni-UI with any method")
            self.service_status['qwen3_omni_ui'] = ServiceStatus.FAILED
            return None

        except Exception as e:
            logger.error(f"[FAIL] Failed to start Qwen3-Omni-UI: {e}")
            self.service_status['qwen3_omni_ui'] = ServiceStatus.FAILED
            return None

    def start_duckbot(self) -> Optional[subprocess.Popen]:
        """Start DuckBot with dependency checking"""
        logger.info("[EMOJI] Starting DuckBot Discord bot...")
        
        # Check dependencies first
        if 'comfyui' in self.services['duckbot'].dependencies:
            if not self.service_status.get('comfyui') == ServiceStatus.RUNNING:
                logger.warning("[WARN] ComfyUI dependency not running, DuckBot may have limited functionality")
        
        self.service_status['duckbot'] = ServiceStatus.STARTING
        
        # Find DuckBot script
        possible_scripts = [
            "DuckBot-v2.3.0-Trading-Video-Enhanced.py",
            "DuckBot.py", 
            "main.py",
            "bot.py"
        ]
        
        main_script = None
        for script_name in possible_scripts:
            script_path = self.base_dir / script_name
            if script_path.exists():
                main_script = script_path
                break
        
        if not main_script:
            logger.error("[FAIL] DuckBot script not found")
            self.service_status['duckbot'] = ServiceStatus.FAILED
            return None

        try:
            # Load environment for DuckBot
            load_dotenv()
            
            # Verify Discord token
            if not os.getenv('DISCORD_TOKEN'):
                logger.error("[FAIL] DISCORD_TOKEN not found in environment")
                self.service_status['duckbot'] = ServiceStatus.FAILED
                return None
            
            process = subprocess.Popen([
                sys.executable, str(main_script)
            ], cwd=str(self.base_dir))
            
            logger.info(f"[OK] DuckBot started successfully (PID: {process.pid})")
            return process
            
        except Exception as e:
            logger.error(f"[FAIL] Failed to start DuckBot: {e}")
            self.service_status['duckbot'] = ServiceStatus.FAILED
            return None

    def setup_signal_handlers(self):
        """Setup enterprise signal handling"""
        def signal_handler(sig, frame):
            signal_name = signal.Signals(sig).name
            logger.info(f"\n[STOP] Received {signal_name} signal, initiating graceful shutdown...")
            security_logger.warning(f"Shutdown signal received: {signal_name}")
            
            self.shutdown_requested = True
            self.shutdown_all()
            
            logger.info("[OK] Ecosystem shutdown completed")
            sys.exit(0)
        
        # Handle multiple signals
        for sig in [signal.SIGINT, signal.SIGTERM]:
            signal.signal(sig, signal_handler)
        
        # Windows-specific
        if sys.platform == "win32":
            signal.signal(signal.SIGBREAK, signal_handler)

    def shutdown_all(self):
        """Enterprise graceful shutdown with proper cleanup"""
        logger.info("[STOP] Initiating graceful shutdown of all services...")
        
        shutdown_start = time.time()
        
        # Shutdown services in reverse order of dependencies
        shutdown_order = ['duckbot', 'open_notebook', 'jupyter', 'n8n', 'comfyui', 'open-webui']
        
        for service_name in shutdown_order:
            if service_name not in self.processes:
                continue
                
            process = self.processes[service_name]
            if process and process.poll() is None:
                logger.info(f"   Stopping {service_name} (PID: {process.pid})...")
                
                try:
                    # Send graceful termination signal
                    if sys.platform == "win32":
                        # Use taskkill for better process tree handling on Windows
                        subprocess.run([
                            'taskkill', '/PID', str(process.pid), '/T', '/F'
                        ], capture_output=True, timeout=30)
                    else:
                        # Use process group termination on Unix-like systems
                        os.killpg(os.getpgid(process.pid), signal.SIGTERM)
                    
                    # Wait for graceful shutdown
                    try:
                        process.wait(timeout=15)
                        logger.info(f"   [OK] {service_name} stopped gracefully")
                    except subprocess.TimeoutExpired:
                        logger.warning(f"   ⏰ {service_name} shutdown timeout, forcing...")
                        process.kill()
                        process.wait(timeout=5)
                        logger.info(f"   [EMOJI] {service_name} force stopped")
                    
                    # Log shutdown event
                    self.log_service_event(service_name, "stopped", "Graceful shutdown")
                    self.service_status[service_name] = ServiceStatus.STOPPED
                    
                except subprocess.TimeoutExpired:
                    logger.error(f"   [FAIL] Failed to stop {service_name}, process may be stuck")
                except ProcessLookupError:
                    logger.info(f"   [OK] {service_name} already stopped")
                except Exception as e:
                    logger.error(f"   [FAIL] Error stopping {service_name}: {e}")
        
        # Clean up Docker containers if any
        self.cleanup_docker_containers()
        
        shutdown_time = time.time() - shutdown_start
        perf_logger.info(f"Shutdown completed in {shutdown_time:.2f}s")
        security_logger.info("Ecosystem shutdown completed successfully")

    def cleanup_docker_containers(self):
        """Clean up any Docker containers we started"""
        try:
            # Check for our specific containers
            container_names = ['open-notebook-instance']
            
            for container_name in container_names:
                try:
                    # Stop container
                    subprocess.run(['docker', 'stop', container_name], 
                                 capture_output=True, timeout=30)
                    # Remove container
                    subprocess.run(['docker', 'rm', container_name], 
                                 capture_output=True, timeout=10)
                    logger.debug(f"Cleaned up Docker container: {container_name}")
                except subprocess.TimeoutExpired:
                    logger.warning(f"Timeout cleaning up container: {container_name}")
                except subprocess.CalledProcessError:
                    pass  # Container might not exist
                    
        except Exception as e:
            logger.debug(f"Docker cleanup error (non-critical): {e}")

    def monitor_services(self):
        """Enterprise service monitoring with auto-restart capability"""
        logger.info("[EMOJI] Starting service monitoring...")
        
        monitor_interval = self.monitoring_config.get('health_check_interval', 30)
        performance_interval = self.monitoring_config.get('performance_log_interval', 60)
        last_performance_log = time.time()
        
        while not self.shutdown_requested:
            try:
                current_time = time.time()
                
                # Monitor each service
                for service_name, process in list(self.processes.items()):
                    if process is None:
                        continue
                        
                    # Check if process is still alive
                    return_code = process.poll()
                    
                    if return_code is not None:
                        # Process has died
                        logger.error(f"[EMOJI] {service_name} process died (exit code: {return_code})")
                        self.service_status[service_name] = ServiceStatus.FAILED
                        self.log_service_event(service_name, "process_died", f"Exit code: {return_code}")
                        
                        # Attempt restart if configured
                        if self.should_restart_service(service_name):
                            self.restart_service(service_name)
                    
                    else:
                        # Process is alive, check health if possible
                        service_config = self.services.get(service_name)
                        if service_config and service_config.health_endpoint:
                            try:
                                response = requests.get(service_config.health_endpoint, timeout=5)
                                if response.status_code >= 500:
                                    logger.warning(f"[WARN] {service_name} health check failed: {response.status_code}")
                                    # Could implement health-based restart logic here
                            except requests.RequestException:
                                # Health check failed, but process is alive - might be starting up
                                pass
                
                # Log performance metrics periodically
                if current_time - last_performance_log >= performance_interval:
                    self.log_performance_metrics()
                    last_performance_log = current_time
                
                time.sleep(monitor_interval)
                
            except Exception as e:
                logger.error(f"Error in service monitoring: {e}")
                time.sleep(30)  # Back off on error

    def should_restart_service(self, service_name: str) -> bool:
        """Determine if a service should be restarted based on policy"""
        service_config = self.services.get(service_name)
        if not service_config:
            return False
        
        # Check restart attempts
        current_attempts = self.restart_counts.get(service_name, 0)
        if current_attempts >= service_config.restart_attempts:
            logger.warning(f"[NO] {service_name} exceeded max restart attempts ({service_config.restart_attempts})")
            return False
        
        # Check cooldown period
        last_restart = self.last_restart.get(service_name)
        if last_restart:
            cooldown = self.monitoring_config.get('restart_cooldown', 300)  # 5 minutes
            time_since_restart = (datetime.now() - last_restart).total_seconds()
            if time_since_restart < cooldown:
                logger.info(f"⏰ {service_name} still in restart cooldown ({cooldown - time_since_restart:.0f}s remaining)")
                return False
        
        return True

    def restart_service(self, service_name: str):
        """Restart a failed service"""
        logger.info(f"[EMOJI] Attempting to restart {service_name}...")
        
        # Update counters
        self.restart_counts[service_name] = self.restart_counts.get(service_name, 0) + 1
        self.last_restart[service_name] = datetime.now()
        
        # Remove from processes dict
        if service_name in self.processes:
            del self.processes[service_name]
        
        self.service_status[service_name] = ServiceStatus.RESTARTING
        self.log_service_event(service_name, "restarting", f"Attempt {self.restart_counts[service_name]}")
        
        # Wait for restart delay
        service_config = self.services.get(service_name)
        if service_config:
            time.sleep(service_config.restart_delay)
        
        # Start the service
        start_methods = {
            'comfyui': self.start_comfyui,
            'n8n': self.start_n8n,
            'open_notebook': self.start_open_notebook,
            'jupyter': self.start_jupyter,
            'lm_studio': self.start_lm_studio,
            'open-webui': self.start_open_webui,
            'qwen3_omni_ui': self.start_qwen3_omni_ui,
            'duckbot': self.start_duckbot
        }
        
        start_method = start_methods.get(service_name)
        if start_method:
            try:
                process = start_method()
                if process:
                    self.processes[service_name] = process
                    logger.info(f"[OK] {service_name} restarted successfully (PID: {process.pid})")
                    
                    # Wait for health check
                    if service_config.health_endpoint:
                        threading.Thread(
                            target=self.wait_for_service,
                            args=(service_name,),
                            daemon=True
                        ).start()
                else:
                    logger.error(f"[FAIL] Failed to restart {service_name}")
                    self.service_status[service_name] = ServiceStatus.FAILED
                    
            except Exception as e:
                logger.error(f"[FAIL] Error restarting {service_name}: {e}")
                self.service_status[service_name] = ServiceStatus.FAILED

    def log_performance_metrics(self):
        """Log system and service performance metrics"""
        try:
            # System metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            perf_logger.info(f"System - CPU: {cpu_percent}%, Memory: {memory.percent}%, Disk: {disk.percent}%")
            
            # Log to database
            with sqlite3.connect(self.db_path) as conn:
                timestamp = datetime.now()
                metrics = [
                    ('system', 'cpu_percent', cpu_percent, timestamp),
                    ('system', 'memory_percent', memory.percent, timestamp),
                    ('system', 'disk_percent', disk.percent, timestamp)
                ]
                
                conn.executemany(
                    "INSERT INTO performance_metrics (service_name, metric_name, metric_value, timestamp) VALUES (?, ?, ?, ?)",
                    metrics
                )
                conn.commit()
            
            # Service-specific metrics
            for service_name, process in self.processes.items():
                if process and process.poll() is None:
                    try:
                        p = psutil.Process(process.pid)
                        cpu_percent = p.cpu_percent()
                        memory_mb = p.memory_info().rss / 1024 / 1024
                        
                        perf_logger.info(f"{service_name} - CPU: {cpu_percent}%, Memory: {memory_mb:.1f}MB")
                        
                        with sqlite3.connect(self.db_path) as conn:
                            metrics = [
                                (service_name, 'cpu_percent', cpu_percent, timestamp),
                                (service_name, 'memory_mb', memory_mb, timestamp)
                            ]
                            conn.executemany(
                                "INSERT INTO performance_metrics (service_name, metric_name, metric_value, timestamp) VALUES (?, ?, ?, ?)",
                                metrics
                            )
                            conn.commit()
                            
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        pass
                        
        except Exception as e:
            logger.error(f"Error logging performance metrics: {e}")

    def print_enterprise_status(self):
        """Print comprehensive enterprise status dashboard"""
        print("\n" + "="*80)
        print("[EMOJI] DUCKBOT ENTERPRISE ECOSYSTEM STATUS")
        print("="*80)
        
        # System information
        uptime = datetime.now() - self.start_time
        print(f"[EMOJI] Uptime: {str(uptime).split('.')[0]}")
        print(f"[CHART] System Load: CPU {psutil.cpu_percent()}% | RAM {psutil.virtual_memory().percent}%")
        print("-"*80)
        
        services_info = [
            ("[ART] ComfyUI", "http://localhost:8188", "Image/Video Generation", 'comfyui'),
            ("[EMOJI] n8n", "http://localhost:5678", "Workflow Automation", 'n8n'),
            ("[EMOJI] Open Notebook", "http://localhost:8502", "AI Notebook Interface", 'open_notebook'),
            ("[GLOBE] Open WebUI", "http://localhost:8080", "Web-based Chat UI", 'open-webui'),
            ("[CHART] Jupyter", "http://localhost:8889", "Data Analysis", 'jupyter'),
            ("[TARGET] Qwen3-Omni-UI", "http://localhost:8788", "Advanced AI Interface", 'qwen3_omni_ui'),
            ("[EMOJI] DuckBot", "Discord", "Main Bot Interface", 'duckbot')
        ]
        
        running_services = []
        
        for name, url, desc, service_key in services_info:
            process = self.processes.get(service_key)
            status = self.service_status.get(service_key, ServiceStatus.STOPPED)
            
            # Status symbols and colors
            status_symbols = {
                ServiceStatus.RUNNING: "[OK] Running",
                ServiceStatus.STARTING: "[EMOJI] Starting", 
                ServiceStatus.RESTARTING: "[EMOJI] Restarting",
                ServiceStatus.FAILED: "[FAIL] Failed",
                ServiceStatus.STOPPED: "⚪ Stopped"
            }
            
            status_text = status_symbols.get(status, "[EMOJI] Unknown")
            
            # Add PID if running
            pid_info = ""
            if process and process.poll() is None:
                pid_info = f"(PID:{process.pid})"
            
            # Add restart count if any
            restart_info = ""
            restart_count = self.restart_counts.get(service_key, 0)
            if restart_count > 0:
                restart_info = f"[R:{restart_count}]"
            
            print(f"{name:<18} {status_text:<14} {pid_info:<12} {restart_info:<8} {url:<25} {desc}")
            
            if status == ServiceStatus.RUNNING and url != "Discord":
                running_services.append((name, url))
        
        print("-"*80)
        
        # Quick access links
        if running_services:
            print("[LAUNCH] Quick Access Links:")
            for name, url in running_services:
                print(f"   • {name}: {url}")
            print("-"*80)
        
        # Health status summary
        total_services = len(services_info)
        running_count = sum(1 for status in self.service_status.values() if status == ServiceStatus.RUNNING)
        
        health_percentage = (running_count / total_services) * 100 if total_services > 0 else 0
        health_status = "[EMOJI] Healthy" if health_percentage >= 80 else "[EMOJI] Degraded" if health_percentage >= 50 else "[EMOJI] Critical"
        
        print(f"[EMOJI] System Health: {health_status} ({running_count}/{total_services} services running - {health_percentage:.0f}%)")
        print(f"[FOLDER] Logs: {enterprise_logger.log_dir}")
        print(f"[SAVE] Database: {self.db_path}")
        print("-"*80)
        print("[EMOJI] Access your services at the URLs above")
        print("[STOP] Press Ctrl+C to shutdown all services")
        print("="*80 + "\n")

    def run(self):
        """Main enterprise execution method"""
        logger.info("[LAUNCH] Starting DuckBot Enterprise Ecosystem...")
        security_logger.info(f"Ecosystem startup initiated by user: {os.getenv('USERNAME', 'unknown')}")
        
        try:
            # Setup signal handlers
            self.setup_signal_handlers()
            
            # Comprehensive dependency check with error handling
            logger.info("[EMOJI] Performing enterprise dependency validation...")
            try:
                dependencies_ok = self.check_and_install_dependencies()
                if not dependencies_ok:
                    logger.warning("[WARN] Some dependencies had issues, but continuing...")
            except Exception as e:
                logger.error(f"[FAIL] Error during dependency check: {e}")
                logger.info("[EMOJI] Continuing with ecosystem startup despite dependency issues...")
                # Continue anyway - don't let dependency issues stop the whole system
            
            # Install open-notebook
            if not self.install_open_notebook():
                logger.warning("[WARN] open-notebook installation failed, service will be skipped")
            
            # Start services with proper dependency order
            startup_order = [
                ('comfyui', self.start_comfyui),
                ('lm_studio', self.start_lm_studio),
                ('jupyter', self.start_jupyter),
                ('n8n', self.start_n8n),
                ('open-webui', self.start_open_webui),
                ('open_notebook', self.start_open_notebook),
                ('duckbot', self.start_duckbot)
            ]
            
            logger.info("[EMOJI] Starting services in dependency order...")
            
            for service_name, start_func in startup_order:
                try:
                    logger.info(f"▶[EMOJI] Starting {service_name}...")
                    
                    process = start_func()
                    if process:
                        self.processes[service_name] = process
                        self.log_service_event(service_name, "started", f"PID: {process.pid}")
                        
                        # Wait for startup delay
                        service_config = self.services.get(service_name)
                        if service_config:
                            time.sleep(service_config.startup_delay)
                    else:
                        logger.warning(f"[WARN] {service_name} failed to start or is already running")
                        
                except Exception as e:
                    logger.error(f"[FAIL] Failed to start {service_name}: {e}")
                    self.log_service_event(service_name, "start_failed", str(e))
                    continue
            
            # Perform health checks
            logger.info("[EMOJI] Performing initial health checks...")
            health_check_services = ['comfyui', 'n8n', 'open_notebook', 'jupyter', 'open-webui']
            
            with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
                health_futures = {
                    executor.submit(self.wait_for_service, service): service 
                    for service in health_check_services 
                    if service in self.processes
                }
                
                for future in concurrent.futures.as_completed(health_futures):
                    service = health_futures[future]
                    try:
                        result = future.result()
                        if result:
                            logger.info(f"[OK] {service} health check passed")
                        else:
                            logger.warning(f"[WARN] {service} health check failed")
                    except Exception as e:
                        logger.error(f"[FAIL] Health check error for {service}: {e}")
            
            # Display status dashboard
            self.print_enterprise_status()
            
            # Start background monitoring
            logger.info("[EMOJI] Starting background service monitoring...")
            monitor_thread = threading.Thread(target=self.monitor_services, daemon=True)
            monitor_thread.start()
            
            # Log successful startup
            security_logger.info("Enterprise ecosystem startup completed successfully")
            
            # Main event loop
            logger.info("[OK] Enterprise ecosystem ready - entering main loop")
            try:
                while not self.shutdown_requested:
                    time.sleep(1)
            except KeyboardInterrupt:
                logger.info("Keyboard interrupt received")
            
            return True
            
        except Exception as e:
            logger.critical(f"[EMOJI] Critical error in enterprise ecosystem: {e}")
            security_logger.critical(f"Critical system failure: {e}")
            return False
        
        finally:
            if not self.shutdown_requested:
                self.shutdown_all()

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="DuckBot Enterprise Ecosystem Manager")
    parser.add_argument("--service", help="Start a specific service")
    args = parser.parse_args()

    try:
        manager = EcosystemManager()
        if args.service:
            if args.service in manager.services:
                logger.info(f"Starting single service: {args.service}")
                start_func = {
                    'comfyui': manager.start_comfyui,
                    'n8n': manager.start_n8n,
                    'open_notebook': manager.start_open_notebook,
                    'jupyter': manager.start_jupyter,
                    'lm_studio': manager.start_lm_studio,
                    'open-webui': manager.start_open_webui,
                    'duckbot': manager.start_duckbot
                }.get(args.service)

                if start_func:
                    process = start_func()
                    if process:
                        manager.processes[args.service] = process
                        manager.wait_for_service(args.service)
                        logger.info(f"{args.service} started. Press Ctrl+C to stop.")
                        while True:
                            time.sleep(1)
                    else:
                        logger.error(f"Failed to start service: {args.service}")
                        sys.exit(1)
                else:
                    logger.error(f"Unknown service: {args.service}")
                    sys.exit(1)
            else:
                logger.error(f"Unknown service: {args.service}")
                sys.exit(1)
        else:
            success = manager.run()
            sys.exit(0 if success else 1)
    except Exception as e:
        logger.critical(f"[EMOJI] Fatal error: {e}")
        sys.exit(1)
