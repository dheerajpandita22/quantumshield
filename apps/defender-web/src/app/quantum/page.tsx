import Sidebar from "@/components/Sidebar";
import TopBar from "@/components/TopBar";
import PlaceholderBanner from "@/components/PlaceholderBanner";
import { Atom, CheckCircle, Circle, Info } from "lucide-react";

const QUANTUM_FEATURES = [
  { name: "Qiskit Aer Backend",        status: "implemented", detail: "AerSimulator executing circuits" },
  { name: "RY State Preparation",      status: "implemented", detail: "Parameterised RY(θ) circuits" },
  { name: "Bell Pair Generation",      status: "implemented", detail: "All four Bell states" },
  { name: "Quantum Teleportation",     status: "implemented", detail: "Full feed-forward circuit" },
  { name: "X/Y/Z Basis Measurement",  status: "implemented", detail: "Basis rotation + measurement" },
  { name: "State Verification",        status: "implemented", detail: "⟨Z⟩ and ⟨X⟩ statistical check" },
  { name: "Noise Modelling",           status: "implemented", detail: "Depolarising + amplitude damping" },
  { name: "QKD Protocol",             status: "planned",     detail: "Planned for Day 3+" },
  { name: "Quantum Signature Scheme",  status: "planned",     detail: "Planned for Day 4+" },
  { name: "Hardware Integration",      status: "planned",     detail: "IBM Quantum — requires credentials" },
];

export default function QuantumPage() {
  return (
    <div className="flex min-h-screen bg-[#0a0e1a]">
      <Sidebar />
      <main className="ml-64 flex-1 flex flex-col">
        <TopBar title="Quantum Verification" subtitle="Quantum circuit status and verification results" />
        <div className="flex-1 p-6 space-y-6">
          <PlaceholderBanner message="Quantum verification results shown here will reflect actual Qiskit Aer simulation outputs once the API is wired to this UI." />

          <div className="bg-blue-500/10 border border-blue-500/20 rounded-lg px-4 py-3 text-blue-300 text-sm flex items-start gap-3">
            <Info className="w-4 h-4 mt-0.5 shrink-0" />
            <div>
              <strong>Quantum Simulation Disclaimer:</strong> All quantum computations on Day 1 use
              Qiskit Aer (a classical simulator). Results are statistically valid simulations of
              quantum circuits. No real quantum hardware is accessed. Teleportation transfers quantum
              states — it does not protect HTTP traffic or databases directly.
            </div>
          </div>

          <div className="section-card">
            <div className="flex items-center gap-2 mb-5">
              <Atom className="w-4 h-4 text-indigo-400" />
              <h2 className="text-white font-semibold">Quantum Feature Status</h2>
            </div>
            <div className="space-y-2">
              {QUANTUM_FEATURES.map(({ name, status, detail }) => (
                <div key={name} className="flex items-center justify-between p-3 rounded-lg bg-white/2 border border-white/5">
                  <div className="flex items-center gap-3">
                    {status === "implemented"
                      ? <CheckCircle className="w-4 h-4 text-emerald-400" />
                      : <Circle className="w-4 h-4 text-slate-600" />}
                    <span className="text-slate-200 text-sm font-medium">{name}</span>
                  </div>
                  <div className="flex items-center gap-3">
                    <span className="text-slate-500 text-xs">{detail}</span>
                    <span className={`badge ${status === "implemented" ? "badge-green" : "badge-gray"}`}>
                      {status === "implemented" ? "Implemented" : "Planned"}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="section-card">
            <h2 className="text-white font-semibold mb-4">Teleportation Protocol (Day 1)</h2>
            <div className="font-mono text-xs text-slate-400 bg-[#0a0e1a] rounded-lg p-4 leading-relaxed">
              <div className="text-indigo-400 mb-2"># Teleportation circuit layout</div>
              <div>q[0]: ─── RY(θ) ─── ●──── H ─── M ───────────────── Alice</div>
              <div>q[1]: ─── H ─── ●── X ──────── M ─────────────────── Alice (Bell)</div>
              <div>q[2]: ─── X ───────────────────── [X if c0] [Z if c1] Bob</div>
              <div className="mt-2 text-slate-600"># Classical feed-forward conditions</div>
              <div>if alice[0] == 1: X(q[2])</div>
              <div>if alice[1] == 1: Z(q[2])</div>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
