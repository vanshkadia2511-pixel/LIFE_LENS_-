"""
LifeLens Ω — Phase H: Low-Literacy Spoken Mode & Regional Language Packs
Provides spoken audio synthesis scripts and localized plain-language explanations
for users who cannot read fine-print evidence cards.
Languages: English, Hindi, Hinglish, Arabic.
Note: Field effectiveness requires in-person comprehension testing with target users.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional


@dataclass
class SpokenExplanation:
    language_code: str
    language_name: str
    spoken_audio_script: str
    core_warning_phrase: str
    simple_action_instruction: str
    field_comprehension_validated: bool = False
    disclaimer: str = (
        "Spoken scripts are linguistically reviewed drafts. Comprehensive field "
        "comprehension must be empirically tested with real community cohorts before claiming field efficacy."
    )


class LowLiteracyService:
    """
    Generates plain-language spoken audio scripts across regional languages
    for low-literacy victims of financial and impersonation scams.
    """

    LANGUAGE_PACKS: Dict[str, Dict[str, str]] = {
        "hi": {
            "name": "Hindi (हिंदी)",
            "warning": "धोखाधड़ी का बड़ा खतरा है। तुरंत रुकें।",
            "action": "अपना यूपीआई पिन कभी न डालें। किसी भी वीडियो कॉल पर न जुड़ें। पुलिस कभी वीडियो कॉल पर गिरफ़्तारी नहीं करती।",
            "script": (
                "नमस्ते। यह लाइफ लेंस सुरक्षा संदेश है। आपको जो संदेश मिला है, वह खतरनाक हो सकता है। "
                "कृपया ध्यान दें: पैसे पाने के लिए कभी यूपीआई पिन नहीं डालना होता। "
                "और भारत में कोई भी पुलिस अधिकारी वीडियो कॉल पर डिजिटल गिरफ़्तारी नहीं करता। "
                "तुरंत फ़ोन काट दें और किसी समझदार रिश्तेदार या 1930 साइबर हेल्पलाइन पर बात करें।"
            ),
        },
        "hi_en": {
            "name": "Hinglish (Hindi-English)",
            "warning": "Yeh request high-risk fraud lag rahi hai. Abhi ruko.",
            "action": "Apna UPI PIN bilkul mat daalna. Video call pe police digital arrest nahi karti.",
            "script": (
                "Hello, yeh LifeLens security alert hai. Jo message aapko mila hai, yeh high risk fraud lag raha hai. "
                "Dhyan rakhein: UPI PIN daalne se paise katte hain, aate nahi hain. "
                "Aur Mumbai ya Delhi Police kabhi Skype ya WhatsApp pe digital arrest nahi karti. "
                "Phone disconnect karein aur 1930 helpline pe call karein."
            ),
        },
        "ar": {
            "name": "Arabic (العربية)",
            "warning": "تحذير أمني: هذا الطلب يبدو عالي الخطورة واحتيالي.",
            "action": "لا تقم بتحويل أي أموال أو إرسال رموز التحقق السرية.",
            "script": (
                "مرحبًا. هذا تنبيه أمني من لايف لينس. الرسالة أو الرابط الذي تلقيته يمثل خطورة عالية. "
                "لا تقم بإدخال رمز التحقق أو تحويل أي مبالغ مالية تحت أي ضغط أو ادعاء قانوني. "
                "قم بإنهاء المكالمة فورًا والتحقق من مصدر مستقل."
            ),
        },
        "en": {
            "name": "English",
            "warning": "High risk detected. Pause immediately.",
            "action": "Do not enter your UPI PIN. Law enforcement never arrests anyone over video calls.",
            "script": (
                "Hello. This is a LifeLens Ω safety notice. The request you received looks high-risk. "
                "Entering your PIN always deducts money from your account. "
                "Police and customs officers never hold trials or demand bail over video calls. "
                "Hang up now and seek independent advice."
            ),
        },
    }

    def generate_spoken_explanation(self, language_code: str = "en") -> SpokenExplanation:
        pack = self.LANGUAGE_PACKS.get(language_code.lower(), self.LANGUAGE_PACKS["en"])
        return SpokenExplanation(
            language_code=language_code,
            language_name=pack["name"],
            spoken_audio_script=pack["script"],
            core_warning_phrase=pack["warning"],
            simple_action_instruction=pack["action"],
            field_comprehension_validated=False,
        )

    def list_supported_languages(self) -> List[Dict[str, str]]:
        return [
            {"code": k, "name": v["name"]}
            for k, v in self.LANGUAGE_PACKS.items()
        ]
