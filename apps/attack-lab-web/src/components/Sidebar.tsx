"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import clsx from "clsx";
import {
  Shield, Zap, LayoutDashboard, FlaskConical,
  Play, List, History, FileText, AlertOctagon,
} from "lucide-react";

const NAV_ITEMS = [
  { href: "/",           label: "Lab Dashboard",      icon: LayoutDashboard },
  { href: "/scenarios",  label: "Attack Scenarios",   icon: FlaskConical },
  { href: "/simulate",   label: "Run Simulation",     icon: Play },
  { href: "/batch",      label: "Batch Testing",      icon: List },
  { href: "/history",    label: "Execution History",  icon: History },
  { href: "/results",    label: "Results & Evaluation",icon: FileText },
];

export default function Sidebar() {
  const pathname = usePathname();
  return (
    <aside className="fixed inset-y-0 left-0 w-64 bg-[#0e1218] border-r border-[#1a2030] flex flex-col z-30">
      <div className="flex items-center gap-3 px-6 py-5 border-b border-[#1a2030]">
        <div className="relative">
          <Shield className="w-8 h-8 text-orange-500" />
          <Zap className="w-3 h-3 text-yellow-400 absolute -top-0.5 -right-0.5" />
        </div>
        <div>
          <div className="text-white font-bold text-sm leading-tight">QuantumShield</div>
          <div className="text-orange-400 text-xs font-medium">ATTACK LAB</div>
        </div>
      </div>

      <div className="mx-4 my-3 px-3 py-2 bg-orange-500/10 border border-orange-500/20 rounded-lg">
        <div className="flex items-center gap-2 text-orange-400 text-xs font-semibold">
          <AlertOctagon className="w-3.5 h-3.5" />
          AUTHORIZED LAB ONLY
        </div>
        <p className="text-orange-300/60 text-xs mt-0.5">Local sandbox · Synthetic data only</p>
      </div>

      <nav className="flex-1 px-3 py-2 space-y-1 overflow-y-auto">
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

      <div className="px-4 py-4 border-t border-[#1a2030]">
        <div className="flex items-center gap-2 text-xs text-slate-500">
          <span className="w-2 h-2 rounded-full bg-orange-500 animate-pulse" />
          Lab Environment Ready
        </div>
        <div className="text-xs text-slate-600 mt-1">v0.1.0 — Day 1</div>
      </div>
    </aside>
  );
}
