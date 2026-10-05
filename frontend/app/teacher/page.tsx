import { NavBar } from "@/components/ui/NavBar";
import { TeacherView } from "@/components/teacher/TeacherView";

export default function TeacherPage() {
  return (
    <main className="min-h-screen bg-panel">
      <NavBar active="teacher" />
      <TeacherView />
    </main>
  );
}
