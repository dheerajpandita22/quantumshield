import Sidebar from "@/components/Sidebar";
import TopBar from "@/components/TopBar";
import PlaceholderBanner from "@/components/PlaceholderBanner";
import { FileWarning } from "lucide-react";

export default function IncidentsPage() {
  return (
    <div className="flex min-h-screen bg-[#0a0e1a]">
      <Sidebar />
      <main className="ml-64 flex-1 flex flex-col">
        <TopBar title="Incidents" subtitle="Incident tracking and response" />
        <div className="flex-1 p-6">
          <PlaceholderBanner message="Incident management pipeline is planned for Day 2+. No incidents are currently tracked." />
          <div className="section-card flex flex-col items-center justify-center py-20 text-center">
            <FileWarning className="w-12 h-12 text-slate-600 mb-4" />
            <h2 className="text-white font-semibold text-lg mb-2">No Incidents</h2>
            <p className="text-slate-500 text-sm max-w-md">
              The incident management pipeline will be implemented in Day 2+.
              Incidents will be automatically created when the threat detection
              engine identifies security violations.
            </p>
            <div className="mt-6 px-4 py-2 bg-indigo-500/10 border border-indigo-500/20 rounded-lg text-indigo-400 text-sm">
              Planned: Automated incident classification, severity scoring, and response workflows.
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
