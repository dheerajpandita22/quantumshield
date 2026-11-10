import Sidebar from "@/components/Sidebar";
import TopBar from "@/components/TopBar";
import SandboxBanner from "@/components/SandboxBanner";
import { Play, AlertOctagon } from "lucide-react";

export default function SimulatePage() {
  return (
    <div className="flex min-h-screen bg-[#0a0d12]">
      <Sidebar />
      <main className="ml-64 flex-1 flex flex-col">
        <TopBar title="Run Simulation" subtitle="Execute individual attack scenarios" />
        <div className="flex-1 p-6">
          <SandboxBanner />
          <div className="section-card flex flex-col items-center justify-center py-20 text-center">
            <div className="p-4 bg-orange-500/10 rounded-full mb-4">
              <Play className="w-10 h-10 text-orange-400" />
            </div>
            <h2 className="text-white font-semibold text-lg mb-2">Simulation Engine — Not Yet Available</h2>
            <p className="text-slate-500 text-sm max-w-md mb-6">
              The attack simulation execution engine is planned for Day 3+.
              Scenarios are defined and the quantum backend is ready.
              Once implemented, you can select a scenario, configure parameters,
              and run it against the local sandbox.
            </p>
            <div className="flex items-center gap-2 text-orange-400 bg-orange-500/10 border border-orange-500/20 px-4 py-2 rounded-lg text-sm">
              <AlertOctagon className="w-4 h-4" />
              Sandbox-only · No external targets ever
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
