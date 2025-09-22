#!/usr/bin/env node

const { spawn } = require('child_process');
const net = require('net');
const fs = require('fs');
const path = require('path');

console.log('🧪 Testing DuckBot React + Electron Setup');
console.log('='.repeat(50));

class SetupTester {
    constructor() {
        this.testResults = [];
        this.reactPort = 3001; // Use a different port for testing
    }

    logTest(testName, passed, message = '') {
        const status = passed ? '✅' : '❌';
        console.log(`${status} ${testName}${message ? ': ' + message : ''}`);
        this.testResults.push({ testName, passed, message });
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

    async testNodeInstallation() {
        try {
            const result = spawn('node', ['--version']);
            await new Promise((resolve, reject) => {
                result.on('exit', (code) => code === 0 ? resolve() : reject());
                result.on('error', reject);
            });
            this.logTest('Node.js Installation', true);
            return true;
        } catch (error) {
            this.logTest('Node.js Installation', false, error.message);
            return false;
        }
    }

    async testNpmInstallation() {
        try {
            const result = spawn('npm', ['--version']);
            await new Promise((resolve, reject) => {
                result.on('exit', (code) => code === 0 ? resolve() : reject());
                result.on('error', reject);
            });
            this.logTest('npm Installation', true);
            return true;
        } catch (error) {
            this.logTest('npm Installation', false, error.message);
            return false;
        }
    }

    async testDependencies() {
        const nodeModulesPath = path.join(__dirname, 'node_modules');
        const packageJsonPath = path.join(__dirname, 'package.json');

        const hasNodeModules = fs.existsSync(nodeModulesPath);
        const hasPackageJson = fs.existsSync(packageJsonPath);

        if (!hasPackageJson) {
            this.logTest('Package.json', false, 'package.json not found');
            return false;
        }

        if (!hasNodeModules) {
            this.logTest('Dependencies', false, 'node_modules not found. Run: npm install');
            return false;
        }

        // Check key dependencies
        const keyDeps = ['react', 'react-dom', 'electron', 'react-scripts'];
        const missingDeps = [];

        for (const dep of keyDeps) {
            const depPath = path.join(nodeModulesPath, dep);
            if (!fs.existsSync(depPath)) {
                missingDeps.push(dep);
            }
        }

        if (missingDeps.length > 0) {
            this.logTest('Key Dependencies', false, `Missing: ${missingDeps.join(', ')}`);
            return false;
        }

        this.logTest('Dependencies', true);
        return true;
    }

    async testPortAvailability() {
        const port = await this.checkPort(this.reactPort);
        this.logTest('Port Availability', port, port ? `Port ${this.reactPort} is available` : `Port ${this.reactPort} is in use`);
        return port;
    }

    async testStartupScript() {
        const scriptPath = path.join(__dirname, 'start-react-electron.js');
        const scriptExists = fs.existsSync(scriptPath);

        if (!scriptExists) {
            this.logTest('Startup Script', false, 'start-react-electron.js not found');
            return false;
        }

        // Test if script can be executed
        try {
            const result = spawn('node', [scriptPath, '--help']);
            let output = '';
            let error = '';

            result.stdout.on('data', (data) => {
                output += data.toString();
            });

            result.stderr.on('data', (data) => {
                error += data.toString();
            });

            await new Promise((resolve, reject) => {
                result.on('exit', (code) => {
                    if (code === 0) {
                        resolve();
                    } else {
                        reject(new Error(error || 'Script execution failed'));
                    }
                });
                result.on('error', reject);
            });

            this.logTest('Startup Script', true, 'Script executes successfully');
            return true;
        } catch (error) {
            this.logTest('Startup Script', false, error.message);
            return false;
        }
    }

    async testElectronConfig() {
        const electronMainPath = path.join(__dirname, 'electron-main.js');
        const preloadPath = path.join(__dirname, 'preload.js');

        const hasElectronMain = fs.existsSync(electronMainPath);
        const hasPreload = fs.existsSync(preloadPath);

        if (!hasElectronMain) {
            this.logTest('Electron Main', false, 'electron-main.js not found');
            return false;
        }

        if (!hasPreload) {
            this.logTest('Preload Script', false, 'preload.js not found');
            return false;
        }

        this.logTest('Electron Configuration', true);
        return true;
    }

    async testReactSource() {
        const srcPath = path.join(__dirname, 'src');
        const appPath = path.join(srcPath, 'App.js');
        const indexPath = path.join(srcPath, 'index.tsx');

        const hasSrc = fs.existsSync(srcPath);
        const hasApp = fs.existsSync(appPath);
        const hasIndex = fs.existsSync(indexPath);

        if (!hasSrc) {
            this.logTest('React Source', false, 'src directory not found');
            return false;
        }

        if (!hasApp) {
            this.logTest('React App', false, 'src/App.js not found');
            return false;
        }

        if (!hasIndex) {
            this.logTest('React Index', false, 'src/index.tsx not found');
            return false;
        }

        this.logTest('React Source Files', true);
        return true;
    }

    async testEnvironmentFile() {
        const envPath = path.join(__dirname, '.env.development.local');
        const envExists = fs.existsSync(envPath);

        if (!envExists) {
            this.logTest('Environment File', false, '.env.development.local not found');
            return false;
        }

        try {
            const envContent = fs.readFileSync(envPath, 'utf8');
            const requiredVars = ['PORT', 'HOST', 'BROWSER'];
            const missingVars = [];

            for (const varName of requiredVars) {
                if (!envContent.includes(`${varName}=`)) {
                    missingVars.push(varName);
                }
            }

            if (missingVars.length > 0) {
                this.logTest('Environment Variables', false, `Missing: ${missingVars.join(', ')}`);
                return false;
            }

            this.logTest('Environment File', true);
            return true;
        } catch (error) {
            this.logTest('Environment File', false, error.message);
            return false;
        }
    }

    async testPackageJsonScripts() {
        const packageJsonPath = path.join(__dirname, 'package.json');

        try {
            const packageJson = JSON.parse(fs.readFileSync(packageJsonPath, 'utf8'));
            const scripts = packageJson.scripts || {};

            const requiredScripts = [
                'start:all',
                'start:react',
                'start:electron',
                'electron:dev'
            ];

            const missingScripts = [];

            for (const script of requiredScripts) {
                if (!scripts[script]) {
                    missingScripts.push(script);
                }
            }

            if (missingScripts.length > 0) {
                this.logTest('Package.json Scripts', false, `Missing: ${missingScripts.join(', ')}`);
                return false;
            }

            this.logTest('Package.json Scripts', true);
            return true;
        } catch (error) {
            this.logTest('Package.json Scripts', false, error.message);
            return false;
        }
    }

    async runAllTests() {
        console.log('🔍 Running comprehensive setup tests...\n');

        const tests = [
            this.testNodeInstallation(),
            this.testNpmInstallation(),
            this.testDependencies(),
            this.testPortAvailability(),
            this.testStartupScript(),
            this.testElectronConfig(),
            this.testReactSource(),
            this.testEnvironmentFile(),
            this.testPackageJsonScripts()
        ];

        const results = await Promise.all(tests);

        console.log('\n' + '='.repeat(50));
        console.log('📊 Test Results Summary');
        console.log('='.repeat(50));

        const passed = results.filter(r => r).length;
        const total = results.length;

        console.log(`Passed: ${passed}/${total}`);

        if (passed === total) {
            console.log('\n🎉 All tests passed! The React + Electron setup is ready.');
            console.log('\n🚀 Quick Start Commands:');
            console.log('  npm run start:all     # Start both React and Electron');
            console.log('  node start-react-electron.js --help     # See all options');
            console.log('  START_REACT_ELECTRON.bat              # Windows launcher');
        } else {
            console.log('\n❌ Some tests failed. Please fix the issues above before starting.');
            console.log('\n🔧 Common Fixes:');
            console.log('  npm install                           # Install dependencies');
            console.log('  npm install -g electron               # Install Electron globally');
            console.log('  Check port availability with netstat -an');
        }

        console.log('\nFor detailed troubleshooting, see README_REACT_ELECTRON.md');
    }
}

// Run the tests
const tester = new SetupTester();
tester.runAllTests().catch(console.error);