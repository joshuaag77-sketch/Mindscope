import { BaselineProfile } from "@/components/baseline-profile";
import { TopNav } from "@/components/top-nav";

export default function BaselinePage() {
  return (
    <main className="page-shell">
      <TopNav />
      <BaselineProfile />
    </main>
  );
}
