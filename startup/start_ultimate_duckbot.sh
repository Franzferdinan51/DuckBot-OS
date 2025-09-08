#!/bin/bash

# =============================================================================
# DuckBot v3.1.0+ Ultimate Launcher (Linux/WSL)
# Enhanced with ByteBot, Archon, ChromiumOS, and Charm integrations
# Cross-platform startup script with intelligent system detection  
# =============================================================================

set -euo pipefail

# Color definitions
readonly COLOR_RESET='\033[0m'
readonly COLOR_CYAN='\033[96m'
readonly COLOR_GREEN='\033[92m'
readonly COLOR_YELLOW='\033[93m'
readonly COLOR_RED='\033[91m'
readonly COLOR_BLUE='\033[94m'
readonly COLOR_MAGENTA='\033[95m'
readonly COLOR_BOLD='\033[1m'

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Configuration
WSL_DETECTED=false
GPU_AVAILABLE=false
DOCKER_AVAILABLE=false
PYTHON_VERSION=""

# Functions
print_header() {
    clear
    echo -e "${COLOR_CYAN}${COLOR_BOLD}"
    echo "================================================================================"
    echo "    ____             __   ____        __     _    _ _ _   _                 _   "
    echo "   |    \ |   |  ___| |__| _   |  ___ | |_  | | | | | | |_| | |_ || |_| | ||| | "
    echo "   |  _  \| | | |/ __| '_ \|  _  | / _ \| __| | | | | | | __ || __| | _ | | _ | _ |"
    echo "   | |_) | |_| | (__| | | | |_) |  __/ |_   | | | | | | | | | |_| | | | | | | | |"
    echo "   |____/ \____|\___|_| |_|____/ \___|\__|  | |_| |_|_| |_| \__|_| |_| |_| |_| |_|"
    echo ""
    echo "                          v3.1.0+ Ultimate Edition"
    echo "          Enhanced with ByteBot + Archon + ChromiumOS + Charm Features"
    echo "================================================================================"
    echo -e "${COLOR_RESET}"
}

log_info() {
    echo -e "${COLOR_GREEN}[INFO]${COLOR_RESET} $1"
}

log_warning() {
    echo -e "${COLOR_YELLOW}[WARNING]${COLOR_RESET} $1"
}

log_error() {
    echo -e "${COLOR_RED}[ERROR]${COLOR_RESET} $1"
}

log_success() {
    echo -e "${COLOR_GREEN}[OK]${COLOR_RESET} $1"
}

check_system() {
    log_info "Detecting system configuration..."
    
    # Check if running in WSL
    if grep -qi microsoft /proc/version 2>/dev/null; then
        WSL_DETECTED=true
        log_success "WSL environment detected"
        
        # Get WSL distribution info
        if command -v lsb_release &> /dev/null; then
            echo -e "${COLOR_BLUE}[WSL]${COLOR_RESET} Distribution: $(lsb_release -ds)"
        fi
        
        # Check Windows host integration
        if [[ -d "/mnt/c/Windows" ]]; then
            log_success "Windows host filesystem accessible"
        fi
    else
        log_info "Native Linux environment detected"
    fi
    
    # System information
    echo -e "${COLOR_BLUE}[SYSTEM]${COLOR_RESET} $(uname -a)"
    echo -e "${COLOR_BLUE}[USER]${COLOR_RESET} $(whoami)@$(hostname)"
    echo -e "${COLOR_BLUE}[DATE]${COLOR_RESET} $(date)"
    
    # Check available resources
    if command -v free &> /dev/null; then
        echo -e "${COLOR_BLUE}[MEMORY]${COLOR_RESET} $(free -h | grep '^Mem' | awk '{print $3 "/" $2}')"
    fi
    
    if command -v df &> /dev/null; then
        echo -e "${COLOR_BLUE}[DISK]${COLOR_RESET} $(df -h . | tail -1 | awk '{print $3 "/" $2 " (" $5 " used)"}')"
    fi
}

check_python() {
    log_info "Checking Python installation..."
    
    if command -v python3 &> /dev/null; then
        PYTHON_VERSION=$(python3 --version)
        echo -e "${COLOR_BLUE}[PYTHON]${COLOR_RESET} $PYTHON_VERSION"
        
        # Check Python version compatibility
        local version_check=$(python3 -c "import sys; print(sys.version_info >= (3, 8))")
        if [[ "$version_check" == "True" ]]; then
            log_success "Python version is compatible"
        else
            log_error "Python 3.8+ required, found: $PYTHON_VERSION"
            exit 1
        fi
    else
        log_error "Python 3 not found! Please install Python 3.8+"
        
        # Offer to install on supported systems
        if command -v apt &> /dev/null; then
            echo -e "${COLOR_YELLOW}[HELP]${COLOR_RESET} Install with: sudo apt update && sudo apt install python3 python3-pip"
        elif command -v yum &> /dev/null; then
            echo -e "${COLOR_YELLOW}[HELP]${COLOR_RESET} Install with: sudo yum install python3 python3-pip"
        fi
        exit 1
    fi
}

check_gpu() {
    log_info "Checking GPU acceleration..."
    
    # Check NVIDIA GPU
    if command -v nvidia-smi &> /dev/null; then
        if nvidia-smi &> /dev/null; then
            GPU_AVAILABLE=true
            log_success "NVIDIA GPU detected"
            echo -e "${COLOR_BLUE}[GPU]${COLOR_RESET} $(nvidia-smi --query-gpu=name --format=csv,noheader,nounits | head -1)"
        fi
    fi
    
    # Check AMD GPU
    if [[ "$GPU_AVAILABLE" == false ]] && command -v rocm-smi &> /dev/null; then
        if rocm-smi &> /dev/null; then
            GPU_AVAILABLE=true
            log_success "AMD ROCm GPU detected"
        fi
    fi
    
    # Check Intel GPU
    if [[ "$GPU_AVAILABLE" == false ]] && [[ -d "/sys/class/drm" ]]; then
        if ls /sys/class/drm/card*/device/vendor 2>/dev/null | xargs cat | grep -q "0x8086"; then
            log_info "Intel GPU detected (limited acceleration)"
        fi
    fi
    
    if [[ "$GPU_AVAILABLE" == false ]]; then
        log_warning "No GPU acceleration detected - using CPU fallback"
    fi
}

check_docker() {
    log_info "Checking Docker availability..."
    
    if command -v docker &> /dev/null; then
        if docker ps &> /dev/null; then
            DOCKER_AVAILABLE=true
            log_success "Docker is available and running"
            echo -e "${COLOR_BLUE}[DOCKER]${COLOR_RESET} $(docker --version)"
        else
            log_warning "Docker installed but not running"
            echo -e "${COLOR_YELLOW}[HELP]${COLOR_RESET} Start with: sudo systemctl start docker"
        fi
    else
        log_warning "Docker not installed"
        if [[ "$WSL_DETECTED" == true ]]; then
            echo -e "${COLOR_YELLOW}[HELP]${COLOR_RESET} Consider installing Docker Desktop for Windows"
        fi
    fi
}

check_dependencies() {
    log_info "Checking Python dependencies..."
    
    if [[ ! -f "requirements.txt" ]]; then
        log_error "requirements.txt not found!"
        exit 1
    fi
    
    # Check if we need to install dependencies
    local missing_deps=$(python3 -c "
import importlib
import sys
required = ['fastapi', 'uvicorn', 'asyncio', 'psutil']
missing = []
for module in required:
    try:
        importlib.import_module(module)
    except ImportError:
        missing.append(module)
if missing:
    print(' '.join(missing))
else:
    print('none')
" 2>/dev/null || echo "check_failed")
    
    if [[ "$missing_deps" == "none" ]]; then
        log_success "All core dependencies available"
    elif [[ "$missing_deps" == "check_failed" ]]; then
        log_warning "Could not check dependencies - attempting installation..."
        install_dependencies
    else
        log_warning "Missing dependencies: $missing_deps"
        install_dependencies
    fi
}

install_dependencies() {
    log_info "Installing Python dependencies..."
    
    # Ensure pip is available
    if ! command -v pip3 &> /dev/null; then
        log_info "Installing pip..."
        python3 -m ensurepip --default-pip || {
            log_error "Failed to install pip"
            exit 1
        }
    fi
    
    # Upgrade pip
    python3 -m pip install --upgrade pip
    
    # Install requirements
    if python3 -m pip install -r requirements.txt; then
        log_success "Dependencies installed successfully"
    else
        log_error "Failed to install dependencies"
        exit 1
    fi
}

show_main_menu() {
    clear
    print_header
    
    echo -e "${COLOR_GREEN}[ULTIMATE MODES]${COLOR_RESET}"
    echo "  1. 🚀 Ultimate Enhanced Mode    - All features enabled (Recommended)"
    echo "  2. 🏠 Local-First Privacy Mode  - Complete offline experience"
    echo "  3. 🌐 Hybrid Cloud+Local Mode   - Best of both worlds"
    echo "  4. 🔧 Developer Debug Mode      - Full debugging enabled"
    echo ""
    echo -e "${COLOR_BLUE}[SPECIALIZED INTERFACES]${COLOR_RESET}"
    echo "  5. 🎨 Enhanced WebUI Dashboard  - Modern web interface"
    echo "  6. 💻 Charm Terminal Interface  - Beautiful terminal UI"
    echo "  7. 🖥️ Desktop Integration Mode   - ByteBot automation"
    echo "  8. 🐧 Linux System Integration  - Native system control"
    echo ""
    echo -e "${COLOR_YELLOW}[SYSTEM MANAGEMENT]${COLOR_RESET}"
    echo "  9. 📊 System Monitoring         - Real-time diagnostics"
    echo "  10. ⚙️ Configuration Manager     - Settings and optimization"
    echo "  11. 🧪 Test All Features         - Comprehensive validation"
    echo "  12. 📦 Create Deployment Package - Generate distribution"
    echo ""
    echo -e "${COLOR_MAGENTA}[UTILITIES]${COLOR_RESET}"
    echo "  q. ⚡ Quick Start (Optimized)   - One-click launch"
    echo "  s. 🛠️ System Diagnostics        - Deep system analysis"
    echo "  h. ❓ Help & Documentation      - Show detailed help"
    echo "  x. ❌ Exit                      - Close launcher"
    echo ""
    
    read -p "Enter your choice: " choice
}

launch_ultimate_mode() {
    log_info "Starting Ultimate Enhanced Mode..."
    
    echo -e "${COLOR_GREEN}[FEATURES]${COLOR_RESET} Enabling all enhancements:"
    echo "  ✓ Enhanced WebUI with real-time updates"
    echo "  ✓ Charm terminal interface"
    echo "  ✓ ByteBot desktop automation"
    echo "  ✓ Archon multi-agent orchestration"  
    echo "  ✓ Native Linux/WSL integration"
    echo "  ✓ Advanced monitoring and analytics"
    echo "  ✓ Multi-model AI routing"
    
    # Set environment variables
    export ENABLE_ENHANCED_WEBUI=true
    export ENABLE_CHARM_TERMINAL=true
    export ENABLE_BYTEBOT=true
    export ENABLE_ARCHON_FEATURES=true
    export ENABLE_WSL_INTEGRATION=$WSL_DETECTED
    export ENABLE_ADVANCED_MONITORING=true
    export AI_MODE=hybrid
    export LOG_LEVEL=info
    
    # Start services
    log_info "Starting enhanced ecosystem..."
    
    # Enhanced WebUI in background
    python3 -m duckbot.enhanced_webui --host 127.0.0.1 --port 8787 &
    WEBUI_PID=$!
    sleep 3
    
    # Charm Terminal in background  
    python3 -m duckbot.charm_terminal_ui &
    TERMINAL_PID=$!
    sleep 2
    
    # Main ecosystem
    python3 start_ecosystem.py --mode ultimate --enable-all
    
    # Cleanup on exit
    trap "kill $WEBUI_PID $TERMINAL_PID 2>/dev/null || true" EXIT
}

launch_local_mode() {
    log_info "Starting Local-First Privacy Mode..."
    
    export AI_LOCAL_ONLY_MODE=true
    export DISABLE_OPENROUTER=true
    export ENABLE_LM_STUDIO_ONLY=true
    export ENABLE_OFFLINE_FEATURES=true
    
    python3 start_local_ecosystem.py --privacy-mode
}

launch_webui_mode() {
    log_info "Starting Enhanced WebUI..."
    python3 -m duckbot.enhanced_webui --host 0.0.0.0 --port 8787
}

launch_terminal_mode() {
    log_info "Starting Charm Terminal Interface..."
    python3 -m duckbot.charm_terminal_ui
}

run_tests() {
    log_info "Running comprehensive feature tests..."
    
    echo -e "${COLOR_BLUE}[INFO]${COLOR_RESET} This will test all integrations and features..."
    
    # Run test suites
    python3 test_every_feature.py
    
    if [[ -f "test_enhanced_duckbot.py" ]]; then
        python3 test_enhanced_duckbot.py
    fi
    
    if [[ -f "test_local_feature_parity.py" ]]; then
        python3 test_local_feature_parity.py
    fi
    
    log_success "All tests completed. Check results above."
    read -p "Press Enter to continue..."
}

run_diagnostics() {
    log_info "Running deep system analysis..."
    
    echo -e "${COLOR_CYAN}[SYSTEM INFORMATION]${COLOR_RESET}"
    uname -a
    
    if command -v lscpu &> /dev/null; then
        echo -e "\n${COLOR_GREEN}[CPU INFO]${COLOR_RESET}"
        lscpu | head -15
    fi
    
    if command -v free &> /dev/null; then
        echo -e "\n${COLOR_GREEN}[MEMORY INFO]${COLOR_RESET}"
        free -h
    fi
    
    if command -v df &> /dev/null; then
        echo -e "\n${COLOR_GREEN}[DISK INFO]${COLOR_RESET}"
        df -h
    fi
    
    echo -e "\n${COLOR_GREEN}[PYTHON ENVIRONMENT]${COLOR_RESET}"
    python3 -c "
import sys, platform
print(f'Python: {sys.version}')
print(f'Platform: {platform.platform()}')
print(f'Architecture: {platform.architecture()}')
"
    
    echo -e "\n${COLOR_GREEN}[DEPENDENCY CHECK]${COLOR_RESET}"
    python3 -c "
import importlib
modules = ['fastapi', 'uvicorn', 'asyncio', 'psutil', 'PIL', 'cv2', 'numpy']
for mod in modules:
    try:
        importlib.import_module(mod.replace('PIL', 'PIL.Image'))
        print(f'✓ {mod}')
    except ImportError:
        print(f'✗ {mod} - missing')
"
    
    if [[ "$DOCKER_AVAILABLE" == true ]]; then
        echo -e "\n${COLOR_GREEN}[DOCKER INFO]${COLOR_RESET}"
        docker info --format 'table {{.ServerVersion}}\t{{.OSType}}/{{.Architecture}}'
    fi
    
    read -p "Press Enter to continue..."
}

show_help() {
    clear
    echo -e "${COLOR_CYAN}${COLOR_BOLD}"
    echo "================================================================================"
    echo "                              DuckBot v3.1.0+ Help"
    echo "================================================================================"
    echo -e "${COLOR_RESET}"
    
    echo -e "${COLOR_GREEN}[OVERVIEW]${COLOR_RESET}"
    echo "DuckBot v3.1.0+ is an enhanced AI ecosystem with advanced integrations:"
    echo ""
    echo -e "${COLOR_BLUE}[KEY FEATURES]${COLOR_RESET}"
    echo "  • Multi-Agent AI Orchestration (Archon-inspired)"
    echo "  • Desktop Automation & Control (ByteBot integration)"
    echo "  • Beautiful Terminal Interfaces (Charm-inspired)"
    echo "  • Linux/WSL native integration"
    echo "  • Real-time WebUI with monitoring"
    echo "  • Privacy-first local-only mode"
    echo "  • Hybrid cloud+local AI routing"
    echo "  • Advanced system monitoring"
    echo ""
    echo -e "${COLOR_YELLOW}[QUICK SETUP]${COLOR_RESET}"
    echo "  1. Choose 'Ultimate Enhanced Mode' for full experience"
    echo "  2. Or 'Local-First Privacy Mode' for offline usage"
    echo "  3. Configure your .env file with API keys (optional for local mode)"
    echo "  4. Access WebUI at http://127.0.0.1:8787"
    echo ""
    echo -e "${COLOR_MAGENTA}[SYSTEM REQUIREMENTS]${COLOR_RESET}"
    echo "  • Linux or Windows Subsystem for Linux"
    echo "  • Python 3.8+ with pip"
    echo "  • 4GB+ RAM (8GB+ recommended)"
    echo "  • GPU acceleration (optional but recommended)"
    echo ""
    
    read -p "Press Enter to continue..."
}

# Main execution
main() {
    # Initial system checks
    print_header
    check_system
    check_python
    check_gpu
    check_docker
    check_dependencies
    
    echo ""
    log_success "System initialization completed!"
    read -p "Press Enter to continue to main menu..."
    
    # Main menu loop
    while true; do
        show_main_menu
        
        case "$choice" in
            1) launch_ultimate_mode ;;
            2) launch_local_mode ;;
            3) 
                export AI_MODE=hybrid
                python3 start_ecosystem.py --mode hybrid
                ;;
            4)
                export LOG_LEVEL=debug
                python3 start_ecosystem.py --debug --verbose
                ;;
            5) launch_webui_mode ;;
            6) launch_terminal_mode ;;
            7) 
                export ENABLE_DESKTOP_AUTOMATION=true
                python3 -c "from duckbot.bytebot_integration import ByteBotIntegration; import asyncio; asyncio.run(ByteBotIntegration().start_interactive_mode())"
                ;;
            8)
                log_info "Starting Linux System Integration..."
                python3 -c "from duckbot.wsl_integration import wsl_integration; import asyncio; asyncio.run(wsl_integration.start_interactive_mode())"
                ;;
            9)
                python3 -c "
import psutil
print(f'CPU: {psutil.cpu_percent()}% | Memory: {psutil.virtual_memory().percent}% | Disk: {psutil.disk_usage(\"/\").percent}%')
"
                read -p "Press Enter to continue..."
                ;;
            10)
                python3 -c "from duckbot.settings_gpt import interactive_config; interactive_config()"
                ;;
            11) run_tests ;;
            12)
                log_info "Creating deployment package..."
                python3 create_deployment_package.py --include-integrations --optimize
                log_success "Deployment package created!"
                read -p "Press Enter to continue..."
                ;;
            q|Q)
                log_info "Quick Start - Using optimized configuration..."
                if [[ "$GPU_AVAILABLE" == true ]]; then
                    export AI_ACCELERATION=gpu
                    log_success "GPU acceleration enabled"
                fi
                python3 start_ecosystem.py --quick-start --optimize-for-system
                ;;
            s|S) run_diagnostics ;;
            h|H) show_help ;;
            x|X)
                echo -e "${COLOR_GREEN}Thank you for using DuckBot v3.1.0+ Ultimate Edition!${COLOR_RESET}"
                exit 0
                ;;
            *)
                log_error "Invalid choice. Please try again."
                sleep 2
                ;;
        esac
    done
}

# Run main function
main "$@"