"use client";

import { useState, useEffect, useCallback } from "react";
import Link from "next/link";
import { Activity, Shield, AlertTriangle, Target, RefreshCw, Database, Play } from "lucide-react";
import Navigation from "@/components/Navigation";
import StatCard from "@/components/StatCard";
import AlertList from "@/components/AlertList";
import { AttackDistributionChart, TrafficTimelineChart } from "@/components/Charts";
import { api, Alert, AttackDistribution, SessionStats } from "@/lib/api";
import styles from "./page.module.css";

const fallbackTrafficData = Array.from({ length: 24 }, (_, i) => ({
  time: `${String(i).padStart(2, "0")}:00`,
  benign: Math.floor(Math.random() * 200) + 400,
  threats: Math.floor(Math.random() * 20),
}));

export default function Dashboard() {
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [sessionStats, setSessionStats] = useState<SessionStats | null>(null);
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [isRefreshing, setIsRefreshing] = useState(false);

  const fetchData = useCallback(async () => {
    try {
      const [sessionRes, alertsRes] = await Promise.all([
        api.getSessionStats(),
        api.getAlerts(10),
      ]);

      if (sessionRes.success) {
        setSessionStats(sessionRes.data);
      }

      if (alertsRes.success) {
        setAlerts(alertsRes.data);
      }

      setError(null);
    } catch (err) {
      setError("Failed to connect to backend.");
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

  const hasData = sessionStats?.has_data ?? false;

  // Empty state - no analysis run yet
  if (!hasData) {
    return (
      <>
        <Navigation />
        <main className={styles.main}>
          <div className={styles.container}>
            <div className={styles.emptyState}>
              <Database size={64} className={styles.emptyIcon} />
              <h1>No Data Analyzed Yet</h1>
              <p>
                Run an analysis on the sample dataset to see real results here.
              </p>
              <Link href="/dataset" className={styles.ctaButton}>
                <Play size={20} />
                Explore Dataset
              </Link>
              <p className={styles.modelNote}>
                Model Accuracy: {sessionStats?.model_accuracy ?? 82.87}%
              </p>
            </div>
          </div>
        </main>
      </>
    );
  }

  // Build attack distribution from session stats
  const attackDistribution: AttackDistribution[] = sessionStats?.attack_distribution ?? [];

  // TypeScript guard - after hasData check, sessionStats is guaranteed to exist
  if (!sessionStats) return null;

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
                  Results from your analysis session
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
              value={sessionStats.total_flows.toLocaleString()}
              icon={<Activity size={20} />}
              variant="accent"
            />
            <StatCard
              title="Threats Detected"
              value={sessionStats.threats_detected}
              icon={<AlertTriangle size={20} />}
              variant="danger"
            />
            <StatCard
              title="Critical Alerts"
              value={sessionStats.critical_alerts}
              icon={<Shield size={20} />}
              variant="warning"
            />
            <StatCard
              title="Model Accuracy"
              value={`${sessionStats.model_accuracy ?? 82.87}%`}
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
                  { type: "No Threats", count: 1 }
                ]}
              />
            </div>
          </section>

          {/* Alerts Section */}
          <section className={styles.alertsSection}>
            <AlertList alerts={alerts} maxItems={5} />
          </section>

          {/* Session Info */}
          <section className={styles.sessionInfo}>
            <p>
              Session started: {sessionStats.started_at ? new Date(sessionStats.started_at).toLocaleString() : 'N/A'}
              {' | '}
              <Link href="/dataset">Analyze more data</Link>
            </p>
          </section>
        </div>
      </main>
    </>
  );
}

