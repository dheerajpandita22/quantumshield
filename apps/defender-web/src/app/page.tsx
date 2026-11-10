import Sidebar from "@/components/Sidebar";
import TopBar from "@/components/TopBar";
import PlaceholderBanner from "@/components/PlaceholderBanner";
import {
  Shield, AlertTriangle, CheckCircle, Activity,
  Atom, TrendingUp, Clock, Zap,
} from "lucide-react";

const STATS = [
  { label: "Active Threats",     value: "—",      sub: "Placeholder",    icon: AlertTriangle, color: "text-red-400",    bg: "bg-red-500/10" },
  { label: "Verified Events",    value: "—",      sub: "Placeholder",    icon: CheckCircle,   color: "text-emerald-400",bg: "bg-emerald-500/10" },
  { label: "Quantum Jobs Today", value: "—",      sub: "Placeholder",    icon: Atom,          color: "text-indigo-400", bg: "bg-indigo-500/10" },
  { label: "System Uptime",      value: "99.9%",  sub: "Target SLA",     icon: Activity,      color: "text-cyan-400",   bg: "bg-cyan-500/10" },
];

const FEED_ITEMS = [
  { type: "INFO",    text: "QuantumShield Defender initialised successfully.", time: "Just now" },
  { type: "NOTICE",  text: "Quantum backend: Qiskit Aer (simulation mode).", time: "Day 1" },
  { type: "NOTICE",  text: "Real threat detection pipeline — planned for Day 2+.", time: "Planned" },
];

export default function DashboardPage() {
  return (
    <div className="flex min-h-screen bg-[#0a0e1a]">
      <Sidebar />
      <main className="ml-64 flex-1 flex flex-col">
        <TopBar title="Dashboard" subtitle="Security Overview" />
        <div className="flex-1 p-6 space-y-6">
          <PlaceholderBanner />

          {/* Stats grid */}
          <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4">
            {STATS.map(({ label, value, sub, icon: Icon, color, bg }) => (
              <div key={label} className="stat-card flex items-start gap-4">
                <div className={`p-2.5 rounded-lg ${bg}`}>
                  <Icon className={`w-5 h-5 ${color}`} />
                </div>
                <div>
                  <div className={`text-2xl font-bold ${color}`}>{value}</div>
                  <div className="text-white text-sm font-medium">{label}</div>
                  <div className="text-slate-500 text-xs">{sub}</div>
                </div>
              </div>
            ))}
          </div>

          {/* Two-column layout */}
          <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
            {/* Live Feed */}
            <div className="section-card">
              <div className="flex items-center gap-2 mb-4">
                <Activity className="w-4 h-4 text-indigo-400" />
                <h2 className="text-white font-semibold">Security Feed</h2>
              </div>
              <div className="space-y-3">
                {FEED_ITEMS.map((item, i) => (
                  <div key={i} className="flex items-start gap-3 p-3 rounded-lg bg-white/2 border border-white/5">
                    <span className={`badge mt-0.5 ${item.type === "INFO" ? "badge-blue" : "badge-yellow"}`}>
                      {item.type}
                    </span>
                    <div className="flex-1 min-w-0">
                      <p className="text-slate-300 text-sm">{item.text}</p>
                      <p className="text-slate-600 text-xs mt-0.5">{item.time}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Quantum status */}
            <div className="section-card">
              <div className="flex items-center gap-2 mb-4">
                <Atom className="w-4 h-4 text-indigo-400" />
                <h2 className="text-white font-semibold">Quantum Engine Status</h2>
              </div>
              <div className="space-y-3">
                {[
                  { label: "Backend",         value: "Qiskit Aer Simulator",  status: "ACTIVE" },
                  { label: "Hardware Access", value: "Not connected",         status: "PLANNED" },
                  { label: "Teleportation",   value: "Circuit implemented",   status: "ACTIVE" },
                  { label: "Bell Pairs",      value: "Circuit implemented",   status: "ACTIVE" },
                  { label: "QKD Protocol",    value: "Planned — Day 3+",      status: "PLANNED" },
                ].map(({ label, value, status }) => (
                  <div key={label} className="flex items-center justify-between py-2 border-b border-[#1e2d4a] last:border-0">
                    <span className="text-slate-400 text-sm">{label}</span>
                    <div className="flex items-center gap-2">
                      <span className="text-slate-300 text-sm">{value}</span>
                      <span className={`badge ${status === "ACTIVE" ? "badge-green" : "badge-gray"}`}>{status}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Architecture note */}
          <div className="section-card">
            <div className="flex items-center gap-2 mb-3">
              <Shield className="w-4 h-4 text-indigo-400" />
              <h2 className="text-white font-semibold">Day 1 Architecture</h2>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
              {[
                { title: "Defender Web",    desc: "Next.js 15 · TypeScript · Tailwind CSS",    status: "✓ Running" },
                { title: "Attack Lab Web",  desc: "Next.js 15 · TypeScript · Tailwind CSS",    status: "✓ Running" },
                { title: "FastAPI Backend", desc: "Python · FastAPI · Pydantic",               status: "✓ Running" },
                { title: "Quantum Engine",  desc: "Qiskit 1.x · Qiskit Aer · Teleportation", status: "✓ Implemented" },
                { title: "PostgreSQL",      desc: "Database — not wired on Day 1",             status: "⏳ Planned" },
                { title: "Redis",           desc: "Job queue — not wired on Day 1",            status: "⏳ Planned" },
              ].map(({ title, desc, status }) => (
                <div key={title} className="p-3 rounded-lg bg-white/2 border border-white/5">
                  <div className="text-white font-medium">{title}</div>
                  <div className="text-slate-500 text-xs mt-1">{desc}</div>
                  <div className="text-indigo-400 text-xs mt-2">{status}</div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
