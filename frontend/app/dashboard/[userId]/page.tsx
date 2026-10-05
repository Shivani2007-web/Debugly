import { DashboardView } from "@/components/dashboard/DashboardView";
import { NavBar } from "@/components/ui/NavBar";

export default async function DashboardPage({
  params,
}: {
  params: Promise<{ userId: string }>;
}) {
  const { userId } = await params;
  return (
    <main className="min-h-screen bg-panel">
      <NavBar userId={userId} active="dashboard" />
      <DashboardView userId={userId} />
    </main>
  );
}
