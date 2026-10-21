/**
 * LifeLens Ω — Risk Card Component (Vanilla JS, no framework deps)
 * Implementation Plan §49, §50, EXT-008, EXT-009, EXT-010
 *
 * Creates a rich risk assessment card with CECT scores, evidence cards,
 * primary concerns, and a safe verification path.
 */

import type { VerificationResponse, EvidenceCard } from "../types/index";

// ── Risk color + emoji helpers ────────────────────────────────────────────────

const RISK_CLASS: Record<string, string> = {
  CRITICAL: "risk-critical",
  HIGH: "risk-high",
  MEDIUM: "risk-medium",
  LOW: "risk-low",
};

const RISK_EMOJI: Record<string, string> = {
  CRITICAL: "🔴",
  HIGH: "🟠",
  MEDIUM: "🟡",
  LOW: "🟢",
};

const RISK_BADGE: Record<string, string> = {
  CRITICAL:
    "background:#c0392b;color:#fff;padding:4px 10px;border-radius:4px;font-weight:700;",
  HIGH: "background:#e67e22;color:#fff;padding:4px 10px;border-radius:4px;font-weight:700;",
  MEDIUM:
    "background:#f39c12;color:#fff;padding:4px 10px;border-radius:4px;font-weight:700;",
  LOW: "background:#27ae60;color:#fff;padding:4px 10px;border-radius:4px;font-weight:700;",
};

function esc(str: string): string {
  const d = document.createElement("div");
  d.textContent = str;
  return d.innerHTML;
}

function pct(v: number | null | undefined): string {
  if (v === null || v === undefined) return "—";
  return `${(v * 100).toFixed(0)}%`;
}

// ── Evidence Card sub-renderer ────────────────────────────────────────────────

function renderEvidenceCard(ev: EvidenceCard): HTMLElement {
  const card = document.createElement("div");
  card.className = "ll-evidence-card";
  card.style.cssText =
    "border:1px solid #dee2e6;border-radius:6px;padding:10px 12px;margin-bottom:8px;background:#fff;font-size:12px;";

  const authorityPct = Math.round((ev.source_authority ?? 0) * 100);
  const indepPct = Math.round((ev.source_independence ?? 0) * 100);
  const userVerBadge = ev.user_verifiable
    ? '<span style="color:#27ae60;font-weight:600;">✓ User verifiable</span>'
    : '<span style="color:#7f8c8d;">⚠ Not directly verifiable</span>';

  card.innerHTML = `
    <div style="display:flex;justify-content:space-between;align-items:flex-start;">
      <div style="font-weight:600;color:#2c3e50;">${esc(ev.source_name)}</div>
      <div style="font-size:10px;color:#7f8c8d;">${esc(ev.source_type)}</div>
    </div>
    <div style="margin:5px 0;color:#34495e;">${esc(ev.observed_value)}</div>
    <div style="display:flex;gap:12px;font-size:11px;color:#7f8c8d;flex-wrap:wrap;">
      <span>Authority: <b>${authorityPct}%</b></span>
      <span>Independence: <b>${indepPct}%</b></span>
      <span>${userVerBadge}</span>
    </div>
    ${
      ev.verification_path
        ? `<div style="margin-top:5px;font-size:11px;color:#2980b9;">
        🔗 <a href="${esc(ev.verification_path)}" target="_blank" rel="noopener noreferrer" style="color:#2980b9;">
          Verify independently
        </a>
      </div>`
        : ""
    }
  `;
  return card;
}

// ── CECT Score Bar renderer ───────────────────────────────────────────────────

function renderCECTBar(label: string, value: number): HTMLElement {
  const wrapper = document.createElement("div");
  wrapper.style.cssText = "margin-bottom:6px;";
  const pctVal = Math.round(value * 100);
  let barColor = "#27ae60";
  if (pctVal < 40) barColor = "#c0392b";
  else if (pctVal < 65) barColor = "#e67e22";

  wrapper.innerHTML = `
    <div style="display:flex;justify-content:space-between;font-size:12px;margin-bottom:2px;">
      <span style="color:#34495e;">${esc(label)}</span>
      <span style="font-weight:600;color:${barColor};">${pctVal}%</span>
    </div>
    <div style="background:#ecf0f1;border-radius:3px;height:5px;overflow:hidden;">
      <div style="background:${barColor};height:100%;width:${pctVal}%;transition:width 0.5s;"></div>
    </div>
  `;
  return wrapper;
}

// ── Main RiskCard renderer ────────────────────────────────────────────────────

/**
 * Builds a complete risk assessment card from a VerificationResponse.
 * Appends it to `container`, replacing any existing card.
 */
export function renderRiskCard(
  container: HTMLElement,
  response: VerificationResponse
): void {
  // Clear previous card
  const existing = container.querySelector(".ll-risk-card");
  if (existing) existing.remove();

  const card = document.createElement("div");
  card.className = "ll-risk-card";
  card.style.cssText =
    "font-family:system-ui,sans-serif;border-radius:10px;overflow:hidden;box-shadow:0 2px 12px rgba(0,0,0,0.1);";

  const level = (response.risk_level ?? "LOW").toUpperCase();
  const riskClass = RISK_CLASS[level] ?? "risk-low";
  const emoji = RISK_EMOJI[level] ?? "🟢";
  const badge = RISK_BADGE[level] ?? RISK_BADGE["LOW"];
  const headline = response.explanation?.summary_headline ?? `${level} RISK`;
  const confidenceLabel = response.explanation?.confidence_label ?? "";

  // ── Header ────────────────────────────────────────────────────────────────
  const header = document.createElement("div");
  header.className = `ll-card-header ${riskClass}`;
  header.style.cssText = "padding:14px 16px;";
  header.innerHTML = `
    <div style="display:flex;align-items:center;gap:8px;margin-bottom:4px;">
      <span style="font-size:20px;">${emoji}</span>
      <span style="font-size:14px;font-weight:700;color:#2c3e50;">${esc(headline)}</span>
    </div>
    <div style="display:flex;gap:8px;align-items:center;flex-wrap:wrap;">
      <span style="${badge}">${level}</span>
      ${confidenceLabel ? `<span style="font-size:12px;color:#7f8c8d;">${esc(confidenceLabel)}</span>` : ""}
    </div>
  `;
  card.appendChild(header);

  const body = document.createElement("div");
  body.style.cssText = "padding:14px 16px;background:#fafafa;";

  // ── Primary concerns ──────────────────────────────────────────────────────
  const concerns = response.explanation?.what_was_found ?? [];
  if (concerns.length > 0) {
    const concernSection = document.createElement("div");
    concernSection.style.cssText = "margin-bottom:12px;";
    concernSection.innerHTML = `<div style="font-size:12px;font-weight:600;color:#7f8c8d;text-transform:uppercase;margin-bottom:6px;">Findings</div>`;
    concerns.forEach((concern) => {
      const item = document.createElement("div");
      item.style.cssText =
        "display:flex;align-items:flex-start;gap:6px;margin-bottom:4px;font-size:12px;color:#2c3e50;";
      item.innerHTML = `<span style="color:#c0392b;margin-top:1px;">⚠</span><span>${esc(concern)}</span>`;
      concernSection.appendChild(item);
    });
    body.appendChild(concernSection);
  }

  // ── CECT Scores ───────────────────────────────────────────────────────────
  const cect = response.cect_scores;
  if (cect) {
    const cectSection = document.createElement("div");
    cectSection.style.cssText = "margin-bottom:12px;";
    cectSection.innerHTML = `<div style="font-size:12px;font-weight:600;color:#7f8c8d;text-transform:uppercase;margin-bottom:6px;">CECT Analysis</div>`;

    const bars: [string, number][] = [
      ["Coherence", cect.coherence ?? 0],
      ["Evidence Independence", cect.evidence_independence ?? 0],
      ["Consistency", cect.consistency ?? 0],
      ["Trajectory Safety", cect.trajectory ?? 0],
    ];
    bars.forEach(([label, val]) => {
      cectSection.appendChild(renderCECTBar(label, val));
    });
    body.appendChild(cectSection);
  }

  // ── Recommended next steps ────────────────────────────────────────────────
  const steps = response.explanation?.recommended_next_steps ?? [];
  if (steps.length > 0) {
    const stepsSection = document.createElement("div");
    stepsSection.style.cssText = "margin-bottom:12px;";
    stepsSection.innerHTML = `<div style="font-size:12px;font-weight:600;color:#7f8c8d;text-transform:uppercase;margin-bottom:6px;">Recommended Actions</div>`;
    steps.forEach((step, i) => {
      const item = document.createElement("div");
      item.style.cssText =
        "display:flex;align-items:flex-start;gap:6px;margin-bottom:4px;font-size:12px;color:#2c3e50;";
      item.innerHTML = `<span style="color:#2980b9;font-weight:700;min-width:16px;">${i + 1}.</span><span>${esc(step)}</span>`;
      stepsSection.appendChild(item);
    });
    body.appendChild(stepsSection);
  }

  // ── Evidence Cards (collapsible) ──────────────────────────────────────────
  const evidenceCards = response.explanation?.evidence_cards ?? [];
  if (evidenceCards.length > 0) {
    const evSection = document.createElement("div");
    evSection.style.cssText = "margin-bottom:12px;";

    const evToggle = document.createElement("button");
    evToggle.style.cssText =
      "width:100%;text-align:left;background:#ecf0f1;border:none;border-radius:5px;padding:7px 10px;font-size:12px;font-weight:600;color:#34495e;cursor:pointer;display:flex;justify-content:space-between;";
    evToggle.innerHTML = `<span>📋 Evidence Cards (${evidenceCards.length})</span><span class="ev-arrow">▼</span>`;

    const evList = document.createElement("div");
    evList.style.cssText = "display:none;margin-top:6px;";
    evList.className = "ll-evidence-list";

    evidenceCards.forEach((ev) => {
      evList.appendChild(renderEvidenceCard(ev));
    });

    evToggle.addEventListener("click", () => {
      const isOpen = evList.style.display !== "none";
      evList.style.display = isOpen ? "none" : "block";
      const arrow = evToggle.querySelector(".ev-arrow");
      if (arrow) arrow.textContent = isOpen ? "▼" : "▲";
    });

    evSection.appendChild(evToggle);
    evSection.appendChild(evList);
    body.appendChild(evSection);
  }

  // ── Disclaimer ────────────────────────────────────────────────────────────
  const disclaimer =
    response.explanation?.disclaimer ??
    "A risk signal is not proof of fraud. Verify independently before sending money or sensitive documents.";
  const disc = document.createElement("div");
  disc.style.cssText =
    "font-size:10px;color:#95a5a6;border-top:1px solid #dee2e6;padding-top:8px;margin-top:4px;line-height:1.4;";
  disc.textContent = disclaimer;
  body.appendChild(disc);

  card.appendChild(body);
  container.appendChild(card);
}

/**
 * Renders a simple error state card when verification fails.
 */
export function renderErrorCard(
  container: HTMLElement,
  message: string
): void {
  const existing = container.querySelector(".ll-risk-card");
  if (existing) existing.remove();

  const card = document.createElement("div");
  card.className = "ll-risk-card";
  card.style.cssText =
    "border-radius:10px;overflow:hidden;box-shadow:0 2px 8px rgba(0,0,0,0.08);";

  card.innerHTML = `
    <div style="background:#fdf2f2;border-left:4px solid #c0392b;padding:14px 16px;">
      <div style="font-weight:700;color:#c0392b;margin-bottom:4px;">⚠ Verification Unavailable</div>
      <div style="font-size:12px;color:#7f8c8d;">${esc(message)}</div>
      <div style="font-size:11px;color:#bdc3c7;margin-top:8px;">
        Try checking the LifeLens backend is running, then retry.
      </div>
    </div>
  `;
  container.appendChild(card);
}
