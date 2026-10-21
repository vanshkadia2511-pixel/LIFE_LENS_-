/**
 * LifeLens Ω — Call Guardian Side Panel Client Logic
 * MV3 CSP Compliant (no inline scripts, no eval)
 */

document.addEventListener("DOMContentLoaded", () => {
  const form = document.getElementById("invite-form");
  const inviteUrlInput = document.getElementById("invite-url");
  const platformSelect = document.getElementById("platform-hint");
  const channelSelect = document.getElementById("channel");
  const hostEmailInput = document.getElementById("host-email");
  const messageContextInput = document.getElementById("message-context");
  const consentCheckbox = document.getElementById("consent-flag");
  const inspectBtn = document.getElementById("inspect-btn");

  const resultsPanel = document.getElementById("results-panel");
  const verdictSeal = document.getElementById("verdict-seal");
  const verdictText = document.getElementById("verdict-text");
  const riskScoreValue = document.getElementById("risk-score-value");
  const signalsList = document.getElementById("signals-list");
  const recommendationsList = document.getElementById("recommendations-list");

  // Attempt to pre-fill from current active tab if it looks like a meeting URL
  if (chrome && chrome.tabs && chrome.tabs.query) {
    chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
      if (tabs && tabs[0] && tabs[0].url) {
        const url = tabs[0].url;
        if (/zoom\.us|meet\.google|teams\.microsoft|webex/i.test(url)) {
          inviteUrlInput.value = url;
        }
      }
    });
  }

  form.addEventListener("submit", async (e) => {
    e.preventDefault();

    if (!consentCheckbox.checked) {
      alert("Explicit user consent (§P5) is required to inspect meeting link metadata.");
      return;
    }

    inspectBtn.disabled = true;
    inspectBtn.textContent = "Inspecting Link Metadata...";

    const payload = {
      invite_url: inviteUrlInput.value.trim(),
      platform_hint: platformSelect.value || null,
      channel: channelSelect.value || null,
      claimed_host_email: hostEmailInput.value.trim() || null,
      message_context: messageContextInput.value.trim() || null,
      consent_flag: true,
    };

    try {
      const response = await fetch("http://localhost:8000/api/v1/call-guard/invite/check", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      if (!response.ok) {
        const err = await response.json();
        throw new Error(err.detail || "Inspection failed");
      }

      const assessment = await response.json();
      renderAssessment(assessment);
    } catch (err) {
      alert("Inspection failed: " + err.message);
    } finally {
      inspectBtn.disabled = false;
      inspectBtn.textContent = "Inspect Meeting Invite";
    }
  });

  function renderAssessment(data) {
    resultsPanel.classList.remove("hidden");
    verdictText.textContent = data.verdict;
    riskScoreValue.textContent = Number(data.risk_score).toFixed(2);

    // Apply Passport Control verdict stamps
    verdictSeal.className = "stamp-seal";
    if (data.verdict === "Verification step completed") {
      verdictSeal.textContent = "VERIFIED";
      verdictSeal.classList.add("stamp-verified");
    } else if (data.verdict === "Request looks high-risk") {
      verdictSeal.textContent = "FLAGGED";
      verdictSeal.classList.add("stamp-high-risk");
    } else {
      verdictSeal.textContent = "UNVERIFIED";
      verdictSeal.classList.add("stamp-needs-verification");
    }

    // Render Signals
    signalsList.innerHTML = "";
    if (!data.signals || data.signals.length === 0) {
      signalsList.innerHTML = `<div class="signal-item INFO"><div class="signal-desc">No anomalous or lookalike signals detected in invite metadata.</div></div>`;
    } else {
      data.signals.forEach((sig) => {
        const item = document.createElement("div");
        item.className = `signal-item ${sig.severity}`;
        item.innerHTML = `
          <div class="signal-header">${sig.signal_type} [${sig.severity}]</div>
          <div class="signal-desc">${sig.description}</div>
          <div class="signal-provenance">Source: ${sig.provenance.where} (${sig.provenance.source_reliability})</div>
        `;
        signalsList.appendChild(item);
      });
    }

    // Render Recommendations
    recommendationsList.innerHTML = "";
    if (data.recommendations && data.recommendations.length > 0) {
      data.recommendations.forEach((rec) => {
        const li = document.createElement("li");
        li.textContent = rec;
        recommendationsList.appendChild(li);
      });
    }
  }
});
