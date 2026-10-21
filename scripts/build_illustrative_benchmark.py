"""
LifeLens Ω — Illustrative Benchmark Dataset Generator (1,000 Scenarios)
Implementation Plan §62–64, Task WP-1A

Generates 1,000 balanced, high-coverage evaluation cases:
- 500 Legitimate Job Scenarios (Direct corporate, verified startups, public sector, and recognized staffing agencies)
- 500 Scam & Adversarial Scenarios (Upfront fees, equipment deposits, fake check cashing, free email impersonation, off-platform messaging, phishing, fake visas)

Label: ILLUSTRATIVE (Master Prompt P4)
"""
import json
import random
import re
from pathlib import Path

random.seed(42)

ROOT_DIR = Path(__file__).resolve().parent.parent
OUTPUT_FILE = ROOT_DIR / "datasets" / "evaluation" / "illustrative_benchmark_1000.json"

# Legitimate Corporate Employers
LEGIT_COMPANIES = [
    {"name": "DeepMind Technologies Limited", "domain": "deepmind.google", "country": "GB", "industry": "AI & Research"},
    {"name": "BBC", "domain": "bbc.co.uk", "country": "GB", "industry": "Broadcasting"},
    {"name": "AstraZeneca PLC", "domain": "astrazeneca.com", "country": "GB", "industry": "Pharmaceuticals"},
    {"name": "Unilever PLC", "domain": "unilever.com", "country": "GB", "industry": "Consumer Goods"},
    {"name": "Barclays PLC", "domain": "barclays.co.uk", "country": "GB", "industry": "Banking"},
    {"name": "Vodafone Group Plc", "domain": "vodafone.com", "country": "GB", "industry": "Telecommunications"},
    {"name": "ARM Limited", "domain": "arm.com", "country": "GB", "industry": "Semiconductors"},
    {"name": "Rolls-Royce plc", "domain": "rolls-royce.com", "country": "GB", "industry": "Aerospace"},
    {"name": "Tesco PLC", "domain": "tesco.com", "country": "GB", "industry": "Retail"},
    {"name": "GlaxoSmithKline Services Unlimited", "domain": "gsk.com", "country": "GB", "industry": "Healthcare"},
]

# Recognized Recruitment Agencies (Issue A5)
RECOGNIZED_AGENCIES = [
    {"name": "Michael Page", "domain": "michaelpage.co.uk"},
    {"name": "Robert Half", "domain": "roberthalf.co.uk"},
    {"name": "Hays Specialist Recruitment", "domain": "hays.co.uk"},
    {"name": "Adecco UK", "domain": "adecco.co.uk"},
    {"name": "Randstad UK", "domain": "randstad.co.uk"},
]

JOB_ROLES = [
    ("Software Engineer", "Developing scalable cloud microservices, reviewing pull requests, and maintaining unit test coverage across our distributed infrastructure."),
    ("Data Analyst", "Analyzing quarterly operational metrics, building automated dashboard reports in SQL, and collaborating with cross-functional product stakeholders."),
    ("Product Manager", "Defining the roadmap, interviewing end users, maintaining sprint backlogs, and coordinating release milestones with engineering."),
    ("DevOps Engineer", "Managing Kubernetes clusters, CI/CD deployment pipelines, infrastructure as code with Terraform, and Prometheus monitoring."),
    ("Cybersecurity Specialist", "Monitoring SOC alerts, performing threat modeling and penetration tests, and verifying vulnerability remediations across enterprise networks."),
    ("Financial Accountant", "Preparing monthly management accounts, balance sheet reconciliations, VAT filings, and assisting external audit teams."),
    ("Human Resources Coordinator", "Managing candidate onboarding pipelines, maintaining employee handbook records, and scheduling technical interviews."),
    ("Customer Success Manager", "Driving enterprise account renewals, delivering quarterly business reviews, and resolving escalations with engineering support."),
    ("Legal Counsel", "Drafting commercial SaaS agreements, advising on intellectual property matters, and assessing regulatory compliance risks."),
    ("Marketing Specialist", "Managing multi-channel digital campaigns, tracking conversion funnels, and optimizing search engine visibility."),
]

# Scam Patterns
SCAM_SCHEMES = [
    {
        "type": "ADVANCE_FEE",
        "description": "Congratulations! You are selected immediately. You must pay a refundable onboarding equipment fee of £150 via bank transfer before equipment can be dispatched to your home address.",
        "urgency": "Urgent joining required within 24 hours.",
    },
    {
        "type": "EQUIPMENT_CHECK",
        "description": "We will mail you a company check for $3,500. You must deposit it and wire $2,800 to our verified hardware vendor via Zelle or Western Union to purchase your home office setup.",
        "urgency": "Immediate response required to lock in your offer.",
    },
    {
        "type": "VISA_SPONSORSHIP_FRAUD",
        "description": "Guaranteed 100% employment visa and relocation package included. Wire a visa documentation processing fee of $450 to our consular immigration processing agent.",
        "urgency": "Visa quota expires today. Act fast.",
    },
    {
        "type": "OFF_PLATFORM_TELEGRAM",
        "description": "We saw your profile and you are shortlisted. Do not reply on this portal. Add our hiring manager immediately on Telegram @GlobalHR_Recruiter for interview.",
        "urgency": "Interview slots closing in 2 hours.",
    },
    {
        "type": "SENSITIVE_ID_THEFT",
        "description": "To process your employment contract, email unredacted color scans of your passport, driver's license, social security card, and front/back photos of your debit card.",
        "urgency": "Mandatory identity verification before first call.",
    },
    {
        "type": "CRYPTO_PAYOUT",
        "description": "Simple tasks from mobile. Earn 500 USDT daily with no prior experience required. Initial security deposit required to activate VIP account.",
        "urgency": "Limited slots available for today's batch.",
    },
]

FREE_EMAIL_DOMAINS = ["gmail.com", "yahoo.com", "outlook.com", "hotmail.com", "protonmail.com"]


def build_benchmark() -> None:
    cases = []

    # 1. Generate 500 Legitimate Cases
    for i in range(1, 501):
        role_title, role_desc = random.choice(JOB_ROLES)
        company = random.choice(LEGIT_COMPANIES)
        use_agency = (i % 5 == 0)  # 20% handled via recognized staffing agencies

        if use_agency:
            agency = random.choice(RECOGNIZED_AGENCIES)
            recruiter_name = f"Recruitment Consultant ({agency['name']})"
            recruiter_email = f"consultant.{i}@{agency['domain']}"
            desc = f"{role_desc} Position is represented exclusively by {agency['name']} on behalf of {company['name']}."
        else:
            recruiter_name = f"{company['name']} Talent Team"
            recruiter_email = f"careers.{i}@{company['domain']}"
            desc = f"Join {company['name']} as a {role_title}. {role_desc} Comprehensive employee benefits, competitive salary, and hybrid work."

        cases.append({
            "id": f"bench-legit-{i:04d}",
            "job_title": f"{role_title} (ID #{i})",
            "company_name": company["name"],
            "company_website": f"https://{company['domain']}",
            "recruiter_name": recruiter_name,
            "recruiter_email": recruiter_email,
            "claimed_country": company["country"],
            "job_description": desc,
            "ground_truth": "LEGITIMATE",
            "dataset_type": "ILLUSTRATIVE",
        })

    # 2. Generate 500 Scam & Adversarial Cases
    for i in range(1, 501):
        role_title, _ = random.choice(JOB_ROLES)
        scheme = random.choice(SCAM_SCHEMES)
        impersonate = (i % 2 == 0)

        if impersonate:
            real_corp = random.choice(LEGIT_COMPANIES)
            company_name = real_corp["name"]
            company_website = f"https://{real_corp['domain']}"
            # Attacker uses free mail or typo domain
            free_domain = random.choice(FREE_EMAIL_DOMAINS)
            recruiter_email = f"hiring.{real_corp['domain'].split('.')[0]}.dept@{free_domain}"
        else:
            company_name = f"Global Nexus Solutions {i} Ltd"
            company_website = f"https://global-nexus-jobs-{i}.biz"
            recruiter_email = f"recruitment@{random.choice(FREE_EMAIL_DOMAINS)}"

        desc = (
            f"URGENT HIRING: {role_title}. High compensation package with immediate onboarding. "
            f"{scheme['description']} {scheme['urgency']}"
        )

        cases.append({
            "id": f"bench-scam-{i:04d}",
            "job_title": f"{role_title} - Immediate Start (ID #{i})",
            "company_name": company_name,
            "company_website": company_website,
            "recruiter_name": f"Hiring Manager {i}",
            "recruiter_email": recruiter_email,
            "claimed_country": "GB",
            "job_description": desc,
            "ground_truth": "SCAM",
            "scam_type": scheme["type"],
            "dataset_type": "ILLUSTRATIVE",
        })

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(cases, f, indent=2)

    print(f"Generated {len(cases)} benchmark cases saved to {OUTPUT_FILE}")
    print(f"Legitimate cases: 500 | Scam/Adversarial cases: 500")


if __name__ == "__main__":
    build_benchmark()
