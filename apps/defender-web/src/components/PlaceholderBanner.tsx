export default function PlaceholderBanner({ message }: { message?: string }) {
  return (
    <div className="bg-amber-500/10 border border-amber-500/20 rounded-lg px-4 py-3 text-amber-300 text-sm mb-6">
      ⚠️ <strong>Development Placeholder:</strong>{" "}
      {message ?? "This page shows synthetic/placeholder data only. No real security events or attack results are presented."}
    </div>
  );
}
