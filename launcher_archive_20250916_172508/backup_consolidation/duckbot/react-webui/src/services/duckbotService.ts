import axios from 'axios';
import type { DuckBotResponse, ChatMessage } from '../types';
import { MiningService } from './miningService';

export class DuckBotService {
    private baseUrl: string;
    private token: string | null;

    constructor(baseUrl: string = 'http://localhost:8787', token: string | null = null) {
        this.baseUrl = baseUrl.replace(/\/$/, ''); // Remove trailing slash
        this.token = token;
    }

    async getToken(): Promise<string> {
        if (this.token) {
            return this.token;
        }

        try {
            const response = await axios.get(`${this.baseUrl}/token`, {
                timeout: 5000
            });
            
            if (response.data && response.data.token) {
                this.token = response.data.token;
                return this.token;
            }
            
            throw new Error('No token received from DuckBot backend');
        } catch (error) {
            console.error('Failed to get DuckBot token:', error);
            throw new Error('DuckBot backend not available. Please ensure DuckBot WebUI is running on port 8787.');
        }
    }

    async chat(message: string, model: string = 'auto'): Promise<string> {
        try {
            const token = await this.getToken();
            
            const response = await axios.post(`${this.baseUrl}/api/chat`, {
                message: message,
                model: model,
                stream: false
            }, {
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                },
                timeout: 30000
            });

            if (response.data && response.data.response) {
                return response.data.response;
            } else if (response.data && typeof response.data === 'string') {
                return response.data;
            } else {
                throw new Error('Invalid response format from DuckBot');
            }
        } catch (error: any) {
            console.error('DuckBot chat error:', error);
            
            if (error.response) {
                const status = error.response.status;
                if (status === 401) {
                    // Token expired, try to refresh
                    this.token = null;
                    return this.chat(message, model);
                } else if (status === 503) {
                    throw new Error('DuckBot AI services are temporarily unavailable. Please try again.');
                }
                throw new Error(`DuckBot error: ${error.response.data?.error || 'Unknown error'}`);
            } else if (error.code === 'ECONNREFUSED') {
                throw new Error('Cannot connect to DuckBot backend. Please ensure DuckBot WebUI is running.');
            } else {
                throw new Error(`Network error: ${error.message}`);
            }
        }
    }

    async getAvailableModels(): Promise<string[]> {
        try {
            const token = await this.getToken();
            
            const response = await axios.get(`${this.baseUrl}/api/models`, {
                headers: {
                    'Authorization': `Bearer ${token}`
                },
                timeout: 10000
            });

            if (response.data && Array.isArray(response.data)) {
                return response.data;
            }
            
            // Fallback to default models
            return ['auto', 'qwen', 'reasoning', 'code'];
        } catch (error) {
            console.error('Failed to get DuckBot models:', error);
            // Return default models as fallback
            return ['auto', 'qwen', 'reasoning', 'code'];
        }
    }

    async getSystemStatus(): Promise<any> {
        try {
            const token = await this.getToken();
            
            const response = await axios.get(`${this.baseUrl}/api/system-status`, {
                headers: {
                    'Authorization': `Bearer ${token}`
                },
                timeout: 5000
            });

            return response.data;
        } catch (error) {
            console.error('Failed to get DuckBot status:', error);
            return { status: 'unknown', error: error instanceof Error ? error.message : 'Unknown error' };
        }
    }

    // VibeVoice TTS Integration
    async generateVoiceScript(text: string, voice: string = 'en-alice'): Promise<string> {
        try {
            const token = await this.getToken();
            
            const response = await axios.post(`${this.baseUrl}/api/voice/generate`, {
                text: text,
                voice: voice,
                preset: 'single'
            }, {
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                },
                timeout: 30000
            });

            return response.data.audio_url || response.data.message;
        } catch (error) {
            console.error('VibeVoice generation failed:', error);
            throw new Error(`Voice generation failed: ${error instanceof Error ? error.message : 'Unknown error'}`);
        }
    }

    // ComfyUI Workflow Integration
    async generateImage(prompt: string, model: string = 'auto'): Promise<any> {
        try {
            const token = await this.getToken();
            
            const response = await axios.post(`${this.baseUrl}/api/generate`, {
                prompt: prompt,
                model: model,
                type: 'image'
            }, {
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                },
                timeout: 60000
            });

            return response.data;
        } catch (error) {
            console.error('Image generation failed:', error);
            throw new Error(`Image generation failed: ${error instanceof Error ? error.message : 'Unknown error'}`);
        }
    }

    // Cost Tracking
    async getCostSummary(days: number = 7): Promise<any> {
        try {
            const token = await this.getToken();
            
            const response = await axios.get(`${this.baseUrl}/api/cost_summary?days=${days}`, {
                headers: {
                    'Authorization': `Bearer ${token}`
                },
                timeout: 10000
            });

            return response.data;
        } catch (error) {
            console.error('Failed to get cost summary:', error);
            return { error: error instanceof Error ? error.message : 'Unknown error' };
        }
    }

    // RAG Integration
    async searchRAG(query: string): Promise<any> {
        try {
            const token = await this.getToken();
            
            const response = await axios.post(`${this.baseUrl}/rag/search`, {
                query: query,
                limit: 5
            }, {
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                },
                timeout: 15000
            });

            return response.data;
        } catch (error) {
            console.error('RAG search failed:', error);
            return { results: [], error: error instanceof Error ? error.message : 'Unknown error' };
        }
    }

    // Service Management
    async getServices(): Promise<any> {
        try {
            const token = await this.getToken();
            
            const response = await axios.get(`${this.baseUrl}/api/services`, {
                headers: {
                    'Authorization': `Bearer ${token}`
                },
                timeout: 10000
            });

            return response.data;
        } catch (error) {
            console.error('Failed to get services:', error);
            return { services: [], error: error instanceof Error ? error.message : 'Unknown error' };
        }
    }

    async controlService(service: string, action: 'start' | 'stop' | 'restart'): Promise<any> {
        try {
            const token = await this.getToken();
            
            const response = await axios.post(`${this.baseUrl}/api/services/${service}/${action}`, {}, {
                headers: {
                    'Authorization': `Bearer ${token}`
                },
                timeout: 30000
            });

            return response.data;
        } catch (error) {
            console.error(`Service ${action} failed:`, error);
            throw new Error(`Service ${action} failed: ${error instanceof Error ? error.message : 'Unknown error'}`);
        }
    }

    // Queue Management
    async getQueueStatus(): Promise<any> {
        try {
            const token = await this.getToken();
            
            const response = await axios.get(`${this.baseUrl}/api/queue/status`, {
                headers: {
                    'Authorization': `Bearer ${token}`
                },
                timeout: 5000
            });

            return response.data;
        } catch (error) {
            console.error('Failed to get queue status:', error);
            return { queue_size: 0, error: error instanceof Error ? error.message : 'Unknown error' };
        }
    }

    // Action Logs
    async getActionLogs(limit: number = 50): Promise<any> {
        try {
            const token = await this.getToken();
            
            const response = await axios.get(`${this.baseUrl}/api/action-logs?limit=${limit}`, {
                headers: {
                    'Authorization': `Bearer ${token}`
                },
                timeout: 10000
            });

            return response.data;
        } catch (error) {
            console.error('Failed to get action logs:', error);
            return { logs: [], error: error instanceof Error ? error.message : 'Unknown error' };
        }
    }

    async testConnection(): Promise<boolean> {
        try {
            await this.getToken();
            return true;
        } catch (error) {
            return false;
        }
    }

    setBaseUrl(url: string) {
        this.baseUrl = url.replace(/\/$/, '');
        this.token = null; // Reset token when changing URL
    }

    setToken(token: string | null) {
        this.token = token;
    }
}

// LM Studio Service
export class LMStudioService {
    private baseUrl: string;

    constructor(baseUrl: string = 'http://localhost:1234') {
        this.baseUrl = baseUrl.replace(/\/$/, '');
    }

    async chat(message: string, model?: string): Promise<string> {
        try {
            // First, get available models if no model specified
            if (!model) {
                const models = await this.getAvailableModels();
                if (models.length === 0) {
                    throw new Error('No models loaded in LM Studio');
                }
                model = models[0].id; // Use first available model
            }

            const response = await axios.post(`${this.baseUrl}/v1/chat/completions`, {
                model: model,
                messages: [{ role: 'user', content: message }],
                temperature: 0.7,
                max_tokens: 2000
            }, {
                headers: {
                    'Content-Type': 'application/json'
                },
                timeout: 30000
            });

            if (response.data && response.data.choices && response.data.choices[0]) {
                return response.data.choices[0].message.content;
            }

            throw new Error('Invalid response from LM Studio');
        } catch (error: any) {
            console.error('LM Studio error:', error);
            
            if (error.code === 'ECONNREFUSED') {
                throw new Error('Cannot connect to LM Studio. Please ensure LM Studio is running with local server enabled.');
            }
            
            throw new Error(`LM Studio error: ${error.message}`);
        }
    }

    async getAvailableModels(): Promise<any[]> {
        try {
            const response = await axios.get(`${this.baseUrl}/v1/models`, {
                timeout: 5000
            });

            if (response.data && Array.isArray(response.data.data)) {
                return response.data.data;
            }

            return [];
        } catch (error) {
            console.error('Failed to get LM Studio models:', error);
            return [];
        }
    }

    async testConnection(): Promise<boolean> {
        try {
            const models = await this.getAvailableModels();
            return models.length > 0;
        } catch (error) {
            return false;
        }
    }

    setBaseUrl(url: string) {
        this.baseUrl = url.replace(/\/$/, '');
    }
}

// OpenRouter Service (keeping as fallback option)
export class OpenRouterService {
    private apiKey: string;

    constructor(apiKey: string) {
        this.apiKey = apiKey;
    }

    async chat(message: string, model: string = 'google/gemma-2-9b-it:free'): Promise<string> {
        if (!this.apiKey) {
            throw new Error('OpenRouter API key not configured');
        }

        try {
            const response = await axios.post('https://openrouter.ai/api/v1/chat/completions', {
                model: model,
                messages: [{ role: 'user', content: message }]
            }, {
                headers: {
                    'Authorization': `Bearer ${this.apiKey}`,
                    'Content-Type': 'application/json',
                    'HTTP-Referer': 'https://duckbot-clippy.local',
                    'X-Title': 'DuckBot Clippy Assistant'
                },
                timeout: 30000
            });

            if (response.data && response.data.choices && response.data.choices[0]) {
                return response.data.choices[0].message.content;
            }

            throw new Error('Invalid response from OpenRouter');
        } catch (error: any) {
            console.error('OpenRouter error:', error);
            
            if (error.response) {
                const errorData = error.response.data;
                throw new Error(`OpenRouter error: ${errorData?.error?.message || 'Unknown error'}`);
            }
            
            throw new Error(`OpenRouter network error: ${error.message}`);
        }
    }

    async getAvailableModels(): Promise<any[]> {
        try {
            const response = await axios.get('https://openrouter.ai/api/v1/models');
            
            if (response.data && response.data.data) {
                // Filter for free models
                return response.data.data.filter((model: any) => 
                    model?.pricing?.prompt === "0" && model?.pricing?.completion === "0"
                );
            }
            
            return [];
        } catch (error) {
            console.error('Failed to get OpenRouter models:', error);
            return [];
        }
    }

    setApiKey(apiKey: string) {
        this.apiKey = apiKey;
    }

    testConnection(): Promise<boolean> {
        return new Promise((resolve) => {
            if (!this.apiKey) {
                resolve(false);
                return;
            }
            // Simple test - just check if API key format is valid
            resolve(this.apiKey.length > 10);
        });
    }
}

// Main AI service that routes to appropriate provider
export class AIService {
    private duckbot: DuckBotService;
    private lmstudio: LMStudioService;
    private openrouter: OpenRouterService;
    private mining: MiningService;

    constructor() {
        this.duckbot = new DuckBotService();
        this.lmstudio = new LMStudioService();
        this.openrouter = new OpenRouterService('');
        this.mining = new MiningService();
    }

    async chat(message: string, provider: 'duckbot' | 'lmstudio' | 'openrouter', model?: string): Promise<string> {
        switch (provider) {
            case 'duckbot':
                return await this.duckbot.chat(message, model);
            case 'lmstudio':
                return await this.lmstudio.chat(message, model);
            case 'openrouter':
                return await this.openrouter.chat(message, model);
            default:
                throw new Error(`Unknown provider: ${provider}`);
        }
    }

    getDuckBotService(): DuckBotService {
        return this.duckbot;
    }

    getLMStudioService(): LMStudioService {
        return this.lmstudio;
    }

    getOpenRouterService(): OpenRouterService {
        return this.openrouter;
    }

    getMiningService(): MiningService {
        return this.mining;
    }

    async testAllConnections(): Promise<{ duckbot: boolean; lmstudio: boolean; openrouter: boolean }> {
        const [duckbot, lmstudio, openrouter] = await Promise.all([
            this.duckbot.testConnection(),
            this.lmstudio.testConnection(),
            this.openrouter.testConnection()
        ]);

        return { duckbot, lmstudio, openrouter };
    }
}