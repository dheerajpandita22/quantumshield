import Sidebar from "@/components/Sidebar";
import TopBar from "@/components/TopBar";
import PlaceholderBanner from "@/components/PlaceholderBanner";
import { FileBarChart } from "lucide-react";

export default function ReportsPage() {
  return (
    <div className="flex min-h-screen bg-[#0a0e1a]">
      <Sidebar />
      <main className="ml-64 flex-1 flex flex-col">
        <TopBar title="Reports" subtitle="Security and quantum verification reports" />
        <div className="flex-1 p-6">
          <PlaceholderBanner message="Reporting engine is planned for Day 2+." />
          <div className="section-card flex flex-col items-center justify-center py-20 text-center">
            <FileBarChart className="w-12 h-12 text-slate-600 mb-4" />
            <h2 className="text-white font-semibold text-lg mb-2">Reports Coming Soon</h2>
            <p className="text-slate-500 text-sm max-w-md">
              Automated security and quantum verification reports will be generated here.
              Report generation requires the event pipeline and quantum execution history
              (planned Day 2+).
            </p>
          </div>
        </div>
      </main>
    </div>
  );
}
