#!/bin/bash
# DuckBot Desktop Environment Installation Script

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging
LOGFILE="/tmp/duckbot-de-install.log"
exec > >(tee -a "$LOGFILE")
exec 2>&1

echo -e "${BLUE}================================${NC}"
echo -e "${BLUE}DuckBot Desktop Environment Installer${NC}"
echo -e "${BLUE}The World's First AI-Native Desktop${NC}"
echo -e "${BLUE}================================${NC}"
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}Error: This script must be run as root (use sudo)${NC}"
    echo "Usage: sudo ./install-duckbot-de.sh"
    exit 1
fi

# Get the actual user (not root when using sudo)
REAL_USER=${SUDO_USER:-$(whoami)}
REAL_HOME=$(eval echo ~$REAL_USER)

echo -e "${GREEN}Installing for user: $REAL_USER${NC}"
echo -e "${GREEN}User home directory: $REAL_HOME${NC}"
echo ""

# Function to print status
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check system requirements
print_status "Checking system requirements..."

# Check Ubuntu version
if ! lsb_release -d | grep -q "Ubuntu"; then
    print_warning "This installer is optimized for Ubuntu. Proceeding anyway..."
fi

# Check GNOME
if ! which gnome-shell >/dev/null 2>&1; then
    print_error "GNOME Shell is required but not installed."
    print_status "Installing GNOME Shell..."
    apt update
    apt install -y gnome-shell gnome-session gnome-control-center
fi

# Check Python
if ! which python3 >/dev/null 2>&1; then
    print_error "Python 3 is required but not installed."
    apt install -y python3 python3-pip
fi

# Check Node.js
if ! which node >/dev/null 2>&1; then
    print_status "Installing Node.js..."
    curl -fsSL https://deb.nodesource.com/setup_18.x | bash -
    apt install -y nodejs
fi

# Check Go
if ! which go >/dev/null 2>&1; then
    print_status "Installing Go..."
    GO_VERSION="1.21.0"
    wget -c "https://go.dev/dl/go${GO_VERSION}.linux-amd64.tar.gz"
    tar -C /usr/local -xzf "go${GO_VERSION}.linux-amd64.tar.gz"
    echo 'export PATH=$PATH:/usr/local/go/bin' >> /etc/profile
    rm "go${GO_VERSION}.linux-amd64.tar.gz"
fi

# Install dependencies
print_status "Installing system dependencies..."
apt update
apt install -y \
    python3-pip \
    python3-dev \
    python3-gi \
    python3-gi-cairo \
    python3-dbus \
    gir1.2-gtk-3.0 \
    gir1.2-glib-2.0 \
    gir1.2-gio-2.0 \
    wmctrl \
    xdotool \
    pulseaudio \
    pipewire \
    gstreamer1.0-plugins-good \
    gstreamer1.0-plugins-bad \
    nodejs \
    npm \
    git \
    curl \
    wget \
    build-essential

print_status "Installing Python dependencies..."
pip3 install --system \
    dbus-python \
    pygobject \
    asyncio \
    websockets \
    aiohttp \
    numpy \
    scipy

# Install DuckBot core dependencies
print_status "Installing DuckBot core system..."

# Create DuckBot directories
mkdir -p /usr/share/duckbot-de
mkdir -p /etc/duckbot-de
mkdir -p /usr/libexec/duckbot-de
mkdir -p /var/lib/duckbot-de

# Copy DuckBot core files (assuming they're in parent directory)
DUCKBOT_SOURCE_DIR="$(dirname "$(pwd)")"
if [ -d "$DUCKBOT_SOURCE_DIR/duckbot" ]; then
    cp -r "$DUCKBOT_SOURCE_DIR/duckbot" /usr/share/duckbot-de/
    cp -r "$DUCKBOT_SOURCE_DIR/requirements.txt" /usr/share/duckbot-de/
    
    # Install Python requirements
    pip3 install -r /usr/share/duckbot-de/requirements.txt
    
    print_status "DuckBot core system installed"
else
    print_warning "DuckBot core not found at $DUCKBOT_SOURCE_DIR/duckbot"
    print_status "You may need to install DuckBot core separately"
fi

# Install Charm ecosystem tools
print_status "Installing Charm ecosystem tools..."
export PATH=$PATH:/usr/local/go/bin
sudo -u $REAL_USER bash << 'EOF'
export PATH=$PATH:/usr/local/go/bin
go install github.com/charmbracelet/gum@latest
go install github.com/charmbracelet/glow@latest
go install github.com/charmbracelet/mods@latest
go install github.com/charmbracelet/skate@latest
go install github.com/charmbracelet/crush@latest
go install github.com/charmbracelet/charm@latest
go install github.com/charmbracelet/freeze@latest
go install github.com/charmbracelet/vhs@latest
EOF

# Copy Charm tools to system path
REAL_USER_HOME=$(eval echo ~$REAL_USER)
if [ -d "$REAL_USER_HOME/go/bin" ]; then
    cp "$REAL_USER_HOME/go/bin"/* /usr/local/bin/ 2>/dev/null || true
    print_status "Charm tools installed system-wide"
fi

# Install GNOME Shell extension
print_status "Installing DuckBot GNOME Shell extension..."
mkdir -p "$REAL_HOME/.local/share/gnome-shell/extensions/duckbot-ai@duckbot-de"
cp -r duckbot-shell-extension/* "$REAL_HOME/.local/share/gnome-shell/extensions/duckbot-ai@duckbot-de/"
chown -R $REAL_USER:$REAL_USER "$REAL_HOME/.local/share/gnome-shell/extensions/duckbot-ai@duckbot-de"

# Compile GSettings schemas if any
if [ -f "duckbot-shell-extension/schemas/org.gnome.shell.extensions.duckbot-ai.gschema.xml" ]; then
    cp duckbot-shell-extension/schemas/* /usr/share/glib-2.0/schemas/
    glib-compile-schemas /usr/share/glib-2.0/schemas/
fi

# Install desktop services
print_status "Installing DuckBot desktop services..."
cp duckbot-desktop-services/* /usr/libexec/duckbot-de/
chmod +x /usr/libexec/duckbot-de/*

# Create service wrapper scripts
cat > /usr/bin/duckbot-ai-service << 'EOF'
#!/bin/bash
export PYTHONPATH=/usr/share/duckbot-de:$PYTHONPATH
cd /usr/share/duckbot-de
exec python3 -c "
import sys
sys.path.insert(0, '/usr/share/duckbot-de')
from duckbot.integration_manager import initialize_integration_manager
import asyncio
asyncio.run(initialize_integration_manager())
"
EOF

cat > /usr/bin/duckbot-window-manager << 'EOF'
#!/bin/bash
export PYTHONPATH=/usr/share/duckbot-de:$PYTHONPATH
exec python3 /usr/libexec/duckbot-de/ai-window-manager.py
EOF

chmod +x /usr/bin/duckbot-ai-service
chmod +x /usr/bin/duckbot-window-manager

# Install session files
print_status "Installing DuckBot session manager..."
cp duckbot-session/duckbot-session /usr/bin/
chmod +x /usr/bin/duckbot-session

cp duckbot-session/duckbot.desktop /usr/share/xsessions/
cp duckbot-session/duckbot.desktop /usr/share/wayland-sessions/ 2>/dev/null || true

# Create GNOME Shell mode
print_status "Creating DuckBot GNOME Shell mode..."
mkdir -p /usr/share/gnome-shell/modes
cat > /usr/share/gnome-shell/modes/duckbot.json << 'EOF'
{
    "parentMode": "user",
    "stylesheetName": "duckbot.css",
    "themeResourceName": "duckbot-theme",
    "hasOverview": true,
    "hasAppMenu": true,
    "hasNotifications": true,
    "hasWmMenus": true,
    "enabledExtensions": ["duckbot-ai@duckbot-de"],
    "sessionMode": "duckbot",
    "unlockDialog": "org.gnome.Shell.ScreenShield"
}
EOF

# Create custom stylesheet
mkdir -p /usr/share/gnome-shell/theme
cat > /usr/share/gnome-shell/theme/duckbot.css << 'EOF'
/* DuckBot AI Desktop Theme */
@import url("gnome-shell.css");

/* AI Panel Styling */
.duckbot-icon {
    color: #4fc3f7;
}

.duckbot-status {
    color: #81c784;
    font-weight: bold;
    margin-left: 8px;
}

/* AI Enhancement Indicators */
.ai-enhanced {
    border-left: 3px solid #4fc3f7;
}

/* Voice Control Indicator */
.voice-active {
    background-color: rgba(76, 175, 80, 0.2);
    border-radius: 6px;
}
EOF

# Set up user configuration
print_status "Setting up user configuration..."
sudo -u $REAL_USER bash << EOF
mkdir -p "$REAL_HOME/.config/duckbot-de"
mkdir -p "$REAL_HOME/.local/share/duckbot-de/logs"

# Default AI configuration
cat > "$REAL_HOME/.config/duckbot-de/ai-config.json" << 'EOCONFIG'
{
    "personality": "professional",
    "verbosity": "moderate",
    "automation": "smart",
    "memory": "enhanced",
    "voice": "enabled",
    "desktop_integration": true,
    "window_management": true,
    "context_awareness": true
}
EOCONFIG

# Workspace templates
cat > "$REAL_HOME/.config/duckbot-de/workspaces.yaml" << 'EOWORKSPACES'
development:
  applications: ["code", "gnome-terminal", "firefox"]
  layout: "development_split"
  ai_agents: ["code-assistant", "documentation"]

research:
  applications: ["firefox", "gnome-text-editor", "evince"]
  layout: "research_grid"
  ai_agents: ["research-assistant", "summarizer"]

creative:
  applications: ["gimp", "inkscape", "blender"]
  layout: "creative_suite"
  ai_agents: ["creative-assistant", "asset-manager"]

communication:
  applications: ["thunderbird", "evolution", "slack"]
  layout: "communication_hub"
  ai_agents: ["meeting-assistant", "email-ai"]
EOWORKSPACES
EOF

# Create desktop applications
print_status "Installing DuckBot applications..."
mkdir -p /usr/share/applications

cat > /usr/share/applications/duckbot-settings.desktop << 'EOF'
[Desktop Entry]
Name=DuckBot AI Settings
Comment=Configure DuckBot AI Desktop Environment
Exec=gnome-control-center
Icon=preferences-system
Type=Application
Categories=Settings;System;
Keywords=duckbot;ai;settings;preferences;
EOF

cat > /usr/share/applications/duckbot-memory-browser.desktop << 'EOF'
[Desktop Entry]
Name=Memory Browser
Comment=Browse and manage AI memory with Memento
Exec=glow /usr/share/duckbot-de/docs/memory.md
Icon=folder-documents
Type=Application
Categories=Office;Utility;
Keywords=duckbot;memory;ai;memento;
EOF

# Enable DuckBot extension for the user
print_status "Enabling DuckBot extension..."
sudo -u $REAL_USER dbus-launch gsettings set org.gnome.shell enabled-extensions "['duckbot-ai@duckbot-de']" 2>/dev/null || true

# Create systemd user services for AI components
print_status "Creating systemd user services..."
mkdir -p /etc/systemd/user

cat > /etc/systemd/user/duckbot-ai.service << 'EOF'
[Unit]
Description=DuckBot AI Desktop Services
After=graphical-session.target

[Service]
Type=simple
ExecStart=/usr/bin/duckbot-ai-service --desktop-mode
Restart=always
RestartSec=5
Environment=DISPLAY=:0
Environment=DUCKBOT_DESKTOP_MODE=true

[Install]
WantedBy=default.target
EOF

cat > /etc/systemd/user/duckbot-window-manager.service << 'EOF'
[Unit]
Description=DuckBot AI Window Manager
After=graphical-session.target duckbot-ai.service
Requires=duckbot-ai.service

[Service]
Type=simple
ExecStart=/usr/bin/duckbot-window-manager
Restart=always
RestartSec=5
Environment=DISPLAY=:0

[Install]
WantedBy=default.target
EOF

systemctl daemon-reload

# Final setup
print_status "Completing installation..."

# Update icon cache
gtk-update-icon-cache -f /usr/share/icons/hicolor/ 2>/dev/null || true

# Update desktop database
update-desktop-database /usr/share/applications/ 2>/dev/null || true

# Set proper permissions
chown -R $REAL_USER:$REAL_USER "$REAL_HOME/.config/duckbot-de"
chown -R $REAL_USER:$REAL_USER "$REAL_HOME/.local/share/duckbot-de"

print_status "Installation complete!"
echo ""
echo -e "${GREEN}🦆 DuckBot AI Desktop Environment has been installed successfully!${NC}"
echo ""
echo -e "${YELLOW}Next Steps:${NC}"
echo "1. Log out of your current session"
echo "2. At the login screen, click the gear icon and select 'DuckBot AI Desktop'"
echo "3. Log in to experience the world's first AI-native desktop environment"
echo ""
echo -e "${BLUE}Features available in your new AI desktop:${NC}"
echo "• AI-powered window management (Super+Space)"
echo "• Voice control for desktop operations (Super+V)"  
echo "• Intelligent workspace creation and organization"
echo "• Memory-enhanced AI assistant with learning capabilities"
echo "• Complete Charm ecosystem integration"
echo "• Multi-agent AI coordination"
echo ""
echo -e "${GREEN}Welcome to the future of desktop computing! 🚀${NC}"
echo ""
print_status "Installation log saved to: $LOGFILE"