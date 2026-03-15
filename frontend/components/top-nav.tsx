"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

export function TopNav() {
  const pathname = usePathname();

  return (
    <header className="top-nav">
      <div className="brand">
        <span className="brand-kicker">MindScope MVP</span>
        <strong className="brand-title" style={{ fontFamily: "var(--font-heading)" }}>
          Overload risk dashboard
        </strong>
      </div>
      <nav className="nav-links">
        <Link className={`nav-pill${pathname === "/" ? " nav-pill-active" : ""}`} href="/">
          Live Monitor
        </Link>
        <Link className={`nav-pill${pathname === "/baseline" ? " nav-pill-active" : ""}`} href="/baseline">
          Baseline Profile
        </Link>
        <Link className={`nav-pill${pathname === "/history" ? " nav-pill-active" : ""}`} href="/history">
          History
        </Link>
        <Link className={`nav-pill${pathname === "/setup" ? " nav-pill-active" : ""}`} href="/setup">
          Setup
        </Link>
      </nav>
    </header>
  );
}
