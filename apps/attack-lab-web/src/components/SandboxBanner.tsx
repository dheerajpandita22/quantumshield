export default function SandboxBanner({ message }: { message?: string }) {
  return (
    <div className="bg-orange-500/10 border border-orange-500/20 rounded-lg px-4 py-3 text-orange-300 text-sm mb-6">
      🔬 <strong>Authorized Sandbox:</strong>{" "}
      {message ?? "All simulations target the local isolated sandbox only. Synthetic data. No real attacks are performed against any external system."}
    </div>
  );
}
