/**
 * LifeLens Ω — Extension Popup Controller
 * Implementation Plan §37, §59
 */

document.addEventListener("DOMContentLoaded", () => {
  const verifyForm = document.getElementById("verifyForm");
  const inputSection = document.getElementById("inputSection");
  const resultsSection = document.getElementById("resultsSection");
  const btnAutoExtract = document.getElementById("btnAutoExtract");
  const btnReset = document.getElementById("btnReset");
  const btnVerify = document.getElementById("btnVerify");
  const verifySpinner = document.getElementById("verifySpinner");
  const statusIndicator = document.getElementById("statusIndicator");

  // Form Fields
  const jobTitleInput = document.getElementById("jobTitle");
  const companyNameInput = document.getElementById("companyName");
  const claimedCountrySelect = document.getElementById("claimedCountry");
  const companyWebsiteInput = document.getElementById("companyWebsite");
  const recruiterEmailInput = document.getElementById("recruiterEmail");
  const jobDescriptionInput = document.getElementById("jobDescription");
  const consentCheckbox = document.getElementById("consentCheckbox");

  // Results elements
  const riskBanner = document.getElementById("riskBanner");
  const riskLevelPill = document.getElementById("riskLevelPill");
  const confidencePill = document.getElementById("confidencePill");
  const integrityScore = document.getElementById("integrityScore");
  const summaryHeadline = document.getElementById("summaryHeadline");
  const signalsList = document.getElementById("signalsList");
  const nextStepsList = document.getElementById("nextStepsList");
  const evidenceCardsList = document.getElementById("evidenceCardsList");
  const evidenceCount = document.getElementById("evidenceCount");

  // CECT Metrics
  const coherenceScoreVal = document.getElementById("coherenceScoreVal");
  const coherenceBar = document.getElementById("coherenceBar");
  const evidenceScoreVal = document.getElementById("evidenceScoreVal");
  const evidenceBar = document.getElementById("evidenceBar");
  const consistencyScoreVal = document.getElementById("consistencyScoreVal");
  const consistencyBar = document.getElementById("consistencyBar");
  const trajectoryScoreVal = document.getElementById("trajectoryScoreVal");
  const trajectoryBar = document.getElementById("trajectoryBar");

  // Auto-extract on popup load
  extractFromActiveTab();

  btnAutoExtract.addEventListener("click", (e) => {
    e.preventDefault();
    extractFromActiveTab();
  });

  function extractFromActiveTab() {
    statusIndicator.textContent = "Detecting...";
    if (typeof chrome !== "undefined" && chrome.tabs) {
      chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
        if (!tabs || !tabs[0] || !tabs[0].id) {
          statusIndicator.textContent = "Ready";
          return;
        }

        chrome.tabs.sendMessage(
          tabs[0].id,
          { type: "EXTRACT_PAGE_DATA" },
          (response) => {
            if (chrome.runtime.lastError || !response || !response.success) {
              console.log("No content script active or unsupported page.");
              statusIndicator.textContent = "Manual Input";
              return;
            }

            const d = response.data;
            if (d.jobTitle) jobTitleInput.value = d.jobTitle;
            if (d.companyName) companyNameInput.value = d.companyName;
            if (d.companyWebsite) companyWebsiteInput.value = d.companyWebsite;
            if (d.recruiterEmail) recruiterEmailInput.value = d.recruiterEmail;
            if (d.jobDescription) jobDescriptionInput.value = d.jobDescription.slice(0, 1500);
            statusIndicator.textContent = "Auto-Filled";
          }
        );
      });
    }
  }

  // Handle verification submission
  verifyForm.addEventListener("submit", async (e) => {
    e.preventDefault();

    if (!consentCheckbox.checked) {
      alert("Please consent to analysis before running verification (§35).");
      return;
    }

    setLoading(true);

    const payload = {
      job_title: jobTitleInput.value.trim() || undefined,
      company_name: companyNameInput.value.trim() || undefined,
      company_website: companyWebsiteInput.value.trim() || undefined,
      recruiter_email: recruiterEmailInput.value.trim() || undefined,
      job_description: jobDescriptionInput.value.trim() || undefined,
      claimed_country: claimedCountrySelect.value || "GB",
      consent_for_analysis: true,
    };

    try {
      let responseData;
      if (typeof chrome !== "undefined" && chrome.runtime && chrome.runtime.sendMessage) {
        const result = await new Promise((resolve) => {
          chrome.runtime.sendMessage({ type: "VERIFY_REQUEST", payload }, resolve);
        });

        if (!result || !result.success) {
          throw new Error(result?.error || "Failed to reach verification backend.");
        }
        responseData = result.data;
      } else {
        // Direct fetch fallback for standalone web testing
        const res = await fetch("http://localhost:8000/api/v1/verify-job", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload),
        });
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        responseData = await res.json();
      }

      renderResults(responseData);
    } catch (err) {
      console.error(err);
      alert(`Verification failed: ${err.message}. Make sure the backend API is running on localhost:8000.`);
    } finally {
      setLoading(false);
    }
  });

  function setLoading(loading) {
    if (loading) {
      btnVerify.disabled = true;
      verifySpinner.style.display = "block";
      statusIndicator.textContent = "Analyzing...";
    } else {
      btnVerify.disabled = false;
      verifySpinner.style.display = "none";
      statusIndicator.textContent = "Complete";
    }
  }

  function renderResults(data) {
    inputSection.classList.add("hidden");
    resultsSection.classList.remove("hidden");

    // 1. Risk Level Banner
    const risk = data.risk_level;
    riskBanner.className = `risk-banner risk-${risk}`;
    riskLevelPill.textContent = `${risk} RISK`;
    confidencePill.textContent = `CONFIDENCE: ${data.explanation?.confidence_label || "MEDIUM"}`;
    
    // Integrity is 1.0 - risk_score
    const integrity = (1.0 - data.risk_score).toFixed(2);
    integrityScore.textContent = integrity;
    summaryHeadline.textContent = data.explanation?.summary_headline || "Verification completed.";

    // 2. CECT Metrics
    const cect = data.cect_scores || { coherence: 1.0, evidence_independence: 1.0, consistency: 1.0, trajectory: 1.0 };
    setMetric(coherenceScoreVal, coherenceBar, cect.coherence);
    setMetric(evidenceScoreVal, evidenceBar, cect.evidence_independence);
    setMetric(consistencyScoreVal, consistencyBar, cect.consistency);
    setMetric(trajectoryScoreVal, trajectoryBar, cect.trajectory);

    // 3. Risk Signals
    signalsList.innerHTML = "";
    const concerns = data.primary_concerns || [];
    if (concerns.length === 0) {
      const li = document.createElement("li");
      li.style.color = "#34d399";
      li.textContent = "No critical risk signals or anomalies detected.";
      signalsList.appendChild(li);
    } else {
      concerns.forEach((c) => {
        const li = document.createElement("li");
        li.textContent = c;
        signalsList.appendChild(li);
      });
    }

    // 4. Next Steps
    nextStepsList.innerHTML = "";
    const steps = data.explanation?.recommended_next_steps || [];
    steps.forEach((s) => {
      const li = document.createElement("li");
      li.textContent = s;
      nextStepsList.appendChild(li);
    });

    // 5. Evidence Cards
    evidenceCardsList.innerHTML = "";
    const cards = data.explanation?.evidence_cards || [];
    evidenceCount.textContent = `${cards.length} Sources`;
    cards.forEach((card) => {
      const item = document.createElement("div");
      item.className = "evidence-item";
      item.innerHTML = `
        <div class="evidence-header">
          <span>${escapeHtml(card.source_name)}</span>
          <span>Authority: ${(card.source_authority * 100).toFixed(0)}%</span>
        </div>
        <div class="evidence-value">${escapeHtml(card.observed_value)}</div>
      `;
      evidenceCardsList.appendChild(item);
    });
  }

  function setMetric(valEl, barEl, score) {
    const pct = Math.round((score || 0) * 100);
    valEl.textContent = `${pct}%`;
    barEl.style.width = `${pct}%`;
  }

  btnReset.addEventListener("click", () => {
    resultsSection.classList.add("hidden");
    inputSection.classList.remove("hidden");
    statusIndicator.textContent = "Ready";
  });

  function escapeHtml(str) {
    if (!str) return "";
    return str.replace(/[&<>"']/g, (m) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[m]);
  }
});
