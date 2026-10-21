/**
 * LifeLens Ω — Content Script Extractor (Vanilla JS)
 * Implementation Plan §37, §58
 */

function extractLinkedInData() {
  const jobTitle = document.querySelector(".job-details-jobs-unified-top-card__job-title, .jobs-unified-top-card__job-title, h1")?.textContent?.trim() || "";
  const companyName = document.querySelector(".job-details-jobs-unified-top-card__company-name, .jobs-unified-top-card__company-name, .jobs-company__name")?.textContent?.trim() || "";
  const location = document.querySelector(".job-details-jobs-unified-top-card__bullet, .jobs-unified-top-card__bullet")?.textContent?.trim() || "";
  const recruiter = document.querySelector(".jobs-poster__name, .hirer-card__hirer-information")?.textContent?.trim() || "";
  const description = document.querySelector("#job-details, .jobs-description__content, .jobs-box__html-content")?.textContent?.trim() || "";

  return {
    jobTitle,
    companyName,
    claimedLocation: location,
    recruiterName: recruiter,
    jobDescription: description,
    sourcePlatform: "LinkedIn",
    sourceUrl: window.location.href,
  };
}

function extractIndeedData() {
  const jobTitle = document.querySelector(".jobsearch-JobInfoHeader-title, h1")?.textContent?.trim() || "";
  const companyName = document.querySelector("[data-testid='inlineHeader-companyName'], .jobsearch-InlineCompanyRating-companyHeader")?.textContent?.trim() || "";
  const location = document.querySelector("[data-testid='inlineHeader-companyLocation']")?.textContent?.trim() || "";
  const description = document.querySelector("#jobDescriptionText")?.textContent?.trim() || "";

  return {
    jobTitle,
    companyName,
    claimedLocation: location,
    jobDescription: description,
    sourcePlatform: "Indeed",
    sourceUrl: window.location.href,
  };
}

function extractGenericJobData() {
  const scripts = Array.from(document.querySelectorAll('script[type="application/ld+json"]'));
  for (const script of scripts) {
    try {
      const data = JSON.parse(script.textContent || "{}");
      if (data["@type"] === "JobPosting" || (Array.isArray(data["@graph"]) && data["@graph"].some((item) => item["@type"] === "JobPosting"))) {
        const job = data["@type"] === "JobPosting" ? data : data["@graph"].find((item) => item["@type"] === "JobPosting");
        return {
          jobTitle: job.title || "",
          companyName: job.hiringOrganization?.name || "",
          companyWebsite: job.hiringOrganization?.sameAs || "",
          claimedLocation: job.jobLocation?.address?.addressLocality || "",
          jobDescription: job.description || "",
          sourcePlatform: "Generic Web (Schema.org)",
          sourceUrl: window.location.href,
        };
      }
    } catch {
      // ignore JSON parse errors
    }
  }

  const h1 = document.querySelector("h1")?.textContent?.trim() || "";
  const pageText = document.body.innerText || "";
  const emailMatch = pageText.match(/([a-zA-Z0-9._-]+@[a-zA-Z0-9._-]+\.[a-zA-Z0-9_-]+)/);
  const recruiterEmail = emailMatch ? emailMatch[1] : "";

  return {
    jobTitle: h1,
    companyName: document.title.split(/[-–|]/)[0]?.trim() || "",
    recruiterEmail: recruiterEmail,
    jobDescription: pageText.slice(0, 3000),
    sourcePlatform: "Generic Web",
    sourceUrl: window.location.href,
  };
}

function extractPageJobData() {
  const host = window.location.hostname.toLowerCase();
  if (host.includes("linkedin.com")) {
    return extractLinkedInData();
  } else if (host.includes("indeed.com")) {
    return extractIndeedData();
  } else {
    return extractGenericJobData();
  }
}

if (typeof chrome !== "undefined" && chrome.runtime && chrome.runtime.onMessage) {
  chrome.runtime.onMessage.addListener((message, _sender, sendResponse) => {
    if (message.type === "EXTRACT_PAGE_DATA") {
      const data = extractPageJobData();
      sendResponse({ success: true, data });
    }
    return true;
  });
}
