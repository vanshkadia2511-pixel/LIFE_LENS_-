/**
 * LifeLens Ω — Background Service Worker
 * Implementation Plan §36, §37, §59
 */

const API_BASE_URL = "http://localhost:8000";

chrome.runtime.onInstalled.addListener(() => {
  console.log("LifeLens Ω Extension Installed Successfully.");
});

async function verifyJobWithApi(payload) {
  try {
    const response = await fetch(`${API_BASE_URL}/api/v1/verify-job`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(payload),
    });

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`API returned ${response.status}: ${errorText}`);
    }

    const data = await response.json();
    return { success: true, data };
  } catch (err) {
    console.error("Verification API Error:", err);
    return { success: false, error: err.message || "Failed to contact LifeLens API" };
  }
}

chrome.runtime.onMessage.addListener((message, _sender, sendResponse) => {
  if (message.type === "VERIFY_REQUEST") {
    verifyJobWithApi(message.payload).then((result) => {
      sendResponse(result);
    });
    return true; // async sendResponse
  }
});
