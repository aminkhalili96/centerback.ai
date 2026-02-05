/**
 * CenterBack.AI - API Client
 * Handles all communication with the FastAPI backend
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

interface ApiResponse<T> {
    success: boolean;
    data: T;
    error?: string;
}

interface BackendEnvelope<T> {
    success: boolean;
    data: T;
    message?: string;
}

interface ClassificationResult {
    prediction: string;
    confidence: number;
    is_threat: boolean;
}

interface BatchClassificationResult {
    total: number;
    benign: number;
    threats: number;
    results: ClassificationResult[];
}

interface DashboardStats {
    total_flows: number;
    threats_detected: number;
    benign_flows: number;
    critical_alerts: number;
    model_accuracy: number;
    model_loaded?: boolean;
    last_updated?: string;
}

interface Alert {
    id: string;
    type: string;
    severity: 'critical' | 'high' | 'medium' | 'low';
    source_ip: string;
    destination_ip: string;
    confidence: number;
    timestamp: string;
    status: string;
}

interface AttackDistribution {
    type: string;
    count: number;
    percentage?: number;
}

interface ModelInfo {
    loaded: boolean;
    accuracy: number;
    accuracy_pct?: number | null;
    n_features: number;
    classes: string[];
}

interface AlertsApiData {
    alerts: Alert[];
    total: number;
}

interface AttackDistributionApiData {
    distribution: AttackDistribution[];
    total_threats: number;
}

class ApiClient {
    private baseUrl: string;

    constructor(baseUrl: string = API_BASE_URL) {
        this.baseUrl = baseUrl;
    }

    private async request<T>(
        endpoint: string,
        options: RequestInit = {}
    ): Promise<ApiResponse<T>> {
        try {
            const response = await fetch(`${this.baseUrl}${endpoint}`, {
                ...options,
                headers: {
                    'Content-Type': 'application/json',
                    ...options.headers,
                },
            });

            const data = await response.json();

            if (!response.ok) {
                return {
                    success: false,
                    data: data as T,
                    error: data.detail || data.message || 'Request failed',
                };
            }

            if (data && typeof data === 'object' && 'success' in data && 'data' in data) {
                const envelope = data as BackendEnvelope<T>;
                return { success: true, data: envelope.data };
            }

            return {
                success: true,
                data: data as T,
            };
        } catch (error) {
            return {
                success: false,
                data: {} as T,
                error: error instanceof Error ? error.message : 'Network error',
            };
        }
    }

    // Health check
    async healthCheck(): Promise<ApiResponse<{ status: string; service: string }>> {
        return this.request('/health');
    }

    // Dashboard stats
    async getStats(): Promise<ApiResponse<DashboardStats>> {
        return this.request('/api/stats');
    }

    // Get recent alerts
    async getAlerts(limit: number = 50): Promise<ApiResponse<Alert[]>> {
        const res = await this.request<AlertsApiData>(`/api/alerts?limit=${limit}`);
        if (!res.success) {
            return { success: false, data: [], error: res.error };
        }
        return { success: true, data: res.data.alerts };
    }

    // Get attack distribution
    async getAttackDistribution(): Promise<ApiResponse<AttackDistribution[]>> {
        const res = await this.request<AttackDistributionApiData>('/api/stats/attacks');
        if (!res.success) {
            return { success: false, data: [], error: res.error };
        }
        return { success: true, data: res.data.distribution };
    }

    // Single flow classification
    async classifyFlow(features: number[]): Promise<ApiResponse<ClassificationResult>> {
        return this.request('/api/classify', {
            method: 'POST',
            body: JSON.stringify({ features }),
        });
    }

    // Batch classification from CSV file
    async classifyBatch(file: File): Promise<ApiResponse<BatchClassificationResult>> {
        const formData = new FormData();
        formData.append('file', file);

        try {
            const response = await fetch(`${this.baseUrl}/api/classify/batch`, {
                method: 'POST',
                body: formData,
            });

            const data = await response.json();

            if (!response.ok) {
                return {
                    success: false,
                    data: data,
                    error: data.detail || 'Classification failed',
                };
            }

            return {
                success: true,
                data: data.data || data,
            };
        } catch (error) {
            return {
                success: false,
                data: {} as BatchClassificationResult,
                error: error instanceof Error ? error.message : 'Network error',
            };
        }
    }

    // Get model info
    async getModelInfo(): Promise<ApiResponse<ModelInfo>> {
        return this.request('/api/model/info');
    }

    // Get dataset info
    async getDatasetInfo(): Promise<ApiResponse<DatasetInfo>> {
        return this.request('/api/dataset/info');
    }

    // Get dataset preview
    async getDatasetPreview(rows: number = 20): Promise<ApiResponse<DatasetPreview>> {
        return this.request(`/api/dataset/preview?rows=${rows}`);
    }

    // Classify sample dataset
    async classifySample(): Promise<ApiResponse<BatchClassificationResult>> {
        return this.request('/api/classify/sample', { method: 'POST' });
    }

    // Get session stats
    async getSessionStats(): Promise<ApiResponse<SessionStats>> {
        return this.request('/api/stats/session');
    }

    // Reset session stats
    async resetSessionStats(): Promise<ApiResponse<null>> {
        return this.request('/api/stats/session/reset', { method: 'POST' });
    }
}

// Additional types for dataset
interface DatasetInfo {
    name: string;
    description: string;
    rows: number;
    features: number;
    attack_types: { name: string; description: string }[];
    file_exists: boolean;
}

interface DatasetPreview {
    columns: string[];
    rows: (string | number)[][];
    total_rows: number;
    preview_rows: number;
}

interface SessionStats {
    has_data: boolean;
    total_flows: number;
    threats_detected: number;
    benign_flows: number;
    critical_alerts: number;
    attack_distribution: AttackDistribution[];
    model_accuracy: number | null;
    started_at: string | null;
    last_updated: string | null;
}

// Export singleton instance
export const api = new ApiClient();

// Export types
export type {
    ApiResponse,
    ClassificationResult,
    BatchClassificationResult,
    DashboardStats,
    Alert,
    AttackDistribution,
    ModelInfo,
    DatasetInfo,
    DatasetPreview,
    SessionStats,
};
