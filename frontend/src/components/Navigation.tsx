"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { LayoutDashboard, Search, Bell, Info, Shield } from "lucide-react";
import styles from "./Navigation.module.css";

const navItems = [
    { href: "/", label: "Dashboard", icon: LayoutDashboard },
    { href: "/analyze", label: "Analyze", icon: Search },
    { href: "/alerts", label: "Alerts", icon: Bell },
    { href: "/about", label: "About", icon: Info },
];

export default function Navigation() {
    const pathname = usePathname();

    return (
        <nav className={styles.nav}>
            <div className={styles.container}>
                <Link href="/" className={styles.logo}>
                    <Shield size={28} />
                    <span className={styles.logoText}>CenterBack.AI</span>
                </Link>

                <ul className={styles.menu}>
                    {navItems.map((item) => {
                        const Icon = item.icon;
                        const isActive = pathname === item.href;
                        return (
                            <li key={item.href}>
                                <Link
                                    href={item.href}
                                    className={`${styles.menuItem} ${isActive ? styles.active : ""}`}
                                >
                                    <Icon size={18} />
                                    <span>{item.label}</span>
                                </Link>
                            </li>
                        );
                    })}
                </ul>

                <div className={styles.status}>
                    <span className={styles.statusDot}></span>
                    <span>Live</span>
                </div>
            </div>
        </nav>
    );
}
