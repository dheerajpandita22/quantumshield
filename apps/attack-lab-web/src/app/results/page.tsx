import Sidebar from "@/components/Sidebar";
import TopBar from "@/components/TopBar";
import SandboxBanner from "@/components/SandboxBanner";
import { FileText } from "lucide-react";

export default function ResultsPage() {
  return (
    <div className="flex min-h-screen bg-[#0a0d12]">
      <Sidebar />
      <main className="ml-64 flex-1 flex flex-col">
        <TopBar title="Results & Evaluation" subtitle="Attack simulation results and analysis" />
        <div className="flex-1 p-6">
          <SandboxBanner />
          <div className="section-card flex flex-col items-center justify-center py-20 text-center">
            <FileText className="w-12 h-12 text-slate-600 mb-4" />
            <h2 className="text-white font-semibold text-lg mb-2">No Results Yet</h2>
            <p className="text-slate-500 text-sm max-w-md">
              Attack simulation results and evaluation reports will appear here
              once scenarios are executed (Day 3+). Results will never claim
              attacks against real systems — sandbox only.
            </p>
          </div>
        </div>
      </main>
    </div>
  );
}
