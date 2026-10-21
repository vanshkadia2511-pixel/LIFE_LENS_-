/**
 * LifeLens Ω — Desktop Call Guard Client Logic (Tauri Frontend)
 * Purely local, in-memory processing.
 */

const API_BASE = "http://localhost:8000/api/v1/desktop-guard";

let currentSessionId = null;
let timerInterval = null;
let remainingSeconds = 15 * 60; // 15 min cooling-off window

document.addEventListener("DOMContentLoaded", () => {
  // Elements
  const guardBadge = document.getElementById("guardBadge");
  const platformSelect = document.getElementById("platformSelect");
  const consentCheckbox = document.getElementById("consentCheckbox");
  const btnStartGuard = document.getElementById("btnStartGuard");
  const btnStopGuard = document.getElementById("btnStopGuard");

  const controlCard = document.getElementById("controlCard");
  const streamCard = document.getElementById("streamCard");
  const coachBar = document.getElementById("coachBar");
  const transcriptFeed = document.getElementById("transcriptFeed");
  const asrLatency = document.getElementById("asrLatency");

  const btnToggleCoach = document.getElementById("btnToggleCoach");
  const coachDrawer = document.getElementById("coachDrawer");
  const challengesList = document.getElementById("challengesList");

  const interstitialModal = document.getElementById("interstitialModal");
  const timerCountdown = document.getElementById("timerCountdown");
  const checklistItems = document.getElementById("checklistItems");
  const btnDismissInterstitial = document.getElementById("btnDismissInterstitial");
  const btnAbortCall = document.getElementById("btnAbortCall");

  const receiptCard = document.getElementById("receiptCard");
  const receiptSessionId = document.getElementById("receiptSessionId");
  const receiptDuration = document.getElementById("receiptDuration");
  const receiptSignals = document.getElementById("receiptSignals");
  const receiptSteps = document.getElementById("receiptSteps");
  const receiptLedgerHash = document.getElementById("receiptLedgerHash");
  const btnNewSession = document.getElementById("btnNewSession");

  // 1. Start Guard Session
  btnStartGuard.addEventListener("click", async () => {
    if (!consentCheckbox.checked) {
      alert("Explicit user consent (§P5 / §P6) is required to start Desktop Call Guard.");
      return;
    }

    try {
      const resp = await fetch(`${API_BASE}/start`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          platform: platformSelect.value,
          consent_flag: true,
        }),
      });
      const data = await resp.json();
      if (!data.is_active) {
        alert("Failed to start: " + data.status_message);
        return;
      }

      currentSessionId = data.session_id;
      guardBadge.textContent = "GUARD IS ON";
      guardBadge.className = "guard-pill pill-on";

      btnStartGuard.classList.add("hidden");
      btnStopGuard.classList.remove("hidden");
      streamCard.classList.remove("hidden");
      coachBar.classList.remove("hidden");
      receiptCard.classList.add("hidden");

      transcriptFeed.innerHTML = '<div class="feed-placeholder">Guard active. Monitoring transcript locally...</div>';
      loadLivenessChallenges(currentSessionId);
    } catch (err) {
      alert("Error starting Call Guard: " + err.message);
    }
  });

  // 2. Stop Guard (One-Click Kill-Switch)
  btnStopGuard.addEventListener("click", async () => {
    if (!currentSessionId) return;
    await endSession(false);
  });

  async function endSession(retainTranscript = false) {
    try {
      const resp = await fetch(`${API_BASE}/end`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          session_id: currentSessionId,
          opt_in_retain_transcript: retainTranscript,
        }),
      });
      const receipt = await resp.json();
      renderReceipt(receipt);

      currentSessionId = null;
      guardBadge.textContent = "GUARD IS OFF";
      guardBadge.className = "guard-pill pill-off";

      btnStartGuard.classList.remove("hidden");
      btnStopGuard.classList.add("hidden");
      streamCard.classList.add("hidden");
      coachBar.classList.add("hidden");
      interstitialModal.classList.add("hidden");
      clearInterval(timerInterval);
    } catch (err) {
      alert("Error stopping Call Guard: " + err.message);
    }
  }

  // 3. Test Phrase Injector (Simulates local Faster-Whisper ASR stream)
  document.querySelectorAll(".btn-chip").forEach((chip) => {
    chip.addEventListener("click", async () => {
      if (!currentSessionId) {
        alert("Please turn Guard ON before testing.");
        return;
      }
      const phrase = chip.getAttribute("data-phrase");
      await sendTranscriptChunk(phrase);
    });
  });

  async function sendTranscriptChunk(text) {
    const t0 = performance.now();
    try {
      const resp = await fetch(`${API_BASE}/chunk`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          session_id: currentSessionId,
          transcript_text: text,
          speaker: "remote_caller",
        }),
      });
      const alerts = await resp.json();
      const latencyMs = Math.round(performance.now() - t0);
      asrLatency.textContent = `LATENCY: ${latencyMs}ms`;

      // Append to local feed
      const line = document.createElement("div");
      line.className = alerts.length > 0 ? "transcript-line alert" : "transcript-line";
      line.innerHTML = `<strong>Caller:</strong> ${text}`;
      transcriptFeed.appendChild(line);
      transcriptFeed.scrollTop = transcriptFeed.scrollHeight;

      if (alerts.length > 0) {
        triggerInterstitial(currentSessionId);
      }
    } catch (err) {
      console.error("Chunk error:", err);
    }
  }

  // 4. Layer 3 Interstitial Modal
  async function triggerInterstitial(sessionId) {
    try {
      const resp = await fetch(`${API_BASE}/interstitial/${sessionId}`);
      if (!resp.ok) return;
      const data = await resp.json();

      interstitialModal.classList.remove("hidden");
      startCoolingTimer(data.cooling_off_minutes || 15);

      checklistItems.innerHTML = "";
      data.callback_checklist.forEach((item, idx) => {
        const li = document.createElement("li");
        li.className = "checklist-item";
        li.innerHTML = `
          <input type="checkbox" id="chk_${idx}" ${item.completed ? "checked" : ""}>
          <label for="chk_${idx}">
            <strong>Step ${idx + 1}: ${item.title}</strong><br>
            <span style="color:var(--graphite-muted);">${item.instruction}</span>
          </label>
        `;
        li.querySelector("input").addEventListener("change", async (e) => {
          if (e.target.checked) {
            await fetch(`${API_BASE}/verify-step`, {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({ session_id: sessionId, step_index: idx }),
            });
          }
        });
        checklistItems.appendChild(li);
      });
    } catch (err) {
      console.error("Interstitial error:", err);
    }
  }

  function startCoolingTimer(minutes) {
    clearInterval(timerInterval);
    remainingSeconds = minutes * 60;
    updateTimerDisplay();

    timerInterval = setInterval(() => {
      remainingSeconds--;
      if (remainingSeconds <= 0) {
        clearInterval(timerInterval);
        timerCountdown.textContent = "00:00 (EXPIRED)";
      } else {
        updateTimerDisplay();
      }
    }, 1000);
  }

  function updateTimerDisplay() {
    const mins = Math.floor(remainingSeconds / 60);
    const secs = remainingSeconds % 60;
    timerCountdown.textContent = `${String(mins).padStart(2, "0")}:${String(secs).padStart(2, "0")}`;
  }

  btnDismissInterstitial.addEventListener("click", () => {
    interstitialModal.classList.add("hidden");
  });

  btnAbortCall.addEventListener("click", async () => {
    alert("Ending protected call immediately and logging event to ledger.");
    await endSession(false);
  });

  // 5. Layer 4 Coach Drawer
  btnToggleCoach.addEventListener("click", () => {
    coachDrawer.classList.toggle("hidden");
    btnToggleCoach.textContent = coachDrawer.classList.contains("hidden") ? "View Challenges" : "Hide Challenges";
  });

  async function loadLivenessChallenges(sessionId) {
    try {
      const resp = await fetch(`${API_BASE}/challenges/${sessionId}`);
      const list = await resp.json();
      challengesList.innerHTML = "";
      list.forEach((ch) => {
        const d = document.createElement("div");
        d.className = "challenge-item";
        d.innerHTML = `
          <div class="challenge-instruction">🎯 ${ch.action_instruction}</div>
          <div class="challenge-rationale">${ch.rationale}</div>
        `;
        challengesList.appendChild(d);
      });
    } catch (err) {
      console.error("Coach error:", err);
    }
  }

  // 6. Post-Call Receipt View
  function renderReceipt(receipt) {
    receiptCard.classList.remove("hidden");
    receiptSessionId.textContent = receipt.session_id;
    receiptDuration.textContent = `${receipt.duration_seconds} seconds`;
    receiptLedgerHash.textContent = receipt.ledger_entry_hash;

    receiptSignals.innerHTML = "";
    if (receipt.signals_fired.length === 0) {
      receiptSignals.innerHTML = '<span style="color:var(--stamp-green);">No risk signals fired.</span>';
    } else {
      receipt.signals_fired.forEach((sig) => {
        const item = document.createElement("div");
        item.style.padding = "4px 0";
        item.innerHTML = `<strong style="color:var(--stamp-red);">[${sig.signal_type}]</strong> Triggered by: "${sig.trigger_phrase}"`;
        receiptSignals.appendChild(item);
      });
    }

    receiptSteps.innerHTML = "";
    if (receipt.verification_steps_completed.length === 0) {
      receiptSteps.innerHTML = "<li>None completed.</li>";
    } else {
      receipt.verification_steps_completed.forEach((step) => {
        const li = document.createElement("li");
        li.textContent = "✓ " + step;
        receiptSteps.appendChild(li);
      });
    }
  }

  btnNewSession.addEventListener("click", () => {
    receiptCard.classList.add("hidden");
    controlCard.classList.remove("hidden");
  });
});
