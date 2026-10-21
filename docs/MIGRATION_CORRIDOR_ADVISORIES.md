# LifeLens Ω — Migration Corridor Labour & Embassy Advisory Sources

> **Document Status:** Curated Review & Legal Terms Audit  
> **Rule Compliance:** Strictly manual audit. No automated scraping conducted.  
> **Source Verification:** Official Ministry, Embassy, and NGO portals (marked "confirm current").  

---

## 1. Overview & Policy

Vulnerable job seekers in cross-border migration corridors face high risks of human trafficking, fake visa issuance, forced cyber-scam compound detention, and extortionate recruitment fee deduction.

To enrich LifeLens Ω's contextual verification models safely and ethically:
1. **Terms of Use First:** Scraping or harvesting is prohibited until explicit API or Open Data terms are verified.
2. **Provenance Mandatory (P3):** Every regulatory advisory references the issuing authority, issuance date, and official advisory document number.
3. **No Unverified Data:** If a portal does not provide an open machine-readable API, advisory rules are ingested through manually curated reference benchmarks, labeled `ILLUSTRATIVE` or `BENCHMARK`.

---

## 2. Curated Migration Corridor Advisory Table

| Corridor ID | Corridor Route | Issuing Authority & Portal | Terms of Use / Access Policy | Machine Readability | Scraping Status | Typical Red Flags / Scam Patterns Documented |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **CORR-01** | **India → Gulf Cooperation Council (UAE, Saudi Arabia, Qatar, Kuwait, Oman, Bahrain)** | Ministry of External Affairs (MEA) / [e-Migrate Portal](https://emigrate.gov.in) *(confirm current)* | Government Open Data / Terms of Portal Use. Commercial redistribution restricted; educational advisories permitted. | **Low** (HTML notices & downloadable PDF circulars). No public JSON REST API. | **PROHIBITED** without written permission. Manual ingestion of registered agency whitelist only. | Recruitment through unregistered agents (Sub-agents without MEA license); tourist/visit visa offered instead of employment visa; demand for medical checkup fees at non-GAMCA clinics. |
| **CORR-02** | **India → South East Asia (Cambodia, Myanmar, Laos PDR, Thailand)** | Ministry of External Affairs & Indian Embassies in Phnom Penh / Vientiane / Yangon / [MEA Public Advisories](https://mea.gov.in) *(confirm current)* | Public Diplomatic Advisory notices. Free for public citizen protection and awareness citation. | **Medium** (Static press releases, RSS feeds of diplomatic press briefings). | **ALLOWED VIA RSS/HTML CITATION**; bulk scraping discouraged. | "Data Entry Operator" / "Customer Support" lures; confiscation of passports upon arrival; transit via Bangkok into scam syndicates (e.g., Myawaddy/KK Park, Sihanoukville); demands to work on crypto/pig-butchering scams. |
| **CORR-03** | **Philippines → Middle East & East Asia** | Department of Migrant Workers (DMW) / formerly POEA / [DMW Official Portal](https://dmw.gov.ph) *(confirm current)* | Republic Act No. 11641 Open Information; public blacklists of unlicensed recruiters. | **Medium** (Searchable portal tables and PDF advisories; public license verification search). | **GATED** (Requires CAPTCHA on license verification search; scraping prohibited by terms). | Direct hiring without DMW Overseas Employment Certificate (OEC); charging placement fees for household service workers (strictly illegal under POEA rules); fly-by-night recruitment agencies. |
| **CORR-04** | **Nepal → Qatar / Malaysia / UAE** | Department of Foreign Employment (DoFE) & Ministry of Labour, Employment and Social Security / [DoFE Portal](https://dofe.gov.np) *(confirm current)* | Public Labour Welfare Notice board; free to view and verify labor permits (Shram Swikriti). | **Low** (Dynamic ASP.NET portal and scanned PDF notices in Nepali/English). | **PROHIBITED**. Periodic manual lookup of licensed agencies (Manpower agencies). | "Free Visa, Free Ticket" scheme violations (charging hidden processing fees in excess of NPR 10,000); forgery of Labour Approval barcodes; fake hotel/hospitality offers. |
| **CORR-05** | **Kenya / Uganda → Gulf & Middle East** | Ministry of Labour and Social Protection Kenya & National Employment Authority (NEA) / [NEA Portal](https://nea.go.ke) *(confirm current)* | Employment Act regulations; official directory of accredited private employment agencies. | **Medium** (Accredited agency directories published in XLSX and PDF formats). | **MANUAL REVIEW ONLY**. Batch download of approved agency roster allowed for safety checking. | Illegal recruitment for domestic or security work without attested employment contracts; retention of travel documents; unaccredited recruiting agents operating from residential apartments. |

---

## 3. Recommended Integration Strategy for LifeLens Ω

1. **Static Corroboration Engine:** Maintain an offline, verified hash list of accredited agency license IDs (e.g. MEA Registration Numbers `B-XXXX/XXX/EXP/YYYY`) updated monthly via manual verification.
2. **Red-Flag Taxonomy Rule Pack:** Map official advisory keywords (e.g. *"visit visa for work"*, *"remote digital entry compound"*, *"no contract prior to departure"*) to CECT Trajectory Stage 2/3 signals (`SIG_OFFER_IRREGULAR_VISA`, `SIG_UNREGISTERED_RECRUITER`).
3. **Citizen Verification Checklist:** On high-risk corridor offers, direct the user to the designated official government registry (e.g., *“Check agent license status on e-Migrate.gov.in prior to submitting passport or fees”*).
