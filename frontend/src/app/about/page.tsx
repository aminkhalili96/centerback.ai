import { Shield, Github, Database, Brain, Zap, Lock } from "lucide-react";
import Navigation from "@/components/Navigation";
import styles from "./page.module.css";

const features = [
    {
        icon: Brain,
        title: "Machine Learning",
        description: "Random Forest classifier trained on CICIDS2017-shaped data (demo model)",
    },
    {
        icon: Zap,
        title: "Real-time Detection",
        description: "Instant classification of network traffic flows for immediate threat response",
    },
    {
        icon: Lock,
        title: "14 Attack Types",
        description: "Detects DDoS, SQL Injection, Port Scans, Brute Force, and more",
    },
    {
        icon: Database,
        title: "Batch Analysis",
        description: "Upload CSV files for bulk classification of historical traffic data",
    },
];

const attackTypes = [
    "DDoS",
    "DoS GoldenEye",
    "DoS Hulk",
    "DoS Slowloris",
    "DoS Slowhttptest",
    "PortScan",
    "Bot",
    "Infiltration",
    "Heartbleed",
    "FTP-Patator",
    "SSH-Patator",
    "Web Attack - Brute Force",
    "Web Attack - SQL Injection",
    "Web Attack - XSS",
];

export default function AboutPage() {
    return (
        <>
            <Navigation />
            <main className={styles.main}>
                <div className={styles.container}>
                    <header className={styles.header}>
                        <Shield size={64} className={styles.logo} />
                        <h1 className={styles.title}>CenterBack.AI</h1>
                        <p className={styles.tagline}>
                            AI-Powered Network Intrusion Detection System
                        </p>
                    </header>

                    <section className={styles.section}>
                        <h2 className={styles.sectionTitle}>About</h2>
                        <p className={styles.description}>
                            CenterBack.AI is an intelligent network security system that uses machine
                            learning to detect and classify network intrusions in real-time. Built with
                            a Random Forest classifier trained on the CICIDS2017 dataset, it can identify
                            14 different types of network attacks (accuracy depends on training data).
                        </p>
                    </section>

                    <section className={styles.section}>
                        <h2 className={styles.sectionTitle}>Features</h2>
                        <div className={styles.featuresGrid}>
                            {features.map((feature) => {
                                const Icon = feature.icon;
                                return (
                                    <div key={feature.title} className={styles.featureCard}>
                                        <Icon size={28} className={styles.featureIcon} />
                                        <h3 className={styles.featureTitle}>{feature.title}</h3>
                                        <p className={styles.featureDescription}>{feature.description}</p>
                                    </div>
                                );
                            })}
                        </div>
                    </section>

                    <section className={styles.section}>
                        <h2 className={styles.sectionTitle}>Detected Attack Types</h2>
                        <div className={styles.attackGrid}>
                            {attackTypes.map((attack) => (
                                <span key={attack} className={styles.attackTag}>
                                    {attack}
                                </span>
                            ))}
                        </div>
                    </section>

                    <section className={styles.section}>
                        <h2 className={styles.sectionTitle}>Tech Stack</h2>
                        <div className={styles.techStack}>
                            <div className={styles.techItem}>
                                <span className={styles.techLabel}>Backend</span>
                                <span className={styles.techValue}>FastAPI + Python</span>
                            </div>
                            <div className={styles.techItem}>
                                <span className={styles.techLabel}>Frontend</span>
                                <span className={styles.techValue}>Next.js + TypeScript</span>
                            </div>
                            <div className={styles.techItem}>
                                <span className={styles.techLabel}>ML Model</span>
                                <span className={styles.techValue}>Random Forest (scikit-learn)</span>
                            </div>
                            <div className={styles.techItem}>
                                <span className={styles.techLabel}>Dataset</span>
                                <span className={styles.techValue}>CICIDS2017 (2.8M flows)</span>
                            </div>
                            <div className={styles.techItem}>
                                <span className={styles.techLabel}>Database</span>
                                <span className={styles.techValue}>Supabase (PostgreSQL)</span>
                            </div>
                            <div className={styles.techItem}>
                                <span className={styles.techLabel}>Charts</span>
                                <span className={styles.techValue}>Apache ECharts</span>
                            </div>
                        </div>
                    </section>

                    <footer className={styles.footer}>
                        <a
                            href="https://github.com/aminkhalili96/centerback.ai"
                            target="_blank"
                            rel="noopener noreferrer"
                            className={styles.githubLink}
                        >
                            <Github size={20} />
                            View on GitHub
                        </a>
                    </footer>
                </div>
            </main>
        </>
    );
}
