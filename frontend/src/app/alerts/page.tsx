"use client";

import { useState, useEffect, useCallback } from "react";
import { Filter, Search, AlertTriangle, AlertCircle, Info, CheckCircle, RefreshCw } from "lucide-react";
import Navigation from "@/components/Navigation";
import { api, Alert } from "@/lib/api";
import styles from "./page.module.css";

// Fallback mock data when API is unavailable
const fallbackAlerts: Alert[] = [
    {
        id: "1",
        type: "DDoS",
        severity: "critical",
        source_ip: "192.168.1.105",
        destination_ip: "10.0.0.50",
        confidence: 0.95,
        timestamp: new Date(Date.now() - 2 * 60000).toISOString(),
        status: "active",
    },
    {
        id: "2",
        type: "PortScan",
        severity: "high",
        source_ip: "192.168.1.42",
        destination_ip: "10.0.0.0/24",
        confidence: 0.89,
        timestamp: new Date(Date.now() - 5 * 60000).toISOString(),
        status: "active",
    },
    {
        id: "3",
        type: "DoS Hulk",
        severity: "high",
        source_ip: "192.168.2.15",
        destination_ip: "10.0.0.80",
        confidence: 0.92,
        timestamp: new Date(Date.now() - 12 * 60000).toISOString(),
        status: "investigating",
    },
    {
        id: "4",
        type: "Bot",
        severity: "medium",
        source_ip: "192.168.1.200",
        destination_ip: "external",
        confidence: 0.78,
        timestamp: new Date(Date.now() - 30 * 60000).toISOString(),
        status: "resolved",
    },
    {
        id: "5",
        type: "SQL Injection",
        severity: "critical",
        source_ip: "192.168.3.50",
        destination_ip: "10.0.0.100",
        confidence: 0.97,
        timestamp: new Date(Date.now() - 60 * 60000).toISOString(),
        status: "resolved",
    },
];

const severityIcons = {
    critical: AlertTriangle,
    high: AlertCircle,
    medium: Info,
    low: CheckCircle,
};

function formatTime(timestamp: string): string {
    const date = new Date(timestamp);
    return date.toLocaleString();
}

export default function AlertsPage() {
    const [alerts, setAlerts] = useState<Alert[]>(fallbackAlerts);
    const [isLoading, setIsLoading] = useState(true);
    const [isRefreshing, setIsRefreshing] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [filter, setFilter] = useState<string>("all");
    const [searchQuery, setSearchQuery] = useState("");

    const fetchAlerts = useCallback(async () => {
        try {
            const response = await api.getAlerts(50);
            if (response.success && response.data.length > 0) {
                setAlerts(response.data);
                setError(null);
            } else if (!response.success) {
                setError("Failed to connect to backend. Showing demo data.");
            }
        } catch (err) {
            setError("Failed to connect to backend. Showing demo data.");
            console.error("API Error:", err);
        }
    }, []);

    const handleRefresh = async () => {
        setIsRefreshing(true);
        await fetchAlerts();
        setIsRefreshing(false);
    };

    useEffect(() => {
        const init = async () => {
            await fetchAlerts();
            setIsLoading(false);
        };
        init();
    }, [fetchAlerts]);

    const filteredAlerts = alerts.filter((alert) => {
        if (filter !== "all" && alert.severity !== filter) return false;
        if (searchQuery && !alert.type.toLowerCase().includes(searchQuery.toLowerCase())) {
            return false;
        }
        return true;
    });

    if (isLoading) {
        return (
            <>
                <Navigation />
                <main className={styles.main}>
                    <div className={styles.loading}>Loading alerts...</div>
                </main>
            </>
        );
    }

    return (
        <>
            <Navigation />
            <main className={styles.main}>
                <div className={styles.container}>
                    <header className={styles.header}>
                        <div className={styles.headerContent}>
                            <div>
                                <h1 className={styles.title}>Security Alerts</h1>
                                <p className={styles.subtitle}>
                                    View and manage detected network threats
                                </p>
                            </div>
                            <button
                                className={styles.refreshBtn}
                                onClick={handleRefresh}
                                disabled={isRefreshing}
                            >
                                <RefreshCw size={18} className={isRefreshing ? styles.spinning : ""} />
                                Refresh
                            </button>
                        </div>
                        {error && <div className={styles.errorBanner}>{error}</div>}
                    </header>

                    <div className={styles.controls}>
                        <div className={styles.searchBox}>
                            <Search size={18} className={styles.searchIcon} />
                            <input
                                type="text"
                                placeholder="Search alerts..."
                                value={searchQuery}
                                onChange={(e) => setSearchQuery(e.target.value)}
                                className={styles.searchInput}
                            />
                        </div>

                        <div className={styles.filterGroup}>
                            <Filter size={18} />
                            <select
                                value={filter}
                                onChange={(e) => setFilter(e.target.value)}
                                className={styles.filterSelect}
                            >
                                <option value="all">All Severity</option>
                                <option value="critical">Critical</option>
                                <option value="high">High</option>
                                <option value="medium">Medium</option>
                                <option value="low">Low</option>
                            </select>
                        </div>
                    </div>

                    <div className={styles.alertsTable}>
                        <div className={styles.tableHeader}>
                            <span>Type</span>
                            <span>Severity</span>
                            <span>Source</span>
                            <span>Destination</span>
                            <span>Confidence</span>
                            <span>Status</span>
                            <span>Time</span>
                        </div>

                        {filteredAlerts.length === 0 ? (
                            <div className={styles.emptyState}>
                                No alerts found matching your criteria
                            </div>
                        ) : (
                            filteredAlerts.map((alert) => {
                                const Icon = severityIcons[alert.severity];
                                return (
                                    <div key={alert.id} className={`${styles.tableRow} ${styles[alert.severity]}`}>
                                        <span className={styles.typeCell}>
                                            <Icon size={16} />
                                            {alert.type}
                                        </span>
                                        <span className={`${styles.badge} ${styles[alert.severity]}`}>
                                            {alert.severity}
                                        </span>
                                        <span>{alert.source_ip}</span>
                                        <span>{alert.destination_ip}</span>
                                        <span>{Math.round(alert.confidence * 100)}%</span>
                                        <span className={`${styles.status} ${styles[alert.status]}`}>
                                            {alert.status}
                                        </span>
                                        <span className={styles.time}>{formatTime(alert.timestamp)}</span>
                                    </div>
                                );
                            })
                        )}
                    </div>
                </div>
            </main>
        </>
    );
}
