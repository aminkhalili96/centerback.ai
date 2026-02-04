"use client";

import { useState, useEffect, useCallback } from "react";
import { Activity, Shield, AlertTriangle, Target, RefreshCw } from "lucide-react";
import Navigation from "@/components/Navigation";
import StatCard from "@/components/StatCard";
import AlertList from "@/components/AlertList";
import { AttackDistributionChart, TrafficTimelineChart } from "@/components/Charts";
import { api, DashboardStats, Alert, AttackDistribution } from "@/lib/api";
import styles from "./page.module.css";

// Fallback mock data when API is unavailable
const fallbackStats: DashboardStats = {
  total_flows: 0,
  threats_detected: 0,
  benign_flows: 0,
  critical_alerts: 0,
  model_accuracy: 82.87,
};

const fallbackTrafficData = Array.from({ length: 24 }, (_, i) => ({
  time: `${String(i).padStart(2, "0")}:00`,
  benign: Math.floor(Math.random() * 200) + 400,
  threats: Math.floor(Math.random() * 20),
}));

export default function Dashboard() {
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [stats, setStats] = useState<DashboardStats>(fallbackStats);
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [attackDistribution, setAttackDistribution] = useState<AttackDistribution[]>([]);
  const [isRefreshing, setIsRefreshing] = useState(false);

  const fetchData = useCallback(async () => {
    try {
      // Fetch all data in parallel
      const [statsRes, alertsRes, distributionRes] = await Promise.all([
        api.getStats(),
        api.getAlerts(10),
        api.getAttackDistribution(),
      ]);

      if (statsRes.success) {
        setStats(statsRes.data);
      }

      if (alertsRes.success) {
        setAlerts(alertsRes.data);
      }

      if (distributionRes.success) {
        setAttackDistribution(distributionRes.data);
      }

      setError(null);
    } catch (err) {
      setError("Failed to connect to backend. Using demo data.");
      console.error("API Error:", err);
    }
  }, []);

  const handleRefresh = async () => {
    setIsRefreshing(true);
    await fetchData();
    setIsRefreshing(false);
  };

  useEffect(() => {
    const init = async () => {
      await fetchData();
      setIsLoading(false);
    };
    init();

    // Auto-refresh every 30 seconds
    const interval = setInterval(fetchData, 30000);
    return () => clearInterval(interval);
  }, [fetchData]);

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
            <div className={styles.headerContent}>
              <div>
                <h1 className={styles.title}>Network Security Dashboard</h1>
                <p className={styles.subtitle}>
                  Real-time network traffic analysis and threat detection
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

          {/* Stats Grid */}
          <section className={styles.statsGrid}>
            <StatCard
              title="Total Flows Analyzed"
              value={stats.total_flows.toLocaleString()}
              icon={<Activity size={20} />}
              trend={{ value: 12, isPositive: true }}
              variant="accent"
            />
            <StatCard
              title="Threats Detected"
              value={stats.threats_detected}
              icon={<AlertTriangle size={20} />}
              trend={{ value: 3, isPositive: false }}
              variant="danger"
            />
            <StatCard
              title="Critical Alerts"
              value={stats.critical_alerts}
              icon={<Shield size={20} />}
              variant="warning"
            />
            <StatCard
              title="Model Accuracy"
              value={`${stats.model_accuracy}%`}
              icon={<Target size={20} />}
              variant="success"
            />
          </section>

          {/* Charts Section */}
          <section className={styles.chartsSection}>
            <div className={styles.chartCard}>
              <h3 className={styles.chartTitle}>Traffic Overview (24h)</h3>
              <TrafficTimelineChart data={fallbackTrafficData} />
            </div>
            <div className={styles.chartCard}>
              <h3 className={styles.chartTitle}>Attack Distribution</h3>
              <AttackDistributionChart
                data={attackDistribution.length > 0 ? attackDistribution : [
                  { type: "No Data", count: 1 }
                ]}
              />
            </div>
          </section>

          {/* Alerts Section */}
          <section className={styles.alertsSection}>
            <AlertList alerts={alerts} maxItems={5} />
          </section>
        </div>
      </main>
    </>
  );
}
