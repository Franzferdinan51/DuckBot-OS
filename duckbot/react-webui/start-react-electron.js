#!/usr/bin/env node

const { spawn } = require('child_process');
const net = require('net');
const fs = require('fs');
const path = require('path');

class ReactElectronLauncher {
    constructor() {
        this.reactProcess = null;
        this.electronProcess = null;
        this.reactPort = 3000;
        this.maxRetries = 5;
        this.retryDelay = 2000;
        this.startupTimeout = 30000; // 30 seconds
        this.args = this.parseCommandLineArgs();
    }

    parseCommandLineArgs() {
        const args = process.argv.slice(2);
        const options = {
            reactOnly: false,
            electronOnly: false,
            help: false,
            port: 3000
        };

        for (let i = 0; i < args.length; i++) {
            const arg = args[i];
            switch (arg) {
                case '--react-only':
                    options.reactOnly = true;
                    break;
                case '--electron-only':
                    options.electronOnly = true;
                    break;
                case '--help':
                case '-h':
                    options.help = true;
                    break;
                case '--port':
                    if (i + 1 < args.length) {
                        options.port = parseInt(args[i + 1]);
                        i++;
                    }
                    break;
            }
        }

        return options;
    }

    showHelp() {
        console.log(`
🤖 DuckBot React + Electron Launcher

Usage: node start-react-electron.js [options]

Options:
  --react-only          Start only React development server
  --electron-only       Start only Electron app (requires React server running)
  --port <number>       Specify port number (default: 3000)
  --help, -h           Show this help message

Examples:
  node start-react-electron.js           # Start both React and Electron
  node start-react-electron.js --react-only  # Start only React server
  node start-react-electron.js --port 3001     # Use custom port
        `);
        process.exit(0);
    }

    async checkPort(port) {
        return new Promise((resolve) => {
            const server = net.createServer();
            server.listen(port, () => {
                server.once('close', () => resolve(true));
                server.close();
            }).on('error', () => resolve(false));
        });
    }

    async findAvailablePort(startPort) {
        for (let port = startPort; port < startPort + 10; port++) {
            if (await this.checkPort(port)) {
                return port;
            }
        }
        throw new Error(`No available ports found starting from ${startPort}`);
    }

    async startReactServer() {
        return new Promise(async (resolve, reject) => {
            try {
                // Find available port (start from the specified port)
                this.reactPort = await this.findAvailablePort(this.reactPort);
                console.log(`🚀 Starting React development server on port ${this.reactPort}...`);

                // Update .env file with the new port
                const envPath = path.join(__dirname, '.env.development.local');
                const envContent = `DANGEROUSLY_DISABLE_HOST_CHECK=true\nHOST=localhost\nPORT=${this.reactPort}\nHTTPS=false\nBROWSER=none\n`;
                fs.writeFileSync(envPath, envContent);

                // Start React server - handle both Windows and Unix
                const isWindows = process.platform === 'win32';
                const reactPath = isWindows
                    ? path.join(__dirname, 'node_modules', '.bin', 'react-scripts.cmd')
                    : path.join(__dirname, 'node_modules', '.bin', 'react-scripts');

                const args = ['start'];

                this.reactProcess = spawn(reactPath, args, {
                    cwd: __dirname,
                    env: { ...process.env, PORT: this.reactPort, BROWSER: 'none' },
                    stdio: 'pipe',
                    shell: isWindows
                });

                let startupTimer;
                let outputBuffer = '';

                const cleanup = () => {
                    if (startupTimer) clearTimeout(startupTimer);
                };

                startupTimer = setTimeout(() => {
                    cleanup();
                    reject(new Error('React server startup timeout'));
                }, this.startupTimeout);

                this.reactProcess.stdout.on('data', (data) => {
                    const output = data.toString();
                    outputBuffer += output;

                    console.log(`[React] ${output.trim()}`);

                    // Check for successful startup indicators
                    if (output.includes('Compiled successfully') ||
                        output.includes('webpack compiled') ||
                        output.includes('Starting the development server')) {
                        cleanup();
                        resolve();
                    }
                });

                this.reactProcess.stderr.on('data', (data) => {
                    const output = data.toString();
                    console.error(`[React Error] ${output.trim()}`);

                    // Check for port conflicts
                    if (output.includes('EADDRINUSE') || output.includes('port is already in use')) {
                        cleanup();
                        reject(new Error('Port conflict detected'));
                    }
                });

                this.reactProcess.on('error', (error) => {
                    cleanup();
                    reject(error);
                });

                this.reactProcess.on('exit', (code, signal) => {
                    cleanup();
                    if (code !== 0) {
                        reject(new Error(`React process exited with code ${code}`));
                    }
                });

            } catch (error) {
                reject(error);
            }
        });
    }

    async waitForReactServer() {
        const maxAttempts = 30;
        const attemptDelay = 1000;

        for (let attempt = 1; attempt <= maxAttempts; attempt++) {
            try {
                const response = await fetch(`http://localhost:${this.reactPort}`);
                if (response.ok) {
                    console.log(`✅ React server is accessible on port ${this.reactPort}`);
                    return;
                }
            } catch (error) {
                console.log(`Attempt ${attempt}/${maxAttempts}: Waiting for React server...`);
            }

            if (attempt < maxAttempts) {
                await new Promise(resolve => setTimeout(resolve, attemptDelay));
            }
        }

        throw new Error('React server did not become accessible');
    }

    async startElectron() {
        return new Promise((resolve, reject) => {
            try {
                console.log('🖥️  Starting Electron app...');

                const isWindows = process.platform === 'win32';
                const electronPath = isWindows
                    ? path.join(__dirname, 'node_modules', '.bin', 'electron.cmd')
                    : path.join(__dirname, 'node_modules', '.bin', 'electron');

                const mainScript = path.join(__dirname, 'electron-main.js');

                // Set environment variable for React port
                const env = { ...process.env, REACT_PORT: this.reactPort };

                this.electronProcess = spawn(electronPath, [mainScript], {
                    cwd: __dirname,
                    env,
                    stdio: 'pipe',
                    shell: isWindows
                });

                this.electronProcess.stdout.on('data', (data) => {
                    console.log(`[Electron] ${data.toString().trim()}`);
                });

                this.electronProcess.stderr.on('data', (data) => {
                    console.error(`[Electron Error] ${data.toString().trim()}`);
                });

                this.electronProcess.on('error', (error) => {
                    reject(error);
                });

                // Resolve when Electron starts successfully
                this.electronProcess.on('spawn', () => {
                    resolve();
                });

            } catch (error) {
                reject(error);
            }
        });
    }

    async updateElectronConfig() {
        try {
            const electronMainPath = path.join(__dirname, 'electron-main.js');
            let electronMainContent = fs.readFileSync(electronMainPath, 'utf8');

            // Update the port in electron-main.js
            electronMainContent = electronMainContent.replace(
                /mainWindow\.loadURL\('http:\/\/localhost:3000'\);/,
                `mainWindow.loadURL('http://localhost:${this.reactPort}');`
            );

            fs.writeFileSync(electronMainPath, electronMainContent);
            console.log(`📝 Updated Electron config to use port ${this.reactPort}`);

        } catch (error) {
            console.error('Failed to update Electron config:', error);
        }
    }

    async cleanup() {
        console.log('🧹 Cleaning up processes...');

        if (this.reactProcess) {
            this.reactProcess.kill('SIGTERM');
            this.reactProcess = null;
        }

        if (this.electronProcess) {
            this.electronProcess.kill('SIGTERM');
            this.electronProcess = null;
        }
    }

    async start() {
        try {
            // Show help if requested
            if (this.args.help) {
                this.showHelp();
                return;
            }

            // Use custom port if specified
            if (this.args.port && this.args.port !== 3000) {
                this.reactPort = this.args.port;
            }

            console.log('🎯 Starting DuckBot React + Electron Application...');
            console.log('='.repeat(50));

            if (this.args.electronOnly) {
                // Start only Electron app
                console.log('🖥️  Starting Electron app only...');
                await this.startElectron();
            } else {
                // Start React server (and optionally Electron)
                await this.startReactServer();
                await this.waitForReactServer();

                if (!this.args.reactOnly) {
                    // Start Electron app as well
                    await this.updateElectronConfig();
                    await this.startElectron();
                }
            }

            console.log('='.repeat(50));
            if (this.args.reactOnly) {
                console.log('🎉 React development server started successfully!');
                console.log(`📍 React server: http://localhost:${this.reactPort}`);
            } else if (this.args.electronOnly) {
                console.log('🎉 Electron app started successfully!');
                console.log('🖥️  Electron app: Running in desktop window');
            } else {
                console.log('🎉 DuckBot React + Electron application started successfully!');
                console.log(`📍 React server: http://localhost:${this.reactPort}`);
                console.log('🖥️  Electron app: Running in desktop window');
            }
            console.log('='.repeat(50));

            // Handle graceful shutdown
            process.on('SIGINT', async () => {
                console.log('\n🛑 Received SIGINT, shutting down gracefully...');
                await this.cleanup();
                process.exit(0);
            });

            process.on('SIGTERM', async () => {
                console.log('\n🛑 Received SIGTERM, shutting down gracefully...');
                await this.cleanup();
                process.exit(0);
            });

        } catch (error) {
            console.error('❌ Failed to start application:', error);
            await this.cleanup();
            process.exit(1);
        }
    }
}

// Start the application
const launcher = new ReactElectronLauncher();
launcher.start().catch(console.error);