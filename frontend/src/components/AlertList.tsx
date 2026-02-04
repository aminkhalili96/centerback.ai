import { AlertTriangle, AlertCircle, Info, CheckCircle } from "lucide-react";
import styles from "./AlertList.module.css";

interface Alert {
    id: string;
    type: string;
    severity: "critical" | "high" | "medium" | "low";
    source_ip: string;
    destination_ip: string;
    confidence: number;
    timestamp: string;
    status: string;
}

interface AlertListProps {
    alerts: Alert[];
    maxItems?: number;
}

const severityConfig = {
    critical: { icon: AlertTriangle, label: "Critical" },
    high: { icon: AlertCircle, label: "High" },
    medium: { icon: Info, label: "Medium" },
    low: { icon: CheckCircle, label: "Low" },
};

function formatTime(timestamp: string): string {
    const date = new Date(timestamp);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);

    if (diffMins < 1) return "Just now";
    if (diffMins < 60) return `${diffMins} min ago`;
    if (diffMins < 1440) return `${Math.floor(diffMins / 60)} hours ago`;
    return date.toLocaleDateString();
}

export default function AlertList({ alerts, maxItems = 5 }: AlertListProps) {
    const displayAlerts = alerts.slice(0, maxItems);

    return (
        <div className={styles.container}>
            <div className={styles.header}>
                <h3 className={styles.title}>Recent Alerts</h3>
                <span className={styles.count}>{alerts.length} total</span>
            </div>

            <div className={styles.list}>
                {displayAlerts.map((alert) => {
                    const config = severityConfig[alert.severity];
                    const Icon = config.icon;

                    return (
                        <div key={alert.id} className={`${styles.item} ${styles[alert.severity]}`}>
                            <div className={styles.iconWrapper}>
                                <Icon size={18} />
                            </div>

                            <div className={styles.content}>
                                <div className={styles.itemHeader}>
                                    <span className={styles.type}>{alert.type}</span>
                                    <span className={`${styles.badge} ${styles[alert.severity]}`}>
                                        {config.label}
                                    </span>
                                </div>
                                <div className={styles.details}>
                                    <span>{alert.source_ip}</span>
                                    <span className={styles.arrow}>→</span>
                                    <span>{alert.destination_ip}</span>
                                </div>
                            </div>

                            <div className={styles.meta}>
                                <span className={styles.confidence}>
                                    {Math.round(alert.confidence * 100)}%
                                </span>
                                <span className={styles.time}>{formatTime(alert.timestamp)}</span>
                            </div>
                        </div>
                    );
                })}
            </div>
        </div>
    );
}
