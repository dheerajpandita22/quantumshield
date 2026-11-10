import Sidebar from "@/components/Sidebar";
import TopBar from "@/components/TopBar";
import SandboxBanner from "@/components/SandboxBanner";
import { FlaskConical, Play, AlertOctagon, Atom, List, BarChart3 } from "lucide-react";

const STATS = [
  { label: "Scenarios Available", value: "4",   sub: "Defined · 0 Executable", icon: FlaskConical,  color: "text-orange-400", bg: "bg-orange-500/10" },
  { label: "Simulations Run",     value: "0",   sub: "Day 1 — none yet",       icon: Play,          color: "text-emerald-400",bg: "bg-emerald-500/10" },
  { label: "Batch Jobs",          value: "0",   sub: "Planned Day 2+",          icon: List,          color: "text-indigo-400", bg: "bg-indigo-500/10" },
  { label: "Results Stored",      value: "0",   sub: "Planned Day 2+",          icon: BarChart3,     color: "text-cyan-400",   bg: "bg-cyan-500/10" },
];

const SCENARIOS = [
  { id: "sig_forgery_v1",   name: "Quantum Signature Forgery",      risk: "HIGH",   status: "PLANNED" },
  { id: "impersonation_v1", name: "Quantum-Channel Impersonation",  risk: "HIGH",   status: "PLANNED" },
  { id: "replay_v1",        name: "Replay Attack",                  risk: "MEDIUM", status: "PLANNED" },
  { id: "channel_manip_v1", name: "Quantum-Channel Manipulation",   risk: "HIGH",   status: "PLANNED" },
];

export default function LabDashboardPage() {
  return (
    <div className="flex min-h-screen bg-[#0a0d12]">
      <Sidebar />
      <main className="ml-64 flex-1 flex flex-col">
        <TopBar title="Attack Lab Dashboard" subtitle="Authorized Simulation Environment" />
        <div className="flex-1 p-6 space-y-6">
          <SandboxBanner />

          <div className="bg-blue-500/10 border border-blue-500/20 rounded-lg px-4 py-3 text-blue-300 text-sm">
            ℹ️ <strong>Day 1 Status:</strong> Attack scenarios are defined but not yet executable.
            Scenario execution engine is planned for Day 3+. No simulated attacks have been run.
          </div>

          {/* Stats */}
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

          {/* Scenarios table */}
          <div className="section-card">
            <div className="flex items-center gap-2 mb-4">
              <FlaskConical className="w-4 h-4 text-orange-400" />
              <h2 className="text-white font-semibold">Attack Scenarios</h2>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-[#1a2030] text-left">
                    {["ID", "Scenario Name", "Risk Level", "Status", "Action"].map(h => (
                      <th key={h} className="pb-3 pr-4 text-slate-500 font-medium text-xs uppercase tracking-wide">{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {SCENARIOS.map(sc => (
                    <tr key={sc.id} className="border-b border-[#1a2030]/50 hover:bg-white/2">
                      <td className="py-3 pr-4 text-slate-400 font-mono text-xs">{sc.id}</td>
                      <td className="py-3 pr-4 text-slate-200">{sc.name}</td>
                      <td className="py-3 pr-4">
                        <span className={`badge ${sc.risk === "HIGH" ? "badge-red" : "badge-yellow"}`}>{sc.risk}</span>
                      </td>
                      <td className="py-3 pr-4">
                        <span className="badge badge-gray">{sc.status}</span>
                      </td>
                      <td className="py-3">
                        <button disabled className="text-xs px-3 py-1 rounded border border-[#1a2030] text-slate-600 cursor-not-allowed">
                          Not Available
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Quantum link */}
          <div className="section-card">
            <div className="flex items-center gap-2 mb-3">
              <Atom className="w-4 h-4 text-orange-400" />
              <h2 className="text-white font-semibold">Quantum Engine (Day 1)</h2>
            </div>
            <p className="text-slate-400 text-sm">
              The quantum engine is running (Qiskit Aer simulation). Attack simulations that require
              quantum computations will leverage the shared quantum backend once the scenario execution
              engine is implemented (Day 3+).
            </p>
          </div>
        </div>
      </main>
    </div>
  );
}
