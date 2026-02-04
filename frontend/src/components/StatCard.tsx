import styles from "./StatCard.module.css";

interface StatCardProps {
    title: string;
    value: string | number;
    icon: React.ReactNode;
    trend?: {
        value: number;
        isPositive: boolean;
    };
    variant?: "default" | "accent" | "success" | "warning" | "danger";
}

export default function StatCard({
    title,
    value,
    icon,
    trend,
    variant = "default",
}: StatCardProps) {
    return (
        <div className={`${styles.card} ${styles[variant]}`}>
            <div className={styles.header}>
                <span className={styles.title}>{title}</span>
                <div className={styles.icon}>{icon}</div>
            </div>
            <div className={styles.value}>{value}</div>
            {trend && (
                <div
                    className={`${styles.trend} ${trend.isPositive ? styles.positive : styles.negative
                        }`}
                >
                    {trend.isPositive ? "+" : ""}
                    {trend.value}% from last hour
                </div>
            )}
        </div>
    );
}
