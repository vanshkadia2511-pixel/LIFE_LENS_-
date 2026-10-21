/**
 * LifeLens Ω — Extension API Service
 * Implementation Plan §41, §58, §59, EXT-001 to EXT-010
 *
 * Thin typed wrapper around the LifeLens backend REST API.
 * Called exclusively from popup.js / background.js — never from content scripts.
 */

import type {
  ExtractedJobData,
  VerificationResponse,
  ExtensionMessage,
} from "../types/index";

const DEFAULT_API_BASE = "http://localhost:8000";

function getApiBase(): string {
  // Allow override via chrome storage (future feature) or env
  return DEFAULT_API_BASE;
}

/**
 * POST /api/v1/verify-job
 * Fast synchronous verification endpoint (job + recruiter enrichment).
 */
export async function verifyJob(
  extracted: ExtractedJobData
): Promise<VerificationResponse> {
  const url = `${getApiBase()}/api/v1/verify-job`;

  const payload: Record<string, string | undefined> = {
    job_title: extracted.jobTitle,
    job_description: extracted.jobDescription,
    company_name: extracted.companyName,
    company_website: extracted.companyWebsite,
    recruiter_name: extracted.recruiterName,
    recruiter_email: extracted.recruiterEmail,
    recruiter_phone: extracted.recruiterPhone,
    claimed_country: undefined,
    source_platform: extracted.sourcePlatform ?? "Browser Extension",
  };

  // Derive claimed_country from claimedLocation if possible
  if (extracted.claimedLocation) {
    payload.claimed_location = extracted.claimedLocation;
  }

  const response = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
    signal: AbortSignal.timeout(15_000),
  });

  if (!response.ok) {
    const errorText = await response.text().catch(() => "Unknown error");
    throw new Error(`LifeLens API error ${response.status}: ${errorText}`);
  }

  return response.json() as Promise<VerificationResponse>;
}

/**
 * POST /api/v1/ml/detect/text
 * Lightweight ML text scam classification (fast, pre-pipeline).
 */
export async function detectText(text: string): Promise<{
  binary_label: "SCAM" | "LEGITIMATE" | null;
  binary_is_scam: boolean | null;
  binary_confidence: number | null;
  multiclass_category: string | null;
  models_loaded: string[];
  risk_level: string | null;
}> {
  const url = `${getApiBase()}/api/v1/ml/detect/text`;
  const response = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text }),
    signal: AbortSignal.timeout(8_000),
  });
  if (!response.ok) throw new Error(`ML text detect error ${response.status}`);
  return response.json();
}

/**
 * POST /api/v1/ml/detect/url
 * Lightweight URL phishing classifier.
 */
export async function detectUrl(url: string): Promise<{
  is_phishing: boolean | null;
  confidence: number | null;
  label: "PHISHING" | "LEGITIMATE" | null;
  model_loaded: boolean;
  risk_level: string | null;
}> {
  const apiUrl = `${getApiBase()}/api/v1/ml/detect/url`;
  const response = await fetch(apiUrl, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ url }),
    signal: AbortSignal.timeout(8_000),
  });
  if (!response.ok) throw new Error(`ML URL detect error ${response.status}`);
  return response.json();
}

/**
 * POST /api/v1/feedback
 * Submit user feedback for a completed verification.
 */
export async function submitFeedback(
  requestId: string,
  feedbackType: "accurate" | "false_positive" | "false_negative" | "unclear",
  comment?: string,
  confirmedOutcome?: "LEGITIMATE" | "SCAM"
): Promise<{ status: string; request_id: string }> {
  const url = `${getApiBase()}/api/v1/feedback`;
  const response = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      request_id: requestId,
      feedback_type: feedbackType,
      comment: comment ?? "",
      confirmed_outcome: confirmedOutcome,
    }),
    signal: AbortSignal.timeout(8_000),
  });
  if (!response.ok) throw new Error(`Feedback submit error ${response.status}`);
  return response.json();
}

/**
 * GET /health
 * Liveness check — resolves true if server is reachable.
 */
export async function checkHealth(): Promise<boolean> {
  try {
    const r = await fetch(`${getApiBase()}/health`, {
      signal: AbortSignal.timeout(3_000),
    });
    return r.ok;
  } catch {
    return false;
  }
}
