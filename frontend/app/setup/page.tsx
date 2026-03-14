import { TopNav } from "@/components/top-nav";

export default function SetupPage() {
  return (
    <main className="page-shell">
      <TopNav />
      <section className="panel">
        <span className="eyebrow">Setup</span>
        <h1 className="hero-title" style={{ fontSize: "2.6rem" }}>
          Connect telemetry, define baseline coverage, keep the framing explicit.
        </h1>
        <p className="page-copy">
          This page is reserved for onboarding ActivityWatch-compatible data,
          checking CSV availability, and clarifying that MindScope estimates
          overload risk rather than diagnosing stress or mental health
          conditions.
        </p>
      </section>
    </main>
  );
}
