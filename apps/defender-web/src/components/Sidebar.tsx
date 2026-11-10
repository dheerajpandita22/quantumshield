"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import clsx from "clsx";
import {
  Shield, LayoutDashboard, AlertTriangle, FileWarning,
  Atom, FileBarChart, Settings, Zap,
} from "lucide-react";

const NAV_ITEMS = [
  { href: "/",           label: "Dashboard",           icon: LayoutDashboard },
  { href: "/events",     label: "Security Events",     icon: AlertTriangle },
  { href: "/incidents",  label: "Incidents",           icon: FileWarning },
  { href: "/quantum",    label: "Quantum Verification",icon: Atom },
  { href: "/reports",    label: "Reports",             icon: FileBarChart },
  { href: "/settings",   label: "Settings",            icon: Settings },
];

export default function Sidebar() {
  const pathname = usePathname();
  return (
    <aside className="fixed inset-y-0 left-0 w-64 bg-[#0f1629] border-r border-[#1e2d4a] flex flex-col z-30">
      {/* Logo */}
      <div className="flex items-center gap-3 px-6 py-5 border-b border-[#1e2d4a]">
        <div className="relative">
          <Shield className="w-8 h-8 text-indigo-500" />
          <Zap className="w-3 h-3 text-cyan-400 absolute -top-0.5 -right-0.5" />
        </div>
        <div>
          <div className="text-white font-bold text-sm leading-tight">QuantumShield</div>
          <div className="text-indigo-400 text-xs font-medium">DEFENDER</div>
        </div>
      </div>

      {/* Nav */}
      <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
        {NAV_ITEMS.map(({ href, label, icon: Icon }) => (
          <Link
            key={href}
            href={href}
            className={clsx("nav-link", pathname === href && "active")}
          >
            <Icon className="w-4 h-4 shrink-0" />
            {label}
          </Link>
        ))}
      </nav>

      {/* Status */}
      <div className="px-4 py-4 border-t border-[#1e2d4a]">
        <div className="flex items-center gap-2 text-xs text-slate-500">
          <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
          System Operational
        </div>
        <div className="text-xs text-slate-600 mt-1">v0.1.0 — Day 1</div>
      </div>
    </aside>
  );
}
