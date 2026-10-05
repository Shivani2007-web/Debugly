import { IDEWorkspace } from "@/components/ide/IDEWorkspace";

// Phase 2: the route segment carries a task id. In Phase 5 this becomes a real
// session id and the task is resolved from the session; the component boundary
// stays the same.
export default async function IDEPage({
  params,
}: {
  params: Promise<{ sessionId: string }>;
}) {
  const { sessionId } = await params;
  return <IDEWorkspace taskId={sessionId} />;
}
