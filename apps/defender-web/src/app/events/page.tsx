import Sidebar from "@/components/Sidebar";
import TopBar from "@/components/TopBar";
import PlaceholderBanner from "@/components/PlaceholderBanner";
import { AlertTriangle, Filter } from "lucide-react";

const PLACEHOLDER_EVENTS = [
  { id: "EVT-001", type: "SYSTEM_START", severity: "INFO",   source: "api",    desc: "QuantumShield API initialised.", time: "2026-11-06T13:42:00Z", resolved: true },
  { id: "EVT-002", type: "NOTICE",       severity: "NOTICE", source: "quantum",desc: "Quantum engine (Aer simulator) connected.", time: "2026-11-06T13:42:01Z", resolved: true },
  { id: "EVT-003", type: "NOTICE",       severity: "NOTICE", source: "system", desc: "Threat detection pipeline pending implementation.", time: "2026-11-06T13:42:02Z", resolved: false },
];

const SEV_COLORS: Record<string, string> = {
  INFO: "badge-blue", NOTICE: "badge-yellow", LOW: "badge-green", MEDIUM: "badge-yellow", HIGH: "badge-red", CRITICAL: "badge-red",
};

export default function EventsPage() {
  return (
    <div className="flex min-h-screen bg-[#0a0e1a]">
      <Sidebar />
      <main className="ml-64 flex-1 flex flex-col">
        <TopBar title="Security Events" subtitle="Event log and classification" />
        <div className="flex-1 p-6">
          <PlaceholderBanner message="Security events shown below are placeholder/seed data only. Real event detection is planned for Day 2+." />
          <div className="section-card">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-2">
                <AlertTriangle className="w-4 h-4 text-indigo-400" />
                <h2 className="text-white font-semibold">Event Log</h2>
              </div>
              <button className="flex items-center gap-1.5 text-slate-400 text-sm border border-[#1e2d4a] px-3 py-1.5 rounded-lg hover:bg-white/5 transition-colors">
                <Filter className="w-3.5 h-3.5" /> Filter
              </button>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-[#1e2d4a] text-left">
                    {["ID", "Type", "Severity", "Source", "Description", "Time", "Status"].map(h => (
                      <th key={h} className="pb-3 pr-4 text-slate-500 font-medium text-xs uppercase tracking-wide">{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {PLACEHOLDER_EVENTS.map(ev => (
                    <tr key={ev.id} className="border-b border-[#1e2d4a]/50 hover:bg-white/2">
                      <td className="py-3 pr-4 text-slate-400 font-mono text-xs">{ev.id}</td>
                      <td className="py-3 pr-4 text-slate-300">{ev.type}</td>
                      <td className="py-3 pr-4"><span className={`badge ${SEV_COLORS[ev.severity] || "badge-gray"}`}>{ev.severity}</span></td>
                      <td className="py-3 pr-4 text-slate-400">{ev.source}</td>
                      <td className="py-3 pr-4 text-slate-300 max-w-xs truncate">{ev.desc}</td>
                      <td className="py-3 pr-4 text-slate-500 text-xs font-mono">{ev.time}</td>
                      <td className="py-3"><span className={`badge ${ev.resolved ? "badge-green" : "badge-yellow"}`}>{ev.resolved ? "Resolved" : "Open"}</span></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
