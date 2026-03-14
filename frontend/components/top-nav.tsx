import Link from "next/link";

export function TopNav() {
  return (
    <header className="top-nav">
      <div className="brand">
        <span className="brand-kicker">MindScope MVP</span>
        <strong className="brand-title" style={{ fontFamily: "var(--font-heading)" }}>
          Overload risk dashboard
        </strong>
      </div>
      <nav className="nav-links">
        <Link className="nav-pill" href="/">
          Dashboard
        </Link>
        <Link className="nav-pill" href="/setup">
          Setup
        </Link>
        <Link className="nav-pill" href="/history">
          History
        </Link>
      </nav>
    </header>
  );
}
