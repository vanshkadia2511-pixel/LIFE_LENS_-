# SOURCE_CATALOG.md
## LifeLens Ω — Verification Source Catalog
### Phase 0 Deliverable (§55–56 of Implementation Plan)

---

## Pilot Country: United Kingdom

| Field | Value |
|---|---|
| Country | United Kingdom |
| Official Registry | Companies House |
| API Available | YES — REST API (JSON) |
| Auth Required | YES — free API key via developer.company-information.service.gov.uk |
| Terms Allow Automated Access | YES — Open Government Licence |
| Base URL | `https://api.company-information.service.gov.uk` |
| Data Freshness | Near real-time |
| Coverage | All UK registered companies |

### Endpoints Used

| Endpoint | Purpose |
|---|---|
| `GET /search/companies?q={name}` | Search company by name |
| `GET /company/{company_number}` | Get company details |
| `GET /company/{company_number}/officers` | Get company officers |

### Field Mapping

| Plan Field | API Field |
|---|---|
| company_name | `company_name` |
| registration_number | `company_number` |
| status | `company_status` (active/dissolved/etc.) |
| registered_address | `registered_office_address` |
| incorporation_date | `date_of_creation` |
| company_type | `type` |

### Known Limitations

- Does not cover Scotland-only registers (separate API parity)
- Director/officer data may lag by days for new appointments
- Dissolved companies remain searchable
- Rate limit: 600 requests/5 minutes per API key

### Failure Conditions

| Condition | Adapter Response |
|---|---|
| Company not found | `NOT_FOUND` |
| API key invalid | `ACCESS_DENIED` |
| Rate limited | `RATE_LIMITED` |
| API timeout | `TIMEOUT` |
| Parse error | `PARSER_ERROR` |
| API unavailable | `SOURCE_UNAVAILABLE` |

### Fallback Behavior

When Companies House API is unavailable:
- Return `source_status: UNAVAILABLE`
- DO NOT escalate to `FRAUD` or high risk solely due to source failure
- Log adapter failure in `adapter_runs` table
- Display to user: "Company could not be verified because the registry source was temporarily unavailable."

### Test Cases

- `APPLE INC` → NOT_FOUND in UK registry (expected)
- `UNILEVER PLC` → FOUND, active
- `DISSOLVED TEST COMPANY` → FOUND, dissolved
- `""` (empty) → validation error before adapter call
- API timeout (mocked) → TIMEOUT, graceful degradation

---

## Domain Verification

| Field | Value |
|---|---|
| Method | DNS lookup + WHOIS (where available) |
| Implementation | stdlib `socket` + `httpx` HEAD request |
| Purpose | Compare recruiter email domain vs. official company domain |
| Terms | No external API required for basic domain comparison |
| Data Freshness | Real-time |

---

## Phase 2 Sources (Deferred)

- India MCA21 (company registry)
- Singapore ACRA
- US SEC EDGAR / state registries
- Recruitment agency licensing databases
- Embassy / labour information portals

---

## Acceptance Criteria (§56)

- [x] At least one authoritative company-verification source identified: **UK Companies House**
- [x] Access method documented: REST API with API key
- [x] Usage constraints documented: 600 req/5min, Open Government Licence
- [x] Data fields mapped: see table above
- [x] Failure conditions understood: 5 failure states documented
- [x] Pilot country selected: **United Kingdom**
- [ ] At least three representative job-scam scenarios defined: see `datasets/evaluation/`
- [ ] At least three legitimate job scenarios defined: see `datasets/evaluation/`
