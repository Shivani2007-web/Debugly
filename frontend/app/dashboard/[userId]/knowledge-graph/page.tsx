import { NavBar } from "@/components/ui/NavBar";
import { KnowledgeGraphView } from "@/components/graph/KnowledgeGraphView";

export default async function KnowledgeGraphPage({
  params,
}: {
  params: Promise<{ userId: string }>;
}) {
  const { userId } = await params;
  return (
    <main className="min-h-screen bg-panel">
      <NavBar userId={userId} active="graph" />
      <KnowledgeGraphView userId={userId} />
    </main>
  );
}
