/**
 * Demo script for DuckBotOS Desktop UI
 *
 * This script demonstrates the enhanced desktop OS-like interface
 * with chroma-web-os inspired components integrated with DuckBot features.
 *
 * Usage:
 * 1. Start the DuckBot WebUI: npm run dev
 * 2. Open http://localhost:3000 in your browser
 * 3. The desktop interface will load automatically
 * 4. Use Ctrl+Space to open the launcher
 * 5. Try different apps and window management features
 */

const express = require('express');
const path = require('path');
const app = express();
const port = 3000;

// Serve static files
app.use(express.static(path.join(__dirname, 'dist')));

// Main demo route
app.get('/', (req, res) => {
  res.send(`
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>DuckBotOS Desktop UI Demo</title>
        <style>
            body {
                margin: 0;
                padding: 0;
                overflow: hidden;
                background: #1a202c;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            }
            .demo-overlay {
                position: fixed;
                top: 0;
                left: 0;
                right: 0;
                bottom: 0;
                background: rgba(0, 0, 0, 0.8);
                display: flex;
                align-items: center;
                justify-content: center;
                z-index: 9999;
                color: white;
                text-align: center;
            }
            .demo-content {
                max-width: 600px;
                padding: 2rem;
            }
            .demo-content h1 {
                margin-top: 0;
                color: #4fd1c7;
            }
            .demo-content .shortcuts {
                background: rgba(255, 255, 255, 0.1);
                border-radius: 8px;
                padding: 1rem;
                margin: 1rem 0;
                text-align: left;
            }
            .demo-content .shortcut {
                margin: 0.5rem 0;
                display: flex;
                justify-content: space-between;
                align-items: center;
            }
            .demo-content .key {
                background: #2d3748;
                padding: 0.25rem 0.5rem;
                border-radius: 4px;
                font-family: monospace;
                font-size: 0.9rem;
            }
            .demo-content button {
                background: #4fd1c7;
                color: #1a202c;
                border: none;
                padding: 0.75rem 1.5rem;
                border-radius: 6px;
                font-weight: 600;
                cursor: pointer;
                margin: 0.5rem;
                transition: all 0.2s;
            }
            .demo-content button:hover {
                background: #38b2ac;
                transform: translateY(-1px);
            }
        </style>
    </head>
    <body>
        <div id="demo-overlay" class="demo-overlay">
            <div class="demo-content">
                <h1>🦆 DuckBotOS Desktop UI Demo</h1>
                <p>Welcome to the enhanced desktop OS-like interface for DuckBot!</p>

                <div class="shortcuts">
                    <h3>Keyboard Shortcuts:</h3>
                    <div class="shortcut">
                        <span>Open App Launcher</span>
                        <span class="key">Ctrl + Space</span>
                    </div>
                    <div class="shortcut">
                        <span>Switch Windows</span>
                        <span class="key">Alt + Tab</span>
                    </div>
                    <div class="shortcut">
                        <span>Close Window</span>
                        <span class="key">Ctrl + W</span>
                    </div>
                    <div class="shortcut">
                        <span>Minimize Window</span>
                        <span class="key">Ctrl + M</span>
                    </div>
                    <div class="shortcut">
                        <span>Close Launcher</span>
                        <span class="key">Esc</span>
                    </div>
                </div>

                <h3>Features to Try:</h3>
                <ul style="text-align: left; line-height: 1.8;">
                    <li>🖥️ <strong>3D Assistant</strong> - Interactive 3D AI assistant with controls</li>
                    <li>💬 <strong>AI Chat</strong> - Full-featured chat interface with voice input</li>
                    <li>🔧 <strong>System Monitor</strong> - Real-time system performance metrics</li>
                    <li>📁 <strong>File Manager</strong> - Navigate and organize your projects</li>
                    <li>⚙️ <strong>Settings</strong> - Configure AI providers and preferences</li>
                    <li>🖱️ <strong>Window Management</strong> - Drag, resize, minimize, maximize windows</li>
                    <li>🔍 <strong>App Launcher</strong> - Search and launch apps with keyboard navigation</li>
                    <li>📊 <strong>System Tray</strong> - WiFi, battery, volume, and time indicators</li>
                </ul>

                <button onclick="startDemo()">Start Desktop Demo</button>
                <button onclick="window.location.href='/?classic=true'">Use Classic Interface</button>
            </div>
        </div>

        <div id="root"></div>

        <script>
            function startDemo() {
                document.getElementById('demo-overlay').style.display = 'none';

                // Show welcome message after a short delay
                setTimeout(() => {
                    if (window.showNotification) {
                        window.showNotification('Welcome to DuckBotOS!', 'Press Ctrl+Space to open the app launcher');
                    }
                }, 2000);
            }

            // Check for classic interface parameter
            const urlParams = new URLSearchParams(window.location.search);
            if (urlParams.get('classic') === 'true') {
                document.getElementById('demo-overlay').style.display = 'none';
                // Load classic interface (would need proper implementation)
                console.log('Loading classic interface...');
            }

            // Global notification function
            window.showNotification = function(title, message) {
                const notification = document.createElement('div');
                notification.style.cssText = \`
                    position: fixed;
                    top: 20px;
                    right: 20px;
                    background: #2d3748;
                    color: white;
                    padding: 1rem;
                    border-radius: 8px;
                    border-left: 4px solid #4fd1c7;
                    max-width: 300px;
                    z-index: 10000;
                    animation: slideIn 0.3s ease-out;
                \`;
                notification.innerHTML = \`
                    <div style="font-weight: 600; margin-bottom: 0.5rem;">\${title}</div>
                    <div style="font-size: 0.9rem; opacity: 0.9;">\${message}</div>
                \`;

                document.body.appendChild(notification);

                setTimeout(() => {
                    notification.style.animation = 'slideOut 0.3s ease-out';
                    setTimeout(() => notification.remove(), 300);
                }, 5000);
            };

            // Add animations
            const style = document.createElement('style');
            style.textContent = \`
                @keyframes slideIn {
                    from { transform: translateX(100%); opacity: 0; }
                    to { transform: translateX(0); opacity: 1; }
                }
                @keyframes slideOut {
                    from { transform: translateX(0); opacity: 1; }
                    to { transform: translateX(100%); opacity: 0; }
                }
            \`;
            document.head.appendChild(style);
        </script>
    </body>
    </html>
  `);
});

// API routes for demo data
app.get('/api/system-status', (req, res) => {
  res.json({
    cpu: 45,
    memory: 67,
    disk: 82,
    network: 'connected',
    uptime: '2h 34m'
  });
});

app.get('/api/apps', (req, res) => {
  res.json([
    { id: 'assistant', name: '3D Assistant', category: 'ai', running: true },
    { id: 'chat', name: 'AI Chat', category: 'ai', running: false },
    { id: 'github', name: 'GitHub Manager', category: 'development', running: false },
    { id: 'monitor', name: 'System Monitor', category: 'system', running: false }
  ]);
});

app.listen(port, () => {
  console.log(`🦆 DuckBotOS Desktop UI Demo running at http://localhost:${port}`);
  console.log('');
  console.log('Features:');
  console.log('• Desktop OS-like interface with window management');
  console.log('• App launcher with search and categories');
  console.log('• 3D AI assistant integration');
  console.log('• System tray and status indicators');
  console.log('• Keyboard shortcuts and accessibility');
  console.log('');
  console.log('Open your browser and try it out!');
});