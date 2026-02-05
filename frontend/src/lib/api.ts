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
}

interface ModelInfo {
    loaded: boolean;
    accuracy: number;
    n_features: number;
    classes: string[];
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
                    data: data,
                    error: data.detail || 'Request failed',
                };
            }

            return {
                success: true,
                data: data.data || data,
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
    async healthCheck(): Promise<ApiResponse<{ status: string; message: string }>> {
        return this.request('/health');
    }

    // Dashboard stats
    async getStats(): Promise<ApiResponse<DashboardStats>> {
        return this.request('/api/stats');
    }

    // Get recent alerts
    async getAlerts(limit: number = 50): Promise<ApiResponse<Alert[]>> {
        try {
            const response = await fetch(`${this.baseUrl}/api/alerts?limit=${limit}`, {
                headers: { 'Content-Type': 'application/json' },
            });
            const json = await response.json();

            if (!response.ok) {
                return { success: false, data: [], error: json.detail || 'Failed to fetch alerts' };
            }

            // Handle nested response: {data: {alerts: [...], total: N}}
            const alerts = json.data?.alerts || json.alerts || [];
            return { success: true, data: alerts };
        } catch (error) {
            return { success: false, data: [], error: error instanceof Error ? error.message : 'Network error' };
        }
    }

    // Get attack distribution
    async getAttackDistribution(): Promise<ApiResponse<AttackDistribution[]>> {
        return this.request('/api/stats/distribution');
    }

    // Single flow classification
    async classifyFlow(features: Record<string, number>): Promise<ApiResponse<ClassificationResult>> {
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
};
