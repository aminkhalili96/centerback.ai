"use client";

import { useState, useEffect } from "react";
import { Activity, Shield, AlertTriangle, Target } from "lucide-react";
import Navigation from "@/components/Navigation";
import StatCard from "@/components/StatCard";
import AlertList from "@/components/AlertList";
import { AttackDistributionChart, TrafficTimelineChart } from "@/components/Charts";
import styles from "./page.module.css";

// Mock data - in production, fetch from API
const mockStats = {
  total_flows: 12847,
  threats_detected: 26,
  critical_alerts: 3,
  model_accuracy: 99.2,
};

const mockAlerts = [
  {
    id: "1",
    type: "DDoS",
    severity: "critical" as const,
    source_ip: "192.168.1.105",
    destination_ip: "10.0.0.50",
    confidence: 0.95,
    timestamp: new Date(Date.now() - 2 * 60000).toISOString(),
    status: "active",
  },
  {
    id: "2",
    type: "PortScan",
    severity: "high" as const,
    source_ip: "192.168.1.42",
    destination_ip: "10.0.0.0/24",
    confidence: 0.89,
    timestamp: new Date(Date.now() - 5 * 60000).toISOString(),
    status: "active",
  },
  {
    id: "3",
    type: "DoS Hulk",
    severity: "high" as const,
    source_ip: "192.168.2.15",
    destination_ip: "10.0.0.80",
    confidence: 0.92,
    timestamp: new Date(Date.now() - 12 * 60000).toISOString(),
    status: "investigating",
  },
  {
    id: "4",
    type: "Bot",
    severity: "medium" as const,
    source_ip: "192.168.1.200",
    destination_ip: "external",
    confidence: 0.78,
    timestamp: new Date(Date.now() - 30 * 60000).toISOString(),
    status: "resolved",
  },
  {
    id: "5",
    type: "SQL Injection",
    severity: "critical" as const,
    source_ip: "192.168.3.50",
    destination_ip: "10.0.0.100",
    confidence: 0.97,
    timestamp: new Date(Date.now() - 60 * 60000).toISOString(),
    status: "resolved",
  },
];

const mockAttackDistribution = [
  { type: "DDoS", count: 45 },
  { type: "PortScan", count: 32 },
  { type: "DoS Hulk", count: 15 },
  { type: "Bot", count: 10 },
  { type: "Web Attack", count: 8 },
  { type: "Other", count: 2 },
];

const mockTrafficData = Array.from({ length: 24 }, (_, i) => ({
  time: `${String(i).padStart(2, "0")}:00`,
  benign: Math.floor(Math.random() * 200) + 400,
  threats: Math.floor(Math.random() * 20),
}));

export default function Dashboard() {
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    // Simulate loading
    const timer = setTimeout(() => setIsLoading(false), 500);
    return () => clearTimeout(timer);
  }, []);

  if (isLoading) {
    return (
      <>
        <Navigation />
        <main className={styles.main}>
          <div className={styles.loading}>Loading dashboard...</div>
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
            <h1 className={styles.title}>Network Security Dashboard</h1>
            <p className={styles.subtitle}>
              Real-time network traffic analysis and threat detection
            </p>
          </header>

          {/* Stats Grid */}
          <section className={styles.statsGrid}>
            <StatCard
              title="Total Flows Analyzed"
              value={mockStats.total_flows.toLocaleString()}
              icon={<Activity size={20} />}
              trend={{ value: 12, isPositive: true }}
              variant="accent"
            />
            <StatCard
              title="Threats Detected"
              value={mockStats.threats_detected}
              icon={<AlertTriangle size={20} />}
              trend={{ value: 3, isPositive: false }}
              variant="danger"
            />
            <StatCard
              title="Critical Alerts"
              value={mockStats.critical_alerts}
              icon={<Shield size={20} />}
              variant="warning"
            />
            <StatCard
              title="Model Accuracy"
              value={`${mockStats.model_accuracy}%`}
              icon={<Target size={20} />}
              variant="success"
            />
          </section>

          {/* Charts Section */}
          <section className={styles.chartsSection}>
            <div className={styles.chartCard}>
              <h3 className={styles.chartTitle}>Traffic Overview (24h)</h3>
              <TrafficTimelineChart data={mockTrafficData} />
            </div>
            <div className={styles.chartCard}>
              <h3 className={styles.chartTitle}>Attack Distribution</h3>
              <AttackDistributionChart data={mockAttackDistribution} />
            </div>
          </section>

          {/* Alerts Section */}
          <section className={styles.alertsSection}>
            <AlertList alerts={mockAlerts} maxItems={5} />
          </section>
        </div>
      </main>
    </>
  );
}
