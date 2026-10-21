# LifeLens Ω — Changelog

All notable changes to LifeLens Ω are documented here.  
Format: [Semantic Version] — Date — Description

## [0.9.0] — 2026-10-13 — Honest Metrics Audit, Leakage Elimination & Harness Hardening

### Added
- **Leakage-Aware Evaluation Harness** (`scripts/train_and_evaluate.py`, `scripts/evaluate_tabular.py`)
  - Integrated near-duplicate text clustering ($\ge 0.90$ TF-IDF cosine similarity via Union-Find) to strictly isolate template clones within single folds.
  - Added registered-domain grouping (`--group-col`) via offline `tldextract==5.1.2` (`suffix_list_urls=()`) to eliminate multi-tenant hosting and subdomain leakage.
  - Added `--calibrate` probability calibration (`CalibratedClassifierCV(cv=5)`) fitted on the training split only.
  - Enforced strict validation-only hyperparameter $C$ and decision threshold selection (fold 1); test split (fold 0) touched exactly once.
  - Automated evaluation artifact export: `metadata.json`, `false_positives.csv`, `false_negatives.csv`, and bootstrap 95% confidence intervals (1,000 resamples).

- **Automated Regression Gate & Table Generator** (`scripts/regression_gate.py`, `scripts/make_results_table.py`)
  - Standalone regression gate comparing candidate runs against saved baselines (`models/baselines/`), enforcing PR-AUC drop $\le 0.02$ without reloading test data.
  - Automated master results generator populating `docs/RESULTS.md` with strictly `MEASURED` numbers.

- **Master Dataset Registry & Verification Cards** (`datasets/VERIFIED.md`, `docs/audit/quality_*.txt`)
  - Cryptographic verification (SHA-256) of DIFrauD, Sentinel, CompPhish, and PhishTank datasets.
  - Overlap tracking across corpora: 1 exact match between DIFrauD train and test; 0 matches between DIFrauD and Sentinel; 954 overlaps between CompPhish and PhishTank.
  - Explicit marking of gated or restricted datasets (Fraud-R1, Mendeley URL-Phish, EMSCAD) as `BLOCKED`.

- **Comprehensive Model Cards & Architectural Records** (`docs/model_cards/`, `docs/adr/0001_leakage_aware_evaluation_grouping.md`)
  - Published detailed model cards for `job_scam_v2`, `sentinel_multiclass_v2`, and `url_phishing_v2` with failure patterns, top features, and operational limitations.
  - Authored ADR 0001 formalizing the near-duplicate text and registered-domain grouping decisions.

- **Unit Test Suites** (`tests/test_train_and_evaluate.py`, `tests/test_regression_gate.py`)
  - 10 new unit tests covering near-duplicate union-find, grouped splits, threshold selection, base-rate calculations, bootstrap CI determinism, label normalization, domain group isolation, and regression gate margin thresholds.
  - Full pytest suite expanded to **283/283 tests passing**.

### Changed
- **Honest Re-Measurement of ML Models**
  - DIFrauD Job Scam F1 corrected from un-grouped claim of 0.8346 to **0.5931 [0.4897, 0.6809]** (Base-rate 5% precision 0.8959, FPR 0.0027, Gate 1: PASS).
  - Sentinel Multiclass macro-F1 corrected from un-grouped claim of 0.9837 to **0.9307** across 4 scam categories.
  - URL Phishing Char N-Gram F1 corrected from un-grouped claim of 0.9524 to **0.9287** (uncalibrated) / **0.9320** (calibrated).
  - Tabular HistGB F1 corrected from un-grouped claim of 0.9680 to **0.9421** (uncalibrated) / **0.9443** (calibrated).
  - Uncovered severe base-rate degradation for URL phishing (~31–36% precision at 5% prevalence), triggering Gate 1 failure alerts and guiding future low-prevalence threshold re-tuning.
- **Documentation Honesty Alignment**
  - Replaced "Production-Ready" across documentation with "Feature-complete prototype, not field-validated".
  - Replaced pilot-readiness badges with "Pilot kit prepared".
  - Updated all stale test counts (119, 184, 245) to the verified pytest count of **283**.

---

## [0.8.0] — 2026-10-12 — Phase 8: Production Industrialization, Observability & Runtime SRE Tooling

### Added
- **Prometheus Telemetry Engine & Scrape Exposition** (`apps/api/app/services/metrics.py`, `apps/api/app/main.py`)
  - Dedicated isolated `PROMETHEUS_REGISTRY` with official Prometheus collectors.
  - `GET /metrics` scrape endpoint matching `prometheus.yml` scrape configuration.
  - Telemetry export matching `alerts.yml` expressions: `lifelens_requests_total`, `lifelens_request_errors_total`, `lifelens_request_duration_seconds`, `lifelens_db_pool_usage`, `lifelens_adapter_health`, `lifelens_kill_switch_active`, `lifelens_service_up`, and `process_resident_memory_bytes`.
  - HTTP middleware with route path normalization preventing high-cardinality label explosion, observing per-endpoint request latencies and HTTP error types.

- **Automated SRE Health Sentinel & Self-Healing Circuit Breakers** (`apps/api/app/services/sre_sentinel.py`)
  - Proactive quality gate audit routine across all 5 verification registries (Companies House, SEC EDGAR, India MCA, UAE NER, Domain WHOIS).
  - Automatic circuit-breaker tripping: if adapter error rate exceeds threshold (`ALERT_ADAPTER_ERROR_RATE = 25%`) or quality gates fail, Sentinel immediately trips the kill-switch (`disable_feature`) and generates alert notifications.
  - Automatic auto-healing: restores kill switches (`enable_feature`) and marks adapters healthy when subsequent probes succeed.
  - Deep multi-subsystem liveness/readiness probe (`get_subsystem_health`) evaluating 6 subsystems (API Gateway, Database Pool, Redis Cache, ML Inference Engines, Registry Adapters, Federated Privacy Sandbox).
  - Runtime alert rules evaluator directly verifying active metrics against `alerts.yml` expressions (APIDown, HighErrorRate, HighLatency, DatabaseConnectionPoolExhausted, HighMemoryUsage).
  - Chaos engineering fault injection module for resilience drills and automated failover validation.

- **Phase 8 SRE & Observability API Router** (`apps/api/app/api/v1_phase8_sre.py`)
  - `GET /api/v1/sre/health` — Deep subsystem health check & readiness probe.
  - `GET /api/v1/sre/adapters` — Live adapter health matrix with kill switch status.
  - `POST /api/v1/sre/sentinel/audit` — Trigger immediate Sentinel quality gate audit.
  - `GET /api/v1/sre/sentinel/history` — Audit trail of recent Sentinel runs.
  - `GET /api/v1/sre/alerts/evaluate` — Live evaluation against `alerts.yml` rules.
  - `POST /api/v1/sre/chaos/inject` — Controlled chaos fault injection.
  - `POST /api/v1/sre/chaos/reset` — Clear chaos faults and trigger self-healing.
  - `GET /api/v1/sre/telemetry` — High-level SRE operational overview.

- **Official Python Developer SDK Observability Layer** (`src/sdk/client.py`)
  - Extended `LifeLensClient` with `get_metrics()`, `get_sre_health()`, `get_sre_adapters()`, `run_sentinel_audit()`, `evaluate_alerts()`, `inject_chaos()`, and `reset_chaos()`.

- **Web Workspace SRE & Observability Console** (`apps/web/index.html`)
  - Live subsystem readiness badges, Prometheus KPI cards (RPS, Error Rate %, p95 Latency SLA, DB Pool %).
  - Real-time Registry Adapter Health Matrix with one-click "Run Sentinel Audit" and "Resiliency Drill (Chaos)" controls.

- **Production Grafana Dashboard Specification** (`infra/monitoring/grafana_dashboard.json`)
  - Ready-to-import Grafana v10+ dashboard JSON mapping all key metrics and alerts.

- **Phase 8 Test Suite** (`tests/test_phase8_industrialization_and_observability.py`)
  - 9 unit & integration tests covering Prometheus scrape formatting, telemetry middleware, deep probes, quality gate matrix, automated circuit breaker tripping, alert rule evaluation, and Python SDK.
  - Total test suite expanded to **184/184 tests passing** with zero warnings.

---

## [0.7.0] — 2026-10-12 — Phase 7: Enterprise Platform & Developer SDK

### Added
- **Multi-Tenant Enterprise Engine** (`apps/api/app/services/enterprise_service.py`)
  - Multi-tenant organization directory with tier management (`FREE`, `STARTUP`, `ENTERPRISE`).
  - Scoped API key issuance with cryptorandom generation, SHA-256 storage, and scope-based authorization (`verify:read`, `verify:write`, `ml:inference`, `recovery:manage`, `webhooks:manage`, `admin:*`).
  - Sliding-window 60-second rate limiter enforcing tier limits (60, 300, 1,200 requests/min).
  - Webhook subscription registry and standard HMAC-SHA256 signature event dispatching (`X-LifeLens-Signature: t={timestamp},v1={hex_signature}`).
  - Enterprise telemetry and security analytics aggregation (`get_analytics`).

- **Phase 7 Enterprise & Webhooks Router** (`apps/api/app/api/v1_phase7_enterprise.py`)
  - `POST /api/v1/enterprise/organizations` — Register new organization.
  - `GET /api/v1/enterprise/organizations/{org_id}` — Query organization profile.
  - `POST /api/v1/enterprise/api-keys` — Issue new scoped API key.
  - `GET /api/v1/enterprise/api-keys` — List active organization keys.
  - `DELETE /api/v1/enterprise/api-keys/{key_id}` — Revoke API key.
  - `GET /api/v1/enterprise/analytics` — Real-time enterprise security posture analytics.
  - `POST /api/v1/webhooks/subscriptions` — Register webhook callback URL.
  - `GET /api/v1/webhooks/subscriptions` — List active webhook listeners.
  - `DELETE /api/v1/webhooks/subscriptions/{sub_id}` — Remove webhook subscription.
  - `POST /api/v1/webhooks/test-dispatch` — Test-fire signed webhook event.

- **Official Python Developer SDK** (`src/sdk/client.py`)
  - Typed `LifeLensClient` with methods for `verify_job`, `detect_scam_text`, `detect_phishing_url`, `initiate_recovery`, `get_enterprise_analytics`, and `create_webhook`.
  - Static cryptographic validation helper `LifeLensClient.verify_webhook_signature` for automated webhook callback verification.

- **Phase 7 Test Suite** (`tests/test_phase7_enterprise_and_sdk.py`)
  - 11 unit & integration tests covering org lifecycle, API key hashing, scope checks, sliding-window rate limits, HMAC signatures, telemetry analytics, and Python SDK client.
  - Repository test suite expanded to **175/175 tests passing** across all 7 phases with zero warnings.

---

## [0.6.0] — 2026-10-12 — Phase 6: Post-Incident Recovery Automation

### Added
- **Phase 6 Post-Incident Recovery Service** (`apps/api/app/services/recovery_service.py`)
  - Incident damage assessment engine (`assess_damage`) computing severity score, urgency timeframe, and containment directives across 6 incident types (Advance Fee, Malware, Credential Theft, Identity Theft, Session Hijack, Off-Platform Extortion).
  - Priority-ranked recovery workflow generator (`generate_recovery_plan`) ordering containment from Tier 1 Critical (Financial/Banking, Primary Email) to Tier 4 (Social/Regulatory).
  - Verification of the blueprint validation experiment criterion: core recovery actions structured under 30 minutes.
  - Interactive step tracking (`complete_step`) with completion timestamps and state transitions (`ACTIVE` → `IN_PROGRESS` → `COMPLETED`).
  - Trusted contact safety broadcast (`notify_trusted_contacts`) generating sanitized emergency warnings preventing secondary social engineering.
  - Formal regulatory complaint packet generator (`generate_regulatory_report`) pre-filling complaints for FBI IC3, FTC, Action Fraud UK, and NCRP India with cryptographic SHA-256 evidence audit fingerprints.

- **Phase 6 Recovery API Router** (`apps/api/app/api/v1_phase6_recovery.py`)
  - `POST /api/v1/recovery/assess` — Real-time damage assessment & blast radius calculation.
  - `POST /api/v1/recovery/initiate` — Initialize persistent recovery plan.
  - `GET /api/v1/recovery/{recovery_id}` — Plan status & step progress query.
  - `POST /api/v1/recovery/{recovery_id}/step/{step_id}/complete` — Interactive step toggle.
  - `POST /api/v1/recovery/{recovery_id}/notify-contacts` — Emergency contact broadcast.
  - `GET /api/v1/recovery/{recovery_id}/regulatory-report/{agency}` — JSON complaint packet.
  - `GET /api/v1/recovery/{recovery_id}/regulatory-report/{agency}/download` — Formatted text download.

- **Web Workspace Interactive Recovery UI** (`apps/web/index.html`)
  - Live recovery intake form with incident type selection, monetary loss calculation, and asset tracking.
  - Dynamic severity badge, urgency timer, containment directives, and progress-bar checklist.
  - One-click regulatory complaint download buttons (FBI IC3, FTC, Action Fraud, NCRP).

- **Phase 6 Test Suite** (`tests/test_phase6_recovery_automation.py`)
  - 11 unit & integration tests covering damage assessment, account tier prioritization, under-30-minute recovery time, step completion progression, emergency contact broadcasting, law enforcement packet exports, and FastAPI endpoints.
  - Total test count expanded to **164/164 tests passing** with zero warnings.

---

## [0.5.0] — 2026-09-23 — Phase 4 & Phase 5: Real-Time Meeting Shield & Unified Trust Platform

### Added
- **§94 Phase 4 Real-Time Meeting Shield** (`apps/api/app/services/meeting_shield.py`)
  - Live meeting session management (`start_session`, `ingest_audio_chunk`, `ingest_video_chunk`, `end_session`)
  - Multi-modal synthetic audio anomaly detection (voice cloning probability, pitch variance, spectral flatness)
  - Visual deepfake face-swap & lip-sync artifact scoring with immediate verification prompt triggers
  - Consent-gated audio/video inspection complying with §80 privacy mandates

- **§100/§101 Phase 5 Unified Multi-Modal CECT Reasoner** (`apps/api/app/cect/unified_reasoner.py`)
  - Canonical 10-step mental model execution (WHO → CLAIMS → EVIDENCE → INDEPENDENCE → AGREEMENT → TRAJECTORY → STRENGTH → RISK → CONFIDENCE → EMPOWERMENT)
  - Seamless orchestration of job verification, community threat intel, meeting shield alerts, and provenance ledgers

- **§13/§100 Cryptographic Trust Integrity Ledger** (`apps/api/app/services/unified_trust_ledger.py`)
  - SHA-256 hash-chained immutable audit trail for verification results
  - Cryptographic tamper-detection verification method (`verify_chain_integrity`)
  - Exportable audit trail endpoint for enterprise compliance

- **§97/§98 Federated Privacy Sandbox & Gate Validator** (`apps/api/app/security/federated_privacy_sandbox.py`)
  - Strict gate compliance: user consent verification, sample threshold gate ($N \ge 20$), Differential Privacy budget cap ($\epsilon \le 1.0$)
  - Model poisoning defense with gradient norm clipping and outlier angle rejection
  - Immediate zero-knowledge local memory purge and privacy reset

- **Phases 4 & 5 API Router** (`apps/api/app/api/v1_phases4_5.py`)
  - `POST /api/v1/meeting-shield/session/start`
  - `POST /api/v1/meeting-shield/session/audio-chunk`
  - `POST /api/v1/meeting-shield/session/video-chunk`
  - `POST /api/v1/meeting-shield/session/{id}/end`
  - `POST /api/v1/unified/verify`
  - `GET /api/v1/ledger/audit-trail`
  - `POST /api/v1/privacy-sandbox/consent`
  - `POST /api/v1/privacy-sandbox/reset/{user_id}`

- **Comprehensive Master Documentation Suite (§92)**
  - `ARCHITECTURE.md` — canonical system architecture reference
  - `API.md` — complete REST & streaming API documentation
  - `DATA_MODEL.md` — entity, claim, evidence, and ledger data schemas
  - `THREAT_MODEL.md` — STRIDE threat analysis, SSRF defenses, red-team matrix
  - `PRIVACY.md` — data governance, data minimization, consent gates

- **119 Total Unit & Integration Tests Passing** (`tests/test_phases4_5_unified_platform.py` + all previous suites)

---

## [0.4.0] — 2026-09-23 — Phase 3: Media Authenticity & Data Quality


### Added
- **§99 MediaAuthenticityProvider Protocol** (`apps/api/app/services/media_authenticity.py`)
  - Pluggable provider abstraction: any deepfake/audio detection service implements the protocol
  - `UnavailableProvider` — graceful degradation stub (§25 Failure Handling)
  - `MockDeepfakeDetectionProvider` — deterministic mock for demos and testing (§87)
  - `MediaAuthenticityOrchestrator` — routes captures to provider, enforces consent gate (§35)
  - Risk boost calculation: SYNTHETIC→0.35, LIKELY_SYNTHETIC→0.20, UNAVAILABLE→0.0

- **§4.3 Real-Time Meeting Alert Engine** (`apps/api/app/services/meeting_alert_engine.py`)
  - Tiered alerts: INFO / WARNING / HIGH / CRITICAL
  - Session summary with highest severity tracking
  - No alert fires on UNAVAILABLE results (§25 compliance)

- **§76 Data Quality Gates** (`apps/api/app/services/data_quality_gates.py`)
  - 6 gates: Coverage, Freshness, Consistency, Availability, Terms/Access, Error Behavior
  - `SourceHealthRegistry` — central health tracking for all verification sources
  - Degraded sources produce DEGRADED status rather than silent false results

- **Phase 3 REST API** (`apps/api/app/api/v1_phase3.py`)
  - `POST /api/v1/media/analyze` — media authenticity analysis
  - `GET /api/v1/media/alerts` — real-time alert history
  - `GET /api/v1/media/session-summary` — meeting session verdict
  - `POST /api/v1/quality-gates/evaluate` — evaluate data quality gates
  - `GET /api/v1/quality-gates/status` — source health registry
  - `GET /api/v1/demo/scenario` — §87 canonical demo scenario

- **Phase 3 Tests** (`tests/test_phase3_media_and_quality.py`)
  - 29 new tests: provider protocol, orchestrator routing, alert engine, data quality gates

- **README** updated badges to Phase 3 Active


Format: [Semantic Version] — Date — Description

---

## [0.3.0] — 2026-09-23 — Phase 2 Intelligence & Observability

### Added
- **§82 Community Threat Intelligence** (`apps/api/app/services/community_threat_intelligence.py`)
  - 8 built-in scam pattern catalog (UPFRONT_FEE, DOMAIN_MISMATCH, URGENCY, etc.)
  - Privacy-safe HMAC-SHA256 domain hashing — raw domains never stored
  - Anonymized community reporting endpoint (`POST /api/v1/threat-intel/report`)
  - Pattern-based risk boost computation for CECT engine integration
  - Pattern confidence auto-elevation with report-count thresholds

- **§83 Trust Trajectory Analyzer** (`apps/api/app/services/trust_trajectory.py`)
  - Stage-based escalation modeling: Initial Contact → Trust Building → Off-Platform → Sensitive Info → Financial Request → Pressure
  - Trajectory labels: `STABLE | INCREASING_RISK | HIGH_RISK_ESCALATION`
  - Trajectory score (0.0–1.0), per-stage events, signal detection
  - REST endpoint (`POST /api/v1/trust-trajectory`)

- **§70/71 Observability Service** (`apps/api/app/services/metrics.py`)
  - Telemetry: request_count, verification_success_rate, adapter_error_rate, p50/p95/p99 latency
  - Risk level distribution, feedback distribution, explanation open rate
  - Configurable alert thresholds via environment variables
  - Admin endpoint (`GET /api/v1/admin/metrics`)

- **§73 Version Manifest** (`apps/api/app/services/versioning.py`)
  - VersionManifest dataclass tagging all assessments with component versions
  - Admin endpoint (`GET /api/v1/admin/versions`)

- **§75 Kill Switches** (same module)
  - Kill switch registry for all adapters, CECT rules, and Phase 2 features
  - Runtime enable/disable without service restart
  - Admin endpoints (`GET/POST /api/v1/admin/kill-switches/*`)

- **§92 Documentation**
  - `docs/threat-model/THREAT_MODEL.md` — full threat model with STRIDE analysis
  - `docs/privacy/PRIVACY.md` — privacy principles, data classes, consent model
  - `docs/EVALUATION.md` — evaluation metrics, dataset, red-team framework
  - `docs/RED_TEAM.md` — 8 adversarial test categories with pass criteria

- **Admin API Router** (`apps/api/app/api/v1_admin.py`)
  - Metrics, alerts, versions, kill switches, threat intel, and trajectory endpoints

- **Test Suite** (`tests/test_phase2_community_and_trajectory.py`)
  - 40+ tests covering §82, §83, §70/71, §73, §75

---

## [0.2.0] — 2026-09-22 — Phase 2 Foundation

### Added
- **§81 Trust Graph Service** (`apps/api/app/services/trust_graph.py`)
  - TrustNode (COMPANY | RECRUITER | DOMAIN) and TrustEdge model
  - Scam flag tracking and trust score computation

- **§32 Behavioral Baseline Engine** (`apps/api/app/cect/behavioral_baseline.py`)
  - Drift detection for payment request timing, off-platform moves

- **§38 SSRF Security Shield** (`apps/api/app/security/ssrf.py`)
  - Blocks private IPs, cloud metadata, loopback addresses

- **Persistence fixes** — `AuditEventDB.metadata` renamed to `event_metadata`
- **Verification adapters** — Fixed `VerificationResult` init for UAE NER, US SEC, India MCA
- **47 tests passing** including benchmark targets

---

## [0.1.0] — 2026-09-21 — Phase 1 MVP

### Added
- CECT Engine: Coherence, Evidence Independence, Consistency, Trajectory
- Risk Engine: signal scoring, confidence assessment
- Explanation Engine: what was checked, what was found, verification path
- Verification Adapters: Companies House (UK), US SEC EDGAR, India MCA, UAE NER, Domain
- FastAPI backend with `/api/v1/verify-job`, `/api/v1/verifications`, `/api/v1/feedback`
- Browser Extension shell (TypeScript, React, Manifest V3)
- Source catalog (`SOURCE_CATALOG.md`)
- Docker Compose development environment
