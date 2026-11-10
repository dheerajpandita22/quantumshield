import Sidebar from "@/components/Sidebar";
import TopBar from "@/components/TopBar";
import SandboxBanner from "@/components/SandboxBanner";
import { FlaskConical, AlertOctagon } from "lucide-react";

const SCENARIOS = [
  {
    id: "sig_forgery_v1",
    name: "Quantum Signature Forgery",
    category: "Forgery",
    risk: "HIGH",
    desc: "Attempts to forge a quantum-assisted digital signature without the original quantum state. Tests the unforgeability property of the quantum signature scheme.",
    status: "PLANNED",
    day: "Day 3+",
  },
  {
    id: "impersonation_v1",
    name: "Quantum-Channel Impersonation",
    category: "Impersonation",
    risk: "HIGH",
    desc: "Simulates an adversary impersonating a trusted sender over a quantum-authenticated channel. Tests identity verification under quantum noise.",
    status: "PLANNED",
    day: "Day 3+",
  },
  {
    id: "replay_v1",
    name: "Replay Attack",
    category: "Replay",
    risk: "MEDIUM",
    desc: "Replays a captured quantum-signed message to bypass freshness verification. Tests nonce and timestamp-based replay protection.",
    status: "PLANNED",
    day: "Day 3+",
  },
  {
    id: "channel_manip_v1",
    name: "Quantum-Channel Manipulation",
    category: "Channel Manipulation",
    risk: "HIGH",
    desc: "Introduces intercept-and-resend operations into the simulated quantum channel to test channel-integrity detection.",
    status: "PLANNED",
    day: "Day 3+",
  },
];

export default function ScenariosPage() {
  return (
    <div className="flex min-h-screen bg-[#0a0d12]">
      <Sidebar />
      <main className="ml-64 flex-1 flex flex-col">
        <TopBar title="Attack Scenarios" subtitle="Defined simulation scenarios (sandbox only)" />
        <div className="flex-1 p-6 space-y-6">
          <SandboxBanner message="All attack scenarios target the local isolated sandbox. No third-party or production systems are ever targeted." />
          <div className="grid grid-cols-1 xl:grid-cols-2 gap-4">
            {SCENARIOS.map(sc => (
              <div key={sc.id} className="section-card">
                <div className="flex items-start justify-between mb-3">
                  <div>
                    <h3 className="text-white font-semibold">{sc.name}</h3>
                    <div className="text-slate-500 text-xs font-mono mt-0.5">{sc.id}</div>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className={`badge ${sc.risk === "HIGH" ? "badge-red" : "badge-yellow"}`}>{sc.risk}</span>
                    <span className="badge badge-gray">{sc.status}</span>
                  </div>
                </div>
                <p className="text-slate-400 text-sm mb-4">{sc.desc}</p>
                <div className="flex items-center justify-between">
                  <span className="text-slate-600 text-xs">Category: {sc.category} · Available: {sc.day}</span>
                  <button disabled className="text-xs px-3 py-1.5 rounded-lg border border-[#1a2030] text-slate-600 cursor-not-allowed flex items-center gap-1.5">
                    <AlertOctagon className="w-3 h-3" /> Not Executable Yet
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      </main>
    </div>
  );
}
