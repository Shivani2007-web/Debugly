import { ConnectionStatus } from "@/components/ui/ConnectionStatus";

// Developer-only diagnostics. The connection-chain UI lives here, off the
// public homepage. The underlying health check is unchanged.
export default function DevHealthPage() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center gap-8 px-6 py-16">
      <header className="max-w-xl text-center">
        <h1 className="text-2xl font-semibold text-slate-100">Developer diagnostics</h1>
        <p className="mt-2 text-sm text-slate-500">
          Internal health check for the Debugly connection chain
          (frontend → backend → database).
        </p>
      </header>
      <ConnectionStatus />
      <a href="/" className="text-sm text-slate-500 underline-offset-4 hover:text-slate-300 hover:underline">
        ← Back to Debugly
      </a>
    </main>
  );
}
