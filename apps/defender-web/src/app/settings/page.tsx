import Sidebar from "@/components/Sidebar";
import TopBar from "@/components/TopBar";
import { Settings } from "lucide-react";

export default function SettingsPage() {
  return (
    <div className="flex min-h-screen bg-[#0a0e1a]">
      <Sidebar />
      <main className="ml-64 flex-1 flex flex-col">
        <TopBar title="Settings" subtitle="System configuration" />
        <div className="flex-1 p-6 space-y-6">
          <div className="section-card">
            <div className="flex items-center gap-2 mb-5">
              <Settings className="w-4 h-4 text-indigo-400" />
              <h2 className="text-white font-semibold">System Settings</h2>
            </div>
            <div className="space-y-4">
              {[
                { label: "API Endpoint",    value: "http://localhost:8000", type: "text" },
                { label: "Quantum Backend", value: "aer_simulator",         type: "select" },
                { label: "Default Shots",   value: "1024",                  type: "number" },
              ].map(({ label, value, type }) => (
                <div key={label} className="flex items-center justify-between py-3 border-b border-[#1e2d4a]">
                  <label className="text-slate-300 text-sm font-medium">{label}</label>
                  <input
                    type={type}
                    defaultValue={value}
                    className="bg-[#0a0e1a] border border-[#1e2d4a] rounded-lg px-3 py-1.5 text-slate-300 text-sm w-56 focus:outline-none focus:border-indigo-500/50"
                    readOnly
                  />
                </div>
              ))}
            </div>
            <p className="text-slate-600 text-xs mt-4">Settings editing will be enabled once the configuration API is wired (Day 2+).</p>
          </div>
        </div>
      </main>
    </div>
  );
}
