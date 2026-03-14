import { TopNav } from "@/components/top-nav";

export default function HistoryPage() {
  return (
    <main className="page-shell">
      <TopNav />
      <section className="panel">
        <span className="eyebrow">History</span>
        <h1 className="hero-title" style={{ fontSize: "2.6rem" }}>
          Trend history is a placeholder for the next iteration.
        </h1>
        <p className="page-copy">
          The eventual view can chart scored windows, baseline drift, and alert
          episodes over time. For the hackathon scaffold, this page marks the
          navigation slot and keeps the routing structure ready for live data.
        </p>
      </section>
    </main>
  );
}
