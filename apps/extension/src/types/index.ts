/**
 * LifeLens Ω — Extension TypeScript Types
 * Implementation Plan §9, §15, §17, §21, §22
 */

export type RiskLevel = "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";

export interface ExtractedJobData {
  jobTitle?: string;
  companyName?: string;
  companyWebsite?: string;
  recruiterName?: string;
  recruiterEmail?: string;
  recruiterPhone?: string;
  jobDescription?: string;
  claimedLocation?: string;
  sourceUrl?: string;
  sourcePlatform?: string;
}

export interface RiskSignal {
  signal_id: string;
  category: string;
  description: string;
  severity: string;
  reliability: number;
  detected_by: string;
  evidence_ids: string[];
}

export interface EvidenceCard {
  evidence_id: string;
  source_name: string;
  source_type: string;
  observed_value: string;
  source_url?: string;
  source_authority: number;
  source_independence: number;
  user_verifiable: boolean;
  verification_path?: string;
  captured_at: string;
}

export interface CECTScores {
  coherence: number;
  evidence_independence: number;
  consistency: number;
  trajectory: number;
  confidence: number;
}

export interface ExplanationReport {
  summary_headline: string;
  confidence_label: string;
  what_was_checked: string[];
  what_was_found: string[];
  why_it_matters: string[];
  what_could_not_be_verified: string[];
  recommended_next_steps: string[];
  evidence_cards: EvidenceCard[];
  disclaimer: string;
}

export interface VerificationResponse {
  request_id: string;
  processed_at: string;
  risk_level: RiskLevel;
  risk_score: number;
  confidence: number;
  cect_scores: CECTScores;
  signals: RiskSignal[];
  primary_concerns: string[];
  mitigating_factors: string[];
  explanation: ExplanationReport;
}

export interface ExtensionMessage {
  type: "EXTRACT_PAGE_DATA" | "VERIFY_REQUEST" | "VERIFICATION_SUCCESS" | "VERIFICATION_ERROR";
  payload?: any;
}
