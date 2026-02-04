"use client";

import { useEffect, useRef } from "react";
import * as echarts from "echarts";
import styles from "./Charts.module.css";

interface AttackDistributionProps {
    data: { type: string; count: number }[];
}

export function AttackDistributionChart({ data }: AttackDistributionProps) {
    const chartRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        if (!chartRef.current) return;

        const chart = echarts.init(chartRef.current, "dark");

        const option = {
            backgroundColor: "transparent",
            tooltip: {
                trigger: "item",
                backgroundColor: "#2d2d2d",
                borderColor: "#404040",
                textStyle: { color: "#f5f5f5" },
            },
            legend: {
                orient: "vertical",
                right: "5%",
                top: "center",
                textStyle: { color: "#a0a0a0" },
            },
            series: [
                {
                    name: "Attack Distribution",
                    type: "pie",
                    radius: ["45%", "75%"],
                    center: ["35%", "50%"],
                    avoidLabelOverlap: false,
                    itemStyle: {
                        borderRadius: 6,
                        borderColor: "#1a1a1a",
                        borderWidth: 2,
                    },
                    label: { show: false },
                    emphasis: {
                        label: { show: true, fontSize: 14, fontWeight: "bold" },
                    },
                    labelLine: { show: false },
                    data: data.map((item, index) => ({
                        value: item.count,
                        name: item.type,
                        itemStyle: {
                            color: [
                                "#da7756",
                                "#e8956a",
                                "#f87171",
                                "#fbbf24",
                                "#4ade80",
                                "#60a5fa",
                            ][index % 6],
                        },
                    })),
                },
            ],
        };

        chart.setOption(option);

        const handleResize = () => chart.resize();
        window.addEventListener("resize", handleResize);

        return () => {
            window.removeEventListener("resize", handleResize);
            chart.dispose();
        };
    }, [data]);

    return <div ref={chartRef} className={styles.chart} />;
}

interface TrafficTimelineProps {
    data: { time: string; benign: number; threats: number }[];
}

export function TrafficTimelineChart({ data }: TrafficTimelineProps) {
    const chartRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        if (!chartRef.current) return;

        const chart = echarts.init(chartRef.current, "dark");

        const option = {
            backgroundColor: "transparent",
            tooltip: {
                trigger: "axis",
                backgroundColor: "#2d2d2d",
                borderColor: "#404040",
                textStyle: { color: "#f5f5f5" },
            },
            legend: {
                data: ["Benign", "Threats"],
                textStyle: { color: "#a0a0a0" },
                top: 0,
            },
            grid: {
                left: "3%",
                right: "4%",
                bottom: "3%",
                top: "15%",
                containLabel: true,
            },
            xAxis: {
                type: "category",
                boundaryGap: false,
                data: data.map((d) => d.time),
                axisLine: { lineStyle: { color: "#404040" } },
                axisLabel: { color: "#a0a0a0" },
            },
            yAxis: {
                type: "value",
                axisLine: { lineStyle: { color: "#404040" } },
                axisLabel: { color: "#a0a0a0" },
                splitLine: { lineStyle: { color: "#2d2d2d" } },
            },
            series: [
                {
                    name: "Benign",
                    type: "line",
                    smooth: true,
                    areaStyle: {
                        opacity: 0.3,
                        color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                            { offset: 0, color: "#4ade80" },
                            { offset: 1, color: "transparent" },
                        ]),
                    },
                    lineStyle: { color: "#4ade80", width: 2 },
                    itemStyle: { color: "#4ade80" },
                    data: data.map((d) => d.benign),
                },
                {
                    name: "Threats",
                    type: "line",
                    smooth: true,
                    areaStyle: {
                        opacity: 0.3,
                        color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                            { offset: 0, color: "#f87171" },
                            { offset: 1, color: "transparent" },
                        ]),
                    },
                    lineStyle: { color: "#f87171", width: 2 },
                    itemStyle: { color: "#f87171" },
                    data: data.map((d) => d.threats),
                },
            ],
        };

        chart.setOption(option);

        const handleResize = () => chart.resize();
        window.addEventListener("resize", handleResize);

        return () => {
            window.removeEventListener("resize", handleResize);
            chart.dispose();
        };
    }, [data]);

    return <div ref={chartRef} className={styles.chart} />;
}
