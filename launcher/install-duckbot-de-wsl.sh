#!/bin/bash
# DuckBot Desktop Environment - WSL Compatible Installation Script

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}================================${NC}"
echo -e "${BLUE}DuckBot-DE WSL Installation${NC}"
echo -e "${BLUE}GNOME + Chrome Remote Desktop${NC}"
echo -e "${BLUE}================================${NC}"

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

# Get current user
REAL_USER=$(whoami)
REAL_HOME="$HOME"

print_status "Installing for user: $REAL_USER"
print_status "User home directory: $REAL_HOME"

# Install GNOME if not present
print_status "Installing GNOME desktop environment..."
sudo apt update
sudo apt install -y gnome-shell gnome-session gnome-control-center ubuntu-desktop-minimal

# Install dependencies
print_status "Installing DuckBot-DE dependencies..."
sudo apt install -y \
    python3-pip \
    python3-dev \
    python3-gi \
    python3-gi-cairo \
    python3-dbus \
    gir1.2-gtk-3.0 \
    wmctrl \
    xdotool \
    nodejs \
    npm \
    git \
    curl \
    wget \
    dos2unix

# Install Python dependencies
print_status "Installing Python dependencies..."
pip3 install --user \
    dbus-python \
    pygobject \
    asyncio \
    websockets \
    aiohttp

# Install GNOME Shell extension
print_status "Installing DuckBot GNOME Shell extension..."
# Use relative path from script location
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DUCKBOT_DE_SOURCE="$(dirname "$SCRIPT_DIR")/DuckBot-DE"
mkdir -p "$REAL_HOME/.local/share/gnome-shell/extensions"

# Copy the shell extension
if [ -d "$DUCKBOT_DE_SOURCE/duckbot-shell-extension" ]; then
    cp -r "$DUCKBOT_DE_SOURCE/duckbot-shell-extension" "$REAL_HOME/.local/share/gnome-shell/extensions/duckbot-ai@duckbot-de"
    print_status "DuckBot shell extension installed"
else
    print_error "Shell extension not found at $DUCKBOT_DE_SOURCE/duckbot-shell-extension"
fi

# Install desktop services
print_status "Installing DuckBot desktop services..."
sudo mkdir -p /usr/libexec/duckbot-de
if [ -d "$DUCKBOT_DE_SOURCE/duckbot-desktop-services" ]; then
    sudo cp -r "$DUCKBOT_DE_SOURCE"/duckbot-desktop-services/* /usr/libexec/duckbot-de/
    sudo chmod +x /usr/libexec/duckbot-de/*
fi

# Create service wrapper scripts
print_status "Creating DuckBot service wrappers..."
sudo tee /usr/bin/duckbot-window-manager > /dev/null << 'EOF'
#!/bin/bash
export DISPLAY=${DISPLAY:-:1}
exec python3 /usr/libexec/duckbot-de/ai-window-manager.py
EOF

sudo chmod +x /usr/bin/duckbot-window-manager

# Configure Chrome Remote Desktop for GNOME
print_status "Configuring Chrome Remote Desktop for GNOME with DuckBot-DE..."
echo "exec /usr/bin/gnome-session" > "$REAL_HOME/.chrome-remote-desktop-session"

# Enable DuckBot extension
print_status "Enabling DuckBot extension..."
gsettings set org.gnome.shell enabled-extensions "['duckbot-ai@duckbot-de']" 2>/dev/null || true

# Create DuckBot configuration
print_status "Creating DuckBot configuration..."
mkdir -p "$REAL_HOME/.config/duckbot-de"
mkdir -p "$REAL_HOME/.local/share/duckbot-de/logs"

cat > "$REAL_HOME/.config/duckbot-de/ai-config.json" << 'EOF'
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
EOF

print_status "Installation complete!"
echo ""
echo -e "${GREEN}🦆 DuckBot-DE for WSL + Chrome Remote Desktop is ready!${NC}"
echo ""
echo -e "${YELLOW}Next Steps:${NC}"
echo "1. Restart Chrome Remote Desktop service:"
echo "   sudo systemctl stop chrome-remote-desktop"
echo "   sudo systemctl start chrome-remote-desktop"
echo ""
echo "2. Reconnect via Chrome Remote Desktop"
echo "3. You should now see GNOME desktop with DuckBot-DE extension!"
echo ""
echo -e "${BLUE}DuckBot-DE Features:${NC}"
echo "• AI panel in GNOME top bar"
echo "• Intelligent window management"
echo "• Voice control integration"
echo "• Memory-enhanced AI assistant"
echo ""
echo -e "${GREEN}Welcome to DuckBot Desktop Environment! 🚀${NC}"