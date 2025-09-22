import axios from 'axios';
import { EventSourcePolyfill } from 'event-source-polyfill';

// RAG System Types
export interface RAGDocument {
    id: string;
    title: string;
    content: string;
    metadata: {
        source: string;
        type: string;
        size: number;
        created: string;
        modified: string;
        author?: string;
        tags?: string[];
        language?: string;
    };
    chunks: number;
    embedding_provider: string;
    indexed: boolean;
    status: 'processing' | 'indexed' | 'failed' | 'pending';
}

export interface RAGSearchResult {
    id: string;
    document_id: string;
    content: string;
    score: number;
    metadata: {
        chunk_id: string;
        document_title: string;
        source: string;
        relevance_score: number;
        confidence: number;
        position: number;
    };
    highlights: string[];
}

export interface RAGSearchQuery {
    query: string;
    filters?: {
        document_types?: string[];
        sources?: string[];
        date_range?: {
            start: string;
            end: string;
        };
        tags?: string[];
        embedding_providers?: string[];
    };
    search_strategy: 'vector' | 'hybrid' | 'keyword' | 'semantic';
    limit: number;
    offset: number;
    include_highlights: boolean;
    min_score: number;
}

export interface RAGIndex {
    id: string;
    name: string;
    description: string;
    document_count: number;
    total_chunks: number;
    embedding_model: string;
    embedding_dimension: number;
    created: string;
    last_updated: string;
    size_mb: number;
    status: 'active' | 'building' | 'optimizing' | 'error';
    performance_metrics: {
        avg_search_time: number;
        accuracy_score: number;
        recall_score: number;
    };
}

export interface RAGEmbeddingProvider {
    id: string;
    name: string;
    type: 'openai' | 'local' | 'huggingface' | 'cohere' | 'anthropic';
    model: string;
    api_endpoint?: string;
    api_key?: string;
    max_tokens: number;
    dimension: number;
    status: 'connected' | 'disconnected' | 'error';
    last_used: string;
}

export interface RAGConfig {
    embedding: {
        default_provider: string;
        chunk_size: number;
        chunk_overlap: number;
        batch_size: number;
        max_document_size: number;
        supported_formats: string[];
    };
    search: {
        default_strategy: string;
        result_limit: number;
        min_score_threshold: number;
        enable_highlights: boolean;
        enable_semantic_search: boolean;
        cache_results: boolean;
        cache_ttl: number;
    };
    performance: {
        max_concurrent_searches: number;
        index_optimization_interval: number;
        memory_cache_size: number;
        enable_compression: boolean;
        parallel_processing: boolean;
    };
    security: {
        enable_authentication: boolean;
        rate_limit_rpm: number;
        rate_limit_rph: number;
        encrypt_indexes: boolean;
        audit_logging: boolean;
        allowed_file_types: string[];
    };
}

export interface RAGMetrics {
    system: {
        uptime: number;
        memory_usage: number;
        cpu_usage: number;
        disk_usage: number;
        status: 'healthy' | 'warning' | 'error';
    };
    documents: {
        total_count: number;
        indexed_count: number;
        failed_count: number;
        processing_count: number;
        total_size: number;
    };
    search: {
        total_queries: number;
        avg_response_time: number;
        success_rate: number;
        popular_queries: Array<{ query: string; count: number }>;
    };
    performance: {
        avg_indexing_time: number;
        avg_search_time: number;
        cache_hit_rate: number;
        error_rate: number;
    };
}

export interface RAGProcess {
    id: string;
    type: 'indexing' | 'search' | 'optimization' | 'cleanup';
    status: 'running' | 'completed' | 'failed' | 'cancelled';
    progress: number;
    message: string;
    started_at: string;
    estimated_completion?: string;
    details?: any;
}

export class RAGService {
    private baseUrl: string;
    private token: string | null;
    private websocket: WebSocket | null = null;
    private eventSource: EventSource | null = null;
    private reconnectAttempts = 0;
    private maxReconnectAttempts = 5;
    private reconnectDelay = 1000;

    constructor(baseUrl: string = 'http://localhost:8787', token: string | null = null) {
        this.baseUrl = baseUrl.replace(/\/$/, '');
        this.token = token;
        this.initializeWebSocket();
    }

    private async getToken(): Promise<string> {
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

            throw new Error('No token received from backend');
        } catch (error) {
            console.error('Failed to get token:', error);
            throw new Error('Backend not available. Please ensure the service is running.');
        }
    }

    private initializeWebSocket() {
        try {
            const wsUrl = this.baseUrl.replace('http', 'ws') + '/ws/rag';
            this.websocket = new WebSocket(wsUrl);

            this.websocket.onopen = () => {
                console.log('RAG WebSocket connected');
                this.reconnectAttempts = 0;
            };

            this.websocket.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data);
                    this.handleWebSocketMessage(data);
                } catch (error) {
                    console.error('Failed to parse WebSocket message:', error);
                }
            };

            this.websocket.onclose = () => {
                console.log('RAG WebSocket disconnected');
                this.attemptReconnect();
            };

            this.websocket.onerror = (error) => {
                console.error('RAG WebSocket error:', error);
            };
        } catch (error) {
            console.error('Failed to initialize WebSocket:', error);
        }
    }

    private attemptReconnect() {
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
            this.reconnectAttempts++;
            setTimeout(() => {
                console.log(`Attempting to reconnect WebSocket (${this.reconnectAttempts}/${this.maxReconnectAttempts})`);
                this.initializeWebSocket();
            }, this.reconnectDelay * this.reconnectAttempts);
        }
    }

    private handleWebSocketMessage(data: any) {
        // Dispatch custom events for different message types
        window.dispatchEvent(new CustomEvent('rag-update', { detail: data }));

        switch (data.type) {
            case 'document_status':
                window.dispatchEvent(new CustomEvent('rag-document-update', { detail: data }));
                break;
            case 'search_progress':
                window.dispatchEvent(new CustomEvent('rag-search-progress', { detail: data }));
                break;
            case 'system_metrics':
                window.dispatchEvent(new CustomEvent('rag-metrics-update', { detail: data }));
                break;
            case 'process_update':
                window.dispatchEvent(new CustomEvent('rag-process-update', { detail: data }));
                break;
        }
    }

    // System Status and Metrics
    async getSystemStatus(): Promise<RAGMetrics> {
        try {
            const token = await this.getToken();

            const response = await axios.get(`${this.baseUrl}/api/rag/status`, {
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                },
                timeout: 5000
            });

            return response.data;
        } catch (error) {
            console.error('Failed to get RAG system status:', error);
            throw new Error(`Failed to get system status: ${error instanceof Error ? error.message : 'Unknown error'}`);
        }
    }

    async getHealthStatus(): Promise<{
        status: 'healthy' | 'warning' | 'error';
        services: {
            embedding: boolean;
            search: boolean;
            indexing: boolean;
            storage: boolean;
        };
        issues: string[];
    }> {
        try {
            const token = await this.getToken();

            const response = await axios.get(`${this.baseUrl}/api/rag/health`, {
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                },
                timeout: 3000
            });

            return response.data;
        } catch (error) {
            console.error('Failed to get RAG health status:', error);
            return {
                status: 'error',
                services: {
                    embedding: false,
                    search: false,
                    indexing: false,
                    storage: false
                },
                issues: [error instanceof Error ? error.message : 'Unknown error']
            };
        }
    }

    // Document Management
    async uploadDocument(file: File, options?: {
        chunk_size?: number;
        overlap?: number;
        embedding_provider?: string;
        metadata?: any;
    }): Promise<{
        document_id: string;
        message: string;
        process_id: string;
    }> {
        try {
            const token = await this.getToken();

            const formData = new FormData();
            formData.append('file', file);

            if (options) {
                formData.append('options', JSON.stringify(options));
            }

            const response = await axios.post(`${this.baseUrl}/api/rag/documents/upload`, formData, {
                headers: {
                    'Authorization': `Bearer ${token}`,
                },
                timeout: 30000
            });

            return response.data;
        } catch (error) {
            console.error('Failed to upload document:', error);
            throw new Error(`Document upload failed: ${error instanceof Error ? error.message : 'Unknown error'}`);
        }
    }

    async getDocuments(filters?: {
        status?: string;
        type?: string;
        source?: string;
        limit?: number;
        offset?: number;
    }): Promise<{
        documents: RAGDocument[];
        total: number;
        has_more: boolean;
    }> {
        try {
            const token = await this.getToken();

            const params = new URLSearchParams();
            if (filters) {
                Object.entries(filters).forEach(([key, value]) => {
                    if (value !== undefined) {
                        params.append(key, value.toString());
                    }
                });
            }

            const response = await axios.get(`${this.baseUrl}/api/rag/documents?${params.toString()}`, {
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                },
                timeout: 10000
            });

            return response.data;
        } catch (error) {
            console.error('Failed to get documents:', error);
            return {
                documents: [],
                total: 0,
                has_more: false
            };
        }
    }

    async getDocument(documentId: string): Promise<RAGDocument> {
        try {
            const token = await this.getToken();

            const response = await axios.get(`${this.baseUrl}/api/rag/documents/${documentId}`, {
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                },
                timeout: 5000
            });

            return response.data;
        } catch (error) {
            console.error('Failed to get document:', error);
            throw new Error(`Failed to get document: ${error instanceof Error ? error.message : 'Unknown error'}`);
        }
    }

    async deleteDocument(documentId: string): Promise<{ success: boolean; message: string }> {
        try {
            const token = await this.getToken();

            const response = await axios.delete(`${this.baseUrl}/api/rag/documents/${documentId}`, {
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                },
                timeout: 10000
            });

            return response.data;
        } catch (error) {
            console.error('Failed to delete document:', error);
            throw new Error(`Document deletion failed: ${error instanceof Error ? error.message : 'Unknown error'}`);
        }
    }

    async bulkDeleteDocuments(documentIds: string[]): Promise<{
        success: boolean;
        deleted_count: number;
        errors: string[];
    }> {
        try {
            const token = await this.getToken();

            const response = await axios.post(`${this.baseUrl}/api/rag/documents/bulk-delete`, {
                document_ids: documentIds
            }, {
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                },
                timeout: 30000
            });

            return response.data;
        } catch (error) {
            console.error('Failed to bulk delete documents:', error);
            throw new Error(`Bulk deletion failed: ${error instanceof Error ? error.message : 'Unknown error'}`);
        }
    }

    // Search Operations
    async search(query: RAGSearchQuery): Promise<{
        results: RAGSearchResult[];
        total: number;
        query_time: number;
        filters_applied: any;
    }> {
        try {
            const token = await this.getToken();

            const response = await axios.post(`${this.baseUrl}/api/rag/search`, query, {
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                },
                timeout: 15000
            });

            return response.data;
        } catch (error) {
            console.error('RAG search failed:', error);
            return {
                results: [],
                total: 0,
                query_time: 0,
                filters_applied: {}
            };
        }
    }

    async getSearchSuggestions(query: string, limit: number = 5): Promise<string[]> {
        try {
            const token = await this.getToken();

            const response = await axios.get(`${this.baseUrl}/api/rag/search/suggestions`, {
                params: { query, limit },
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                },
                timeout: 5000
            });

            return response.data.suggestions || [];
        } catch (error) {
            console.error('Failed to get search suggestions:', error);
            return [];
        }
    }

    async getSearchHistory(limit: number = 50): Promise<Array<{
        query: string;
        timestamp: string;
        result_count: number;
        query_time: number;
    }>> {
        try {
            const token = await this.getToken();

            const response = await axios.get(`${this.baseUrl}/api/rag/search/history?limit=${limit}`, {
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                },
                timeout: 5000
            });

            return response.data.history || [];
        } catch (error) {
            console.error('Failed to get search history:', error);
            return [];
        }
    }

    // Index Management
    async getIndexes(): Promise<RAGIndex[]> {
        try {
            const token = await this.getToken();

            const response = await axios.get(`${this.baseUrl}/api/rag/indexes`, {
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                },
                timeout: 10000
            });

            return response.data.indexes || [];
        } catch (error) {
            console.error('Failed to get indexes:', error);
            return [];
        }
    }

    async createIndex(options: {
        name: string;
        description?: string;
        embedding_model: string;
        documents?: string[];
    }): Promise<RAGIndex> {
        try {
            const token = await this.getToken();

            const response = await axios.post(`${this.baseUrl}/api/rag/indexes`, options, {
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                },
                timeout: 10000
            });

            return response.data;
        } catch (error) {
            console.error('Failed to create index:', error);
            throw new Error(`Index creation failed: ${error instanceof Error ? error.message : 'Unknown error'}`);
        }
    }

    async optimizeIndex(indexId: string): Promise<{ process_id: string; message: string }> {
        try {
            const token = await this.getToken();

            const response = await axios.post(`${this.baseUrl}/api/rag/indexes/${indexId}/optimize`, {}, {
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                },
                timeout: 5000
            });

            return response.data;
        } catch (error) {
            console.error('Failed to optimize index:', error);
            throw new Error(`Index optimization failed: ${error instanceof Error ? error.message : 'Unknown error'}`);
        }
    }

    // Configuration Management
    async getConfig(): Promise<RAGConfig> {
        try {
            const token = await this.getToken();

            const response = await axios.get(`${this.baseUrl}/api/rag/config`, {
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                },
                timeout: 5000
            });

            return response.data;
        } catch (error) {
            console.error('Failed to get RAG config:', error);
            throw new Error(`Failed to get configuration: ${error instanceof Error ? error.message : 'Unknown error'}`);
        }
    }

    async updateConfig(config: Partial<RAGConfig>): Promise<{ success: boolean; message: string }> {
        try {
            const token = await this.getToken();

            const response = await axios.put(`${this.baseUrl}/api/rag/config`, config, {
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                },
                timeout: 10000
            });

            return response.data;
        } catch (error) {
            console.error('Failed to update RAG config:', error);
            throw new Error(`Configuration update failed: ${error instanceof Error ? error.message : 'Unknown error'}`);
        }
    }

    // Embedding Providers
    async getEmbeddingProviders(): Promise<RAGEmbeddingProvider[]> {
        try {
            const token = await this.getToken();

            const response = await axios.get(`${this.baseUrl}/api/rag/embedding-providers`, {
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                },
                timeout: 5000
            });

            return response.data.providers || [];
        } catch (error) {
            console.error('Failed to get embedding providers:', error);
            return [];
        }
    }

    async testEmbeddingProvider(providerId: string): Promise<{
        success: boolean;
        message: string;
        response_time: number;
    }> {
        try {
            const token = await this.getToken();

            const response = await axios.post(`${this.baseUrl}/api/rag/embedding-providers/${providerId}/test`, {}, {
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                },
                timeout: 15000
            });

            return response.data;
        } catch (error) {
            console.error('Failed to test embedding provider:', error);
            return {
                success: false,
                message: error instanceof Error ? error.message : 'Unknown error',
                response_time: 0
            };
        }
    }

    // Process Management
    async getActiveProcesses(): Promise<RAGProcess[]> {
        try {
            const token = await this.getToken();

            const response = await axios.get(`${this.baseUrl}/api/rag/processes`, {
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                },
                timeout: 5000
            });

            return response.data.processes || [];
        } catch (error) {
            console.error('Failed to get active processes:', error);
            return [];
        }
    }

    async cancelProcess(processId: string): Promise<{ success: boolean; message: string }> {
        try {
            const token = await this.getToken();

            const response = await axios.post(`${this.baseUrl}/api/rag/processes/${processId}/cancel`, {}, {
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                },
                timeout: 5000
            });

            return response.data;
        } catch (error) {
            console.error('Failed to cancel process:', error);
            throw new Error(`Process cancellation failed: ${error instanceof Error ? error.message : 'Unknown error'}`);
        }
    }

    // Analytics and Reporting
    async getAnalytics(timeRange: '1h' | '24h' | '7d' | '30d' = '24h'): Promise<{
        search_volume: Array<{ timestamp: string; count: number }>;
        response_times: Array<{ timestamp: string; time: number }>;
        error_rates: Array<{ timestamp: string; rate: number }>;
        popular_queries: Array<{ query: string; count: number }>;
        document_types: Array<{ type: string; count: number }>;
    }> {
        try {
            const token = await this.getToken();

            const response = await axios.get(`${this.baseUrl}/api/rag/analytics?time_range=${timeRange}`, {
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                },
                timeout: 10000
            });

            return response.data;
        } catch (error) {
            console.error('Failed to get analytics:', error);
            return {
                search_volume: [],
                response_times: [],
                error_rates: [],
                popular_queries: [],
                document_types: []
            };
        }
    }

    async exportData(type: 'documents' | 'searches' | 'analytics', format: 'json' | 'csv' = 'json'): Promise<Blob> {
        try {
            const token = await this.getToken();

            const response = await axios.get(`${this.baseUrl}/api/rag/export/${type}`, {
                params: { format },
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                },
                responseType: 'blob',
                timeout: 30000
            });

            return response.data;
        } catch (error) {
            console.error('Failed to export data:', error);
            throw new Error(`Data export failed: ${error instanceof Error ? error.message : 'Unknown error'}`);
        }
    }

    // Event Stream for Real-time Updates
    subscribeToUpdates(callback: (data: any) => void): () => void {
        const handleUpdate = (event: CustomEvent) => {
            callback(event.detail);
        };

        window.addEventListener('rag-update', handleUpdate as EventListener);
        window.addEventListener('rag-document-update', handleUpdate as EventListener);
        window.addEventListener('rag-search-progress', handleUpdate as EventListener);
        window.addEventListener('rag-metrics-update', handleUpdate as EventListener);
        window.addEventListener('rag-process-update', handleUpdate as EventListener);

        return () => {
            window.removeEventListener('rag-update', handleUpdate as EventListener);
            window.removeEventListener('rag-document-update', handleUpdate as EventListener);
            window.removeEventListener('rag-search-progress', handleUpdate as EventListener);
            window.removeEventListener('rag-metrics-update', handleUpdate as EventListener);
            window.removeEventListener('rag-process-update', handleUpdate as EventListener);
        };
    }

    // Utility Methods
    async testConnection(): Promise<boolean> {
        try {
            await this.getHealthStatus();
            return true;
        } catch (error) {
            return false;
        }
    }

    setBaseUrl(url: string) {
        this.baseUrl = url.replace(/\/$/, '');
        this.token = null;
        if (this.websocket) {
            this.websocket.close();
        }
        this.initializeWebSocket();
    }

    setToken(token: string | null) {
        this.token = token;
    }

    // Cleanup
    cleanup() {
        if (this.websocket) {
            this.websocket.close();
            this.websocket = null;
        }
        if (this.eventSource) {
            this.eventSource.close();
            this.eventSource = null;
        }
    }
}

// Export singleton instance
export const ragService = new RAGService();

// Export types for use in components
export type {
    RAGDocument,
    RAGSearchResult,
    RAGSearchQuery,
    RAGIndex,
    RAGEmbeddingProvider,
    RAGConfig,
    RAGMetrics,
    RAGProcess
};