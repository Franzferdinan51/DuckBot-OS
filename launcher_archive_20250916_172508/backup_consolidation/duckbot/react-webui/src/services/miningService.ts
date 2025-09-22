import axios from 'axios';

export class MiningService {
    private baseUrl: string;
    private token: string | null;

    constructor(baseUrl: string = 'http://localhost:8787', token: string | null = null) {
        this.baseUrl = baseUrl.replace(/\/$/, ''); // Remove trailing slash
        this.token = token;
    }

    async setToken(token: string | null) {
        this.token = token;
    }

    private async getHeaders() {
        if (this.token) {
            return {
                'Authorization': `Bearer ${this.token}`,
                'Content-Type': 'application/json'
            };
        }
        return {
            'Content-Type': 'application/json'
        };
    }

    async startMining(software?: string, algorithm?: string, coin?: string, intensity?: number): Promise<any> {
        try {
            const response = await axios.post(`${this.baseUrl}/api/mining/start`, {
                software,
                algorithm,
                coin,
                intensity
            }, {
                headers: await this.getHeaders(),
                timeout: 10000
            });

            return response.data;
        } catch (error: any) {
            console.error('Failed to start mining:', error);
            throw new Error(`Mining start failed: ${error.response?.data?.error || error.message}`);
        }
    }

    async stopMining(): Promise<any> {
        try {
            const response = await axios.post(`${this.baseUrl}/api/mining/stop`, {}, {
                headers: await this.getHeaders(),
                timeout: 10000
            });

            return response.data;
        } catch (error: any) {
            console.error('Failed to stop mining:', error);
            throw new Error(`Mining stop failed: ${error.response?.data?.error || error.message}`);
        }
    }

    async getMiningStatus(): Promise<any> {
        try {
            const response = await axios.get(`${this.baseUrl}/api/mining/status`, {
                headers: await this.getHeaders(),
                timeout: 10000
            });

            return response.data;
        } catch (error: any) {
            console.error('Failed to get mining status:', error);
            throw new Error(`Mining status check failed: ${error.response?.data?.error || error.message}`);
        }
    }

    async optimizeMining(): Promise<any> {
        try {
            const response = await axios.post(`${this.baseUrl}/api/mining/optimize`, {}, {
                headers: await this.getHeaders(),
                timeout: 15000
            });

            return response.data;
        } catch (error: any) {
            console.error('Failed to optimize mining:', error);
            throw new Error(`Mining optimization failed: ${error.response?.data?.error || error.message}`);
        }
    }

    async switchMiner(software: string): Promise<any> {
        try {
            const response = await axios.post(`${this.baseUrl}/api/mining/switch`, {
                software
            }, {
                headers: await this.getHeaders(),
                timeout: 10000
            });

            return response.data;
        } catch (error: any) {
            console.error('Failed to switch miner:', error);
            throw new Error(`Miner switch failed: ${error.response?.data?.error || error.message}`);
        }
    }

    async getProfitabilityData(): Promise<any> {
        try {
            const response = await axios.get(`${this.baseUrl}/api/mining/profitability`, {
                headers: await this.getHeaders(),
                timeout: 10000
            });

            return response.data;
        } catch (error: any) {
            console.error('Failed to get profitability data:', error);
            throw new Error(`Profitability data fetch failed: ${error.response?.data?.error || error.message}`);
        }
    }
}