const fs = require('fs');
const path = require('path');
const { spawn, exec } = require('child_process');
const { promisify } = require('util');

const execAsync = promisify(exec);

class ElectronErrorHandler {
    constructor(config = {}) {
        this.config = {
            logFile: config.logFile || path.join(__dirname, '..', 'logs', 'electron-error.log'),
            enableConsole: config.enableConsole !== false,
            enableFile: config.enableFile !== false,
            autoRecovery: config.autoRecovery !== false,
            maxRetries: config.maxRetries || 3,
            retryDelay: config.retryDelay || 2000,
            maxLogSize: config.maxLogSize || 10 * 1024 * 1024, // 10MB
            ...config
        };

        this.errorHistory = [];
        this.monitoringActive = false;
        this.monitoringInterval = null;

        // Ensure logs directory exists
        this.ensureLogDirectory();

        // Initialize error handler
        this.initialize();
    }

    initialize() {
        try {
            this.logInfo('Electron Error Handler initialized', {
                config: {
                    logFile: this.config.logFile,
                    enableConsole: this.config.enableConsole,
                    enableFile: this.config.enableFile,
                    autoRecovery: this.config.autoRecovery,
                    maxRetries: this.config.maxRetries,
                    retryDelay: this.config.retryDelay
                }
            });
        } catch (error) {
            console.error('Failed to initialize error handler:', error);
        }
    }

    ensureLogDirectory() {
        const logDir = path.dirname(this.config.logFile);
        if (!fs.existsSync(logDir)) {
            fs.mkdirSync(logDir, { recursive: true });
        }
    }

    logInfo(message, context = {}) {
        this.log('INFO', message, context);
    }

    logWarning(message, context = {}) {
        this.log('WARNING', message, context);
    }

    logError(message, context = {}) {
        this.log('ERROR', message, context);
    }

    logDebug(message, context = {}) {
        this.log('DEBUG', message, context);
    }

    log(level, message, context = {}) {
        const timestamp = new Date().toISOString();
        const logEntry = {
            timestamp,
            level,
            message,
            context,
            pid: process.pid
        };

        // Store in history
        this.errorHistory.push(logEntry);

        // Keep history manageable
        if (this.errorHistory.length > 1000) {
            this.errorHistory = this.errorHistory.slice(-500);
        }

        // Console logging
        if (this.config.enableConsole) {
            const consoleMessage = `[${timestamp}] [${level}] ${message}`;
            if (level === 'ERROR') {
                console.error(consoleMessage, context);
            } else if (level === 'WARNING') {
                console.warn(consoleMessage, context);
            } else {
                console.log(consoleMessage, context);
            }
        }

        // File logging
        if (this.config.enableFile) {
            this.writeToFile(logEntry);
        }
    }

    writeToFile(logEntry) {
        try {
            // Check log file size and rotate if necessary
            if (fs.existsSync(this.config.logFile)) {
                const stats = fs.statSync(this.config.logFile);
                if (stats.size > this.config.maxLogSize) {
                    this.rotateLogFile();
                }
            }

            const logLine = JSON.stringify(logEntry) + '\n';
            fs.appendFileSync(this.config.logFile, logLine);
        } catch (error) {
            console.error('Failed to write to log file:', error);
        }
    }

    rotateLogFile() {
        try {
            const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
            const backupFile = this.config.logFile.replace(/\.log$/, `_backup_${timestamp}.log`);

            if (fs.existsSync(this.config.logFile)) {
                fs.renameSync(this.config.logFile, backupFile);
            }
        } catch (error) {
            console.error('Failed to rotate log file:', error);
        }
    }

    handleError(errorCode, message, context = {}) {
        const error = {
            code: errorCode,
            message,
            context,
            timestamp: new Date().toISOString(),
            stack: new Error().stack
        };

        this.logError(`[${errorCode}] ${message}`, context);

        // Attempt automatic recovery if enabled
        if (this.config.autoRecovery) {
            this.attemptRecovery(error);
        }

        return error;
    }

    classifyError(message) {
        const lowerMessage = message.toLowerCase();

        if (lowerMessage.includes('timeout') || lowerMessage.includes('connection')) {
            return { type: 'network', severity: 'high' };
        } else if (lowerMessage.includes('memory') || lowerMessage.includes('allocation')) {
            return { type: 'memory', severity: 'critical' };
        } else if (lowerMessage.includes('permission') || lowerMessage.includes('access')) {
            return { type: 'permission', severity: 'high' };
        } else if (lowerMessage.includes('file') || lowerMessage.includes('not found')) {
            return { type: 'file', severity: 'medium' };
        } else if (lowerMessage.includes('python') || lowerMessage.includes('module')) {
            return { type: 'dependency', severity: 'high' };
        } else {
            return { type: 'unknown', severity: 'medium' };
        }
    }

    attemptRecovery(error) {
        const { type, severity } = this.classifyError(error.message);

        this.logInfo(`Attempting recovery for ${type} error (${severity} severity)`, error);

        switch (type) {
            case 'network':
                this.recoverNetworkError(error);
                break;
            case 'memory':
                this.recoverMemoryError(error);
                break;
            case 'dependency':
                this.recoverDependencyError(error);
                break;
            case 'file':
                this.recoverFileError(error);
                break;
            default:
                this.logWarning(`No specific recovery strategy for error type: ${type}`);
        }
    }

    recoverNetworkError(error) {
        this.logInfo('Attempting network recovery: clearing caches and retrying');
        // Implementation would include clearing network caches, retrying connections
    }

    recoverMemoryError(error) {
        this.logInfo('Attempting memory recovery: cleaning up and reducing memory usage');

        // Clear error history to reduce memory
        if (this.errorHistory.length > 100) {
            this.errorHistory = this.errorHistory.slice(-50);
        }

        // Force garbage collection if available
        if (global.gc) {
            try {
                global.gc();
                this.logInfo('Garbage collection completed');
            } catch (e) {
                this.logWarning('Garbage collection failed');
            }
        }
    }

    recoverDependencyError(error) {
        this.logInfo('Attempting dependency recovery: checking and installing dependencies');
        // Implementation would include checking for missing dependencies and installing them
    }

    recoverFileError(error) {
        this.logInfo('Attempting file recovery: creating directories and checking permissions');

        // Ensure directories exist
        const directories = [
            path.dirname(this.config.logFile),
            path.join(__dirname, '..', 'logs'),
            path.join(__dirname, '..', 'temp')
        ];

        directories.forEach(dir => {
            if (!fs.existsSync(dir)) {
                try {
                    fs.mkdirSync(dir, { recursive: true });
                    this.logInfo(`Created directory: ${dir}`);
                } catch (e) {
                    this.logError(`Failed to create directory ${dir}: ${e.message}`);
                }
            }
        });
    }

    executeCommand(command, description = '') {
        return new Promise((resolve, reject) => {
            this.logInfo(`Executing command: ${description || command}`);

            exec(command, (error, stdout, stderr) => {
                if (error) {
                    this.handleError('COMMAND_FAILED', `Command failed: ${command}`, {
                        error: error.message,
                        stderr: stderr.toString()
                    });
                    reject(error);
                } else {
                    this.logInfo(`Command succeeded: ${description || command}`, {
                        stdout: stdout.toString().trim()
                    });
                    resolve(stdout.toString().trim());
                }
            });
        });
    }

    withErrorHandling(operation, func, options = {}) {
        const { retries = this.config.maxRetries, context = {} } = options;

        return new Promise(async (resolve, reject) => {
            let attempt = 0;
            let lastError = null;

            while (attempt <= retries) {
                try {
                    const result = await func();

                    if (attempt > 0) {
                        this.logInfo(`Operation succeeded after ${attempt} retries: ${operation}`, context);
                    }

                    resolve(result);
                    return;
                } catch (error) {
                    lastError = error;
                    attempt++;

                    this.handleError('OPERATION_FAILED', `Operation failed (attempt ${attempt}/${retries + 1}): ${operation}`, {
                        error: error.message,
                        attempt,
                        operation,
                        context,
                        stack: error.stack
                    });

                    if (attempt <= retries) {
                        this.logInfo(`Retrying operation in ${this.config.retryDelay}ms...`, { operation, attempt });
                        await this.delay(this.config.retryDelay);
                    }
                }
            }

            this.handleError('OPERATION_EXHAUSTED', `Operation failed after ${retries + 1} attempts: ${operation}`, {
                error: lastError.message,
                operation,
                context,
                retries
            });

            reject(lastError);
        });
    }

    delay(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }

    startMonitoring() {
        if (this.monitoringActive) {
            return;
        }

        this.monitoringActive = true;
        this.logInfo('Starting error monitoring');

        // Monitor system resources every 30 seconds
        this.monitoringInterval = setInterval(() => {
            this.checkSystemHealth();
        }, 30000);

        // Initial health check
        this.checkSystemHealth();
    }

    stopMonitoring() {
        if (!this.monitoringActive) {
            return;
        }

        this.monitoringActive = false;

        if (this.monitoringInterval) {
            clearInterval(this.monitoringInterval);
            this.monitoringInterval = null;
        }

        this.logInfo('Error monitoring stopped');
    }

    async checkSystemHealth() {
        try {
            const health = {
                timestamp: new Date().toISOString(),
                memory: process.memoryUsage(),
                uptime: process.uptime(),
                errorCount: this.errorHistory.length,
                recentErrors: this.errorHistory.slice(-10)
            };

            // Check for critical conditions
            const memoryUsage = health.memory.heapUsed / health.memory.heapTotal;
            if (memoryUsage > 0.9) {
                this.handleError('HIGH_MEMORY_USAGE', `High memory usage detected: ${(memoryUsage * 100).toFixed(1)}%`, health);
                this.recoverMemoryError({ message: 'High memory usage' });
            }

            // Check for error storms (too many errors in short time)
            const recentErrors = this.errorHistory.filter(error => {
                const errorTime = new Date(error.timestamp).getTime();
                const now = Date.now();
                return (now - errorTime) < 60000; // Last minute
            });

            if (recentErrors.length > 10) {
                this.handleError('ERROR_STORM', `Error storm detected: ${recentErrors.length} errors in the last minute`, {
                    errorCount: recentErrors.length,
                    recentErrors: recentErrors.slice(-5)
                });
            }

        } catch (error) {
            this.handleError('HEALTH_CHECK_FAILED', `System health check failed: ${error.message}`);
        }
    }

    getErrorStats() {
        const now = Date.now();
        const lastHour = this.errorHistory.filter(error => {
            const errorTime = new Date(error.timestamp).getTime();
            return (now - errorTime) < 3600000; // Last hour
        });

        const last24Hours = this.errorHistory.filter(error => {
            const errorTime = new Date(error.timestamp).getTime();
            return (now - errorTime) < 86400000; // Last 24 hours
        });

        return {
            totalErrors: this.errorHistory.length,
            lastHour: lastHour.length,
            last24Hours: last24Hours.length,
            monitoringActive: this.monitoringActive,
            config: {
                autoRecovery: this.config.autoRecovery,
                maxRetries: this.config.maxRetries
            }
        };
    }

    getRecentLogs(limit = 100) {
        return this.errorHistory.slice(-limit);
    }

    getDiagnostics() {
        return {
            timestamp: new Date().toISOString(),
            process: {
                pid: process.pid,
                uptime: process.uptime(),
                memoryUsage: process.memoryUsage(),
                version: process.version,
                platform: process.platform
            },
            errorHandler: {
                monitoringActive: this.monitoringActive,
                errorHistoryLength: this.errorHistory.length,
                config: this.config
            },
            services: {
                logFile: this.config.logFile,
                logFileExists: fs.existsSync(this.config.logFile)
            }
        };
    }

    exportLogs(filePath) {
        try {
            const logs = {
                exportTime: new Date().toISOString(),
                config: this.config,
                errorHistory: this.errorHistory,
                diagnostics: this.getDiagnostics()
            };

            fs.writeFileSync(filePath, JSON.stringify(logs, null, 2));
            this.logInfo(`Logs exported to: ${filePath}`);
            return true;
        } catch (error) {
            this.handleError('EXPORT_FAILED', `Failed to export logs: ${error.message}`);
            return false;
        }
    }

    clearLogs() {
        try {
            this.errorHistory = [];

            if (fs.existsSync(this.config.logFile)) {
                fs.unlinkSync(this.config.logFile);
                this.logInfo('Log file cleared');
            }

            return true;
        } catch (error) {
            this.handleError('CLEAR_LOGS_FAILED', `Failed to clear logs: ${error.message}`);
            return false;
        }
    }
}

module.exports = { ElectronErrorHandler };