import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "CenterBack.AI - Network Intrusion Detection",
  description: "AI-powered Network Intrusion Detection System - Detects DDoS, SQL Injection, Port Scans & more",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
