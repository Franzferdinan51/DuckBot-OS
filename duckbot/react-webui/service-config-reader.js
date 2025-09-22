const fs = require('fs');
const path = require('path');

/**
 * Service Configuration Reader
 * Reads service configuration from the orchestrator and provides
 * port and URL information to the Electron app
 */
class ServiceConfigReader {
    constructor() {
        this.config = null;
        this.configFile = path.join(__dirname, 'services_config.json');
        this.loadConfig();
    }

    loadConfig() {
        try {
            if (fs.existsSync(this.configFile)) {
                const configData = fs.readFileSync(this.configFile, 'utf8');
                this.config = JSON.parse(configData);
                console.log('Service configuration loaded successfully');
            } else {
                console.warn('Service configuration file not found, using defaults');
                this.config = this.getDefaultConfig();
            }
        } catch (error) {
            console.error('Error loading service configuration:', error);
            this.config = this.getDefaultConfig();
        }
    }

    getDefaultConfig() {
        return {
            services: {
                mcp_server: {
                    port: 8791,
                    url: 'http://127.0.0.1:8791'
                },
                react_server: {
                    port: 3000,
                    url: 'http://127.0.0.1:3000'
                },
                webui_backend: {
                    port: 8787,
                    url: 'http://127.0.0.1:8787'
                }
            },
            timestamp: Date.now()
        };
    }

    getMCPServerConfig() {
        return this.config.services.mcp_server;
    }

    getReactServerConfig() {
        return this.config.services.react_server;
    }

    getWebUIBackendConfig() {
        return this.config.services.webui_backend;
    }

    getMCPPort() {
        return this.config.services.mcp_server.port;
    }

    getReactPort() {
        return this.config.services.react_server.port;
    }

    getWebUIPort() {
        return this.config.services.webui_backend.port;
    }

    getMCPUrl() {
        return this.config.services.mcp_server.url;
    }

    getReactUrl() {
        return this.config.services.react_server.url;
    }

    getWebUIUrl() {
        return this.config.services.webui_backend.url;
    }

    isConfigValid() {
        return this.config && this.config.services &&
               this.config.services.mcp_server &&
               this.config.services.react_server &&
               this.config.services.webui_backend;
    }

    reloadConfig() {
        this.loadConfig();
    }
}

// Export singleton instance
module.exports = new ServiceConfigReader();