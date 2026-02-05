'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { Database, Download, Play, FileText, AlertTriangle, Loader2 } from 'lucide-react';
import styles from './page.module.css';
import { api } from '@/lib/api';

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

export default function DatasetPage() {
    const router = useRouter();
    const [info, setInfo] = useState<DatasetInfo | null>(null);
    const [preview, setPreview] = useState<DatasetPreview | null>(null);
    const [loading, setLoading] = useState(true);
    const [analyzing, setAnalyzing] = useState(false);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        loadDatasetInfo();
    }, []);

    async function loadDatasetInfo() {
        try {
            setLoading(true);
            const [infoRes, previewRes] = await Promise.all([
                api.getDatasetInfo(),
                api.getDatasetPreview(20),
            ]);

            if (infoRes.success) setInfo(infoRes.data);
            if (previewRes.success) setPreview(previewRes.data);
            if (!infoRes.success) setError(infoRes.error || 'Failed to load dataset info');
        } catch (err) {
            setError('Failed to connect to backend');
        } finally {
            setLoading(false);
        }
    }

    async function runAnalysis() {
        try {
            setAnalyzing(true);
            setError(null);
            const result = await api.classifySample();

            if (result.success && result.data) {
                // Redirect to dashboard to see results
                router.push('/');
            } else {
                setError(result.error || 'Analysis failed');
            }
        } catch (err) {
            setError('Analysis failed');
        } finally {
            setAnalyzing(false);
        }
    }

    function downloadDataset() {
        window.open(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/dataset/download`, '_blank');
    }

    if (loading) {
        return (
            <div className={styles.container}>
                <div className={styles.loading}>
                    <Loader2 className={styles.spinner} size={48} />
                    <p>Loading dataset information...</p>
                </div>
            </div>
        );
    }

    return (
        <div className={styles.container}>
            <header className={styles.header}>
                <div className={styles.headerContent}>
                    <Database size={32} />
                    <div>
                        <h1>Explore the Dataset</h1>
                        <p>CICIDS2017 sample data for network intrusion detection</p>
                    </div>
                </div>
            </header>

            {error && (
                <div className={styles.errorBanner}>
                    <AlertTriangle size={20} />
                    <span>{error}</span>
                </div>
            )}

            {/* Dataset Overview Cards */}
            <section className={styles.statsGrid}>
                <div className={styles.statCard}>
                    <FileText size={24} />
                    <div className={styles.statValue}>{info?.rows?.toLocaleString() || '50,000'}</div>
                    <div className={styles.statLabel}>Network Flows</div>
                </div>
                <div className={styles.statCard}>
                    <Database size={24} />
                    <div className={styles.statValue}>{info?.features || 78}</div>
                    <div className={styles.statLabel}>Features</div>
                </div>
                <div className={styles.statCard}>
                    <AlertTriangle size={24} />
                    <div className={styles.statValue}>{info?.attack_types?.length || 15}</div>
                    <div className={styles.statLabel}>Attack Types</div>
                </div>
            </section>

            {/* Dataset Description */}
            <section className={styles.descriptionSection}>
                <h2>About This Dataset</h2>
                <p>{info?.description || 'Synthetic network traffic data based on the CICIDS2017 dataset format.'}</p>

                <h3>Attack Types Included</h3>
                <div className={styles.attackGrid}>
                    {info?.attack_types?.map((attack) => (
                        <div key={attack.name} className={styles.attackCard}>
                            <span className={styles.attackName}>{attack.name}</span>
                            <span className={styles.attackDesc}>{attack.description}</span>
                        </div>
                    ))}
                </div>
            </section>

            {/* Data Preview Table */}
            <section className={styles.previewSection}>
                <div className={styles.previewHeader}>
                    <h2>Data Preview</h2>
                    <span className={styles.previewMeta}>
                        Showing {preview?.preview_rows || 0} of {preview?.total_rows?.toLocaleString() || '50,000'} rows
                    </span>
                </div>

                {preview && (
                    <div className={styles.tableWrapper}>
                        <table className={styles.dataTable}>
                            <thead>
                                <tr>
                                    {preview.columns.map((col) => (
                                        <th key={col}>{col}</th>
                                    ))}
                                </tr>
                            </thead>
                            <tbody>
                                {preview.rows.map((row, i) => (
                                    <tr key={i}>
                                        {row.map((cell, j) => (
                                            <td key={j}>
                                                {typeof cell === 'number' ? cell.toFixed(2) : cell}
                                            </td>
                                        ))}
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                )}
            </section>

            {/* Action Buttons */}
            <section className={styles.actionSection}>
                <button
                    className={styles.downloadButton}
                    onClick={downloadDataset}
                    disabled={!info?.file_exists}
                >
                    <Download size={20} />
                    Download CSV
                </button>

                <button
                    className={styles.analyzeButton}
                    onClick={runAnalysis}
                    disabled={analyzing || !info?.file_exists}
                >
                    {analyzing ? (
                        <>
                            <Loader2 className={styles.spinner} size={20} />
                            Analyzing...
                        </>
                    ) : (
                        <>
                            <Play size={20} />
                            Analyze This Dataset
                        </>
                    )}
                </button>
            </section>
        </div>
    );
}
