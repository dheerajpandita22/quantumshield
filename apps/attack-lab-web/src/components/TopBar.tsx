"use client";
import { Bell, User } from "lucide-react";
interface TopBarProps { title: string; subtitle?: string; }
export default function TopBar({ title, subtitle }: TopBarProps) {
  return (
    <header className="h-14 border-b border-[#1a2030] flex items-center justify-between px-6 bg-[#0a0d12]/80 backdrop-blur sticky top-0 z-20">
      <div>
        <h1 className="text-white font-semibold text-lg leading-tight">{title}</h1>
        {subtitle && <p className="text-slate-500 text-xs">{subtitle}</p>}
      </div>
      <div className="flex items-center gap-3">
        <div className="text-xs text-orange-400 bg-orange-500/10 border border-orange-500/20 px-2 py-1 rounded">
          SANDBOX MODE
        </div>
        <button className="p-2 rounded-lg text-slate-400 hover:text-white hover:bg-white/5 transition-colors">
          <Bell className="w-4 h-4" />
        </button>
        <button className="p-2 rounded-lg text-slate-400 hover:text-white hover:bg-white/5 transition-colors">
          <User className="w-4 h-4" />
        </button>
      </div>
    </header>
  );
}
