"use client";

import { useState, useRef } from "react";
import { Upload, FileText, Play, CheckCircle, AlertTriangle } from "lucide-react";
import Navigation from "@/components/Navigation";
import { api, ClassificationResult } from "@/lib/api";
import styles from "./page.module.css";

interface AnalysisResults {
    total: number;
    benign: number;
    threats: number;
    results: ClassificationResult[];
}

export default function AnalyzePage() {
    const [file, setFile] = useState<File | null>(null);
    const [isAnalyzing, setIsAnalyzing] = useState(false);
    const [results, setResults] = useState<AnalysisResults | null>(null);
    const [error, setError] = useState<string | null>(null);
    const fileInputRef = useRef<HTMLInputElement>(null);

    const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
        const selectedFile = e.target.files?.[0];
        if (selectedFile && selectedFile.name.endsWith(".csv")) {
            setFile(selectedFile);
            setResults(null);
            setError(null);
        }
    };

    const handleDrop = (e: React.DragEvent) => {
        e.preventDefault();
        const droppedFile = e.dataTransfer.files[0];
        if (droppedFile && droppedFile.name.endsWith(".csv")) {
            setFile(droppedFile);
            setResults(null);
            setError(null);
        }
    };

    const handleAnalyze = async () => {
        if (!file) return;

        setIsAnalyzing(true);
        setError(null);

        try {
            const response = await api.classifyBatch(file);

            if (response.success) {
                setResults(response.data);
            } else {
                setError(response.error || "Analysis failed");
                // Fallback to demo results
                setResults({
                    total: 150,
                    benign: 135,
                    threats: 15,
                    results: [
                        { prediction: "BENIGN", confidence: 0.98, is_threat: false },
                        { prediction: "DDoS", confidence: 0.95, is_threat: true },
                        { prediction: "BENIGN", confidence: 0.99, is_threat: false },
                        { prediction: "PortScan", confidence: 0.87, is_threat: true },
                        { prediction: "DoS Hulk", confidence: 0.92, is_threat: true },
                    ],
                });
            }
        } catch {
            setError("Failed to connect to backend. Showing demo results.");
            // Fallback to demo
            setResults({
                total: 150,
                benign: 135,
                threats: 15,
                results: [
                    { prediction: "BENIGN", confidence: 0.98, is_threat: false },
                    { prediction: "DDoS", confidence: 0.95, is_threat: true },
                    { prediction: "PortScan", confidence: 0.87, is_threat: true },
                ],
            });
        }

        setIsAnalyzing(false);
    };

    const handleSampleAnalysis = async () => {
        setIsAnalyzing(true);
        setFile(null);
        setError(null);

        // Demo analysis with sample data
        await new Promise((resolve) => setTimeout(resolve, 1000));

        setResults({
            total: 100,
            benign: 85,
            threats: 15,
            results: [
                { prediction: "BENIGN", confidence: 0.98, is_threat: false },
                { prediction: "DDoS", confidence: 0.95, is_threat: true },
                { prediction: "PortScan", confidence: 0.89, is_threat: true },
                { prediction: "BENIGN", confidence: 0.99, is_threat: false },
                { prediction: "DoS Hulk", confidence: 0.92, is_threat: true },
            ],
        });

        setIsAnalyzing(false);
    };

    return (
        <>
            <Navigation />
            <main className={styles.main}>
                <div className={styles.container}>
                    <header className={styles.header}>
                        <h1 className={styles.title}>Analyze Network Traffic</h1>
                        <p className={styles.subtitle}>
                            Upload a CSV file with network flow data for ML-powered threat detection
                        </p>
                    </header>

                    <div className={styles.content}>
                        {/* Upload Section */}
                        <div className={styles.uploadSection}>
                            <div
                                className={styles.dropzone}
                                onDrop={handleDrop}
                                onDragOver={(e) => e.preventDefault()}
                                onClick={() => fileInputRef.current?.click()}
                            >
                                <input
                                    ref={fileInputRef}
                                    type="file"
                                    accept=".csv"
                                    onChange={handleFileSelect}
                                    className={styles.fileInput}
                                />
                                <Upload size={48} className={styles.uploadIcon} />
                                <h3 className={styles.dropzoneTitle}>
                                    {file ? file.name : "Drop CSV file here or click to browse"}
                                </h3>
                                <p className={styles.dropzoneText}>
                                    Supports CICIDS2017 format with 78 features
                                </p>
                            </div>

                            {error && (
                                <div className={styles.errorBanner}>{error}</div>
                            )}

                            <div className={styles.actions}>
                                <button
                                    className={`${styles.btn} ${styles.btnPrimary}`}
                                    onClick={handleAnalyze}
                                    disabled={!file || isAnalyzing}
                                >
                                    <Play size={18} />
                                    {isAnalyzing ? "Analyzing..." : "Analyze File"}
                                </button>
                                <button
                                    className={`${styles.btn} ${styles.btnSecondary}`}
                                    onClick={handleSampleAnalysis}
                                    disabled={isAnalyzing}
                                >
                                    <FileText size={18} />
                                    Try Sample Data
                                </button>
                            </div>
                        </div>

                        {/* Results Section */}
                        {results && (
                            <div className={styles.resultsSection}>
                                <h2 className={styles.resultsTitle}>Analysis Results</h2>

                                <div className={styles.statsRow}>
                                    <div className={styles.statBox}>
                                        <span className={styles.statValue}>{results.total}</span>
                                        <span className={styles.statLabel}>Total Flows</span>
                                    </div>
                                    <div className={`${styles.statBox} ${styles.success}`}>
                                        <span className={styles.statValue}>{results.benign}</span>
                                        <span className={styles.statLabel}>Benign</span>
                                    </div>
                                    <div className={`${styles.statBox} ${styles.danger}`}>
                                        <span className={styles.statValue}>{results.threats}</span>
                                        <span className={styles.statLabel}>Threats</span>
                                    </div>
                                </div>

                                <div className={styles.resultsList}>
                                    <h3 className={styles.resultsListTitle}>Sample Predictions</h3>
                                    {results.results.slice(0, 10).map((result, index) => (
                                        <div
                                            key={index}
                                            className={`${styles.resultItem} ${result.is_threat ? styles.threat : styles.safe
                                                }`}
                                        >
                                            <div className={styles.resultIcon}>
                                                {result.is_threat ? (
                                                    <AlertTriangle size={18} />
                                                ) : (
                                                    <CheckCircle size={18} />
                                                )}
                                            </div>
                                            <span className={styles.resultPrediction}>
                                                {result.prediction}
                                            </span>
                                            <span className={styles.resultConfidence}>
                                                {Math.round(result.confidence * 100)}% confidence
                                            </span>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        )}
                    </div>
                </div>
            </main>
        </>
    );
}
