"use client";

import { useState } from "react";
import { Filter, Search, AlertTriangle, AlertCircle, Info, CheckCircle } from "lucide-react";
import Navigation from "@/components/Navigation";
import styles from "./page.module.css";

interface Alert {
    id: string;
    type: string;
    severity: "critical" | "high" | "medium" | "low";
    source_ip: string;
    destination_ip: string;
    confidence: number;
    timestamp: string;
    status: "active" | "investigating" | "resolved";
}

const mockAlerts: Alert[] = [
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
    {
        id: "6",
        type: "SSH-Patator",
        severity: "high",
        source_ip: "192.168.4.22",
        destination_ip: "10.0.0.22",
        confidence: 0.85,
        timestamp: new Date(Date.now() - 90 * 60000).toISOString(),
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
    const [filter, setFilter] = useState<string>("all");
    const [searchQuery, setSearchQuery] = useState("");

    const filteredAlerts = mockAlerts.filter((alert) => {
        if (filter !== "all" && alert.severity !== filter) return false;
        if (searchQuery && !alert.type.toLowerCase().includes(searchQuery.toLowerCase())) {
            return false;
        }
        return true;
    });

    return (
        <>
            <Navigation />
            <main className={styles.main}>
                <div className={styles.container}>
                    <header className={styles.header}>
                        <h1 className={styles.title}>Security Alerts</h1>
                        <p className={styles.subtitle}>
                            View and manage detected network threats
                        </p>
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

                        {filteredAlerts.map((alert) => {
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
                        })}
                    </div>
                </div>
            </main>
        </>
    );
}
