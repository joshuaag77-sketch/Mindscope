import { AlertStatusPanel } from "@/components/alert-status-panel";
import { NearestScenarioPanel } from "@/components/scenario-panel";
import { OverloadScoreCard } from "@/components/score-card";
import { RiskComposition } from "@/components/risk-composition";
import { StateBandBadge } from "@/components/state-band-badge";
import { SubscoreCard } from "@/components/subscore-card";
import { TopDriversList } from "@/components/top-drivers-list";
import { TopNav } from "@/components/top-nav";
import { TrendPlaceholder } from "@/components/trend-placeholder";
import { DashboardData } from "@/lib/mock-data";

export function DashboardShell({ data }: { data: DashboardData }) {
  return (
    <main className="page-shell">
      <TopNav />
      <section className="hero">
        <div className="panel hero-copy">
          <span className="eyebrow">Rules-based overload risk</span>
          <h1
            className="hero-title"
            style={{ fontFamily: "var(--font-heading)" }}
          >
            Passive desktop signals, translated into an explainable risk view.
          </h1>
          <p className="hero-body">
            MindScope compares each 10-minute activity window against a
            personalized baseline, scores overload-direction deviations, and
            keeps alerting tied to persistence instead of one noisy spike.
          </p>
          <div className="kpi-strip">
            <div className="kpi-item">
              <strong>Window start</strong>
              <p className="muted">{data.timestampLabel}</p>
            </div>
            <div className="kpi-item">
              <strong>User</strong>
              <p className="muted">{data.userId}</p>
            </div>
            <div className="kpi-item">
              <strong>Data source</strong>
              <p className="muted">{data.source}</p>
            </div>
          </div>
        </div>
        <OverloadScoreCard score={data.overloadScore} band={data.stateBand} />
      </section>

      <section className="metrics-grid">
        <div className="panel span-8">
          <h2 className="panel-title">Subsystem signals</h2>
          <p className="muted">
            Three subscores show where overload risk is coming from in the
            current window.
          </p>
          <div className="subscore-list">
            <SubscoreCard
              title="Fragmentation"
              score={data.fragmentationScore}
              description="App switching, distinct tools, and context entropy."
            />
            <SubscoreCard
              title="Focus instability"
              score={data.focusInstabilityScore}
              description="Shorter focus streaks and more work re-entry."
            />
            <SubscoreCard
              title="Interruption load"
              score={data.interruptionScore}
              description="AFK frequency and time away in the current block."
            />
          </div>
        </div>

        <div className="panel span-4">
          <h2 className="panel-title">Current band</h2>
          <p className="muted">State labels make the score easy to scan.</p>
          <StateBandBadge band={data.stateBand} />
          <ul className="status-list">
            <li>Normal: 0-39</li>
            <li>Elevated: 40-59</li>
            <li>High: 60-74</li>
            <li>Sustained Overload Risk: 75-100</li>
          </ul>
        </div>

        <div className="panel span-6">
          <TopDriversList drivers={data.topDrivers} />
        </div>

        <div className="panel span-6">
          <NearestScenarioPanel scenario={data.nearestScenario} />
        </div>

        <div className="panel span-6">
          <AlertStatusPanel alert={data.alertStatus} />
        </div>

        <div className="panel span-6">
          <RiskComposition
            fragmentation={data.fragmentationScore}
            focusInstability={data.focusInstabilityScore}
            interruption={data.interruptionScore}
          />
        </div>

        <div className="panel span-6">
          <h2 className="panel-title">Scoring posture</h2>
          <div className="kpi-strip">
            <div className="kpi-item">
              <strong>Windows tracked</strong>
              <p className="muted">{data.summary.windowsTracked}</p>
            </div>
            <div className="kpi-item">
              <strong>Average score</strong>
              <p className="muted">{Math.round(data.summary.avgScore)}</p>
            </div>
            <div className="kpi-item">
              <strong>High risk windows</strong>
              <p className="muted">{data.summary.highRiskWindows}</p>
            </div>
          </div>
          <ul className="scenario-list">
            <li>Peak score: {Math.round(data.summary.maxScore)}</li>
            <li>Latest band: {data.summary.latestBand}</li>
            <li>Persistence rules drive alerting to avoid one-off spikes.</li>
          </ul>
        </div>

        <div className="panel span-12">
          <TrendPlaceholder values={data.trendScores} labels={data.trendLabels} />
        </div>
      </section>
    </main>
  );
}
