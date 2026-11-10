import Sidebar from "@/components/Sidebar";
import TopBar from "@/components/TopBar";
import SandboxBanner from "@/components/SandboxBanner";
import { List } from "lucide-react";

export default function BatchPage() {
  return (
    <div className="flex min-h-screen bg-[#0a0d12]">
      <Sidebar />
      <main className="ml-64 flex-1 flex flex-col">
        <TopBar title="Batch Testing" subtitle="Run multiple scenarios in sequence" />
        <div className="flex-1 p-6">
          <SandboxBanner />
          <div className="section-card flex flex-col items-center justify-center py-20 text-center">
            <List className="w-12 h-12 text-slate-600 mb-4" />
            <h2 className="text-white font-semibold text-lg mb-2">Batch Testing — Coming Day 3+</h2>
            <p className="text-slate-500 text-sm max-w-md">
              Batch testing allows running multiple attack scenarios in sequence and comparing results.
              Requires the simulation engine (planned Day 3+).
            </p>
          </div>
        </div>
      </main>
    </div>
  );
}
