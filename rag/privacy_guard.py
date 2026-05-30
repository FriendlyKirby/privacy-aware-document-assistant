"""Simple privacy risk checks for user questions."""

import re


HIGH_RISK_KEYWORDS = [
    "client case notes",
    "case notes",
    "full name",
    "address",
    "personal safety",
    "medical details",
    "immigration status",
    "public ai tool",
    "public ai tools",
    "paste into chatgpt",
    "paste this into chatgpt",
    "paste client",
    "identifiable client",
    "private client",
]

MEDIUM_RISK_KEYWORDS = [
    "privacy policy",
    "ai tools",
    "ai tool",
    "chatgpt",
    "allowed",
    "data privacy",
    "confidentiality",
    "client information",
    "donor information",
]

LOW_RISK_KEYWORDS = [
    "policy lookup",
    "volunteer onboarding",
    "donation receipt",
    "donation receipts",
    "social media approval",
    "leave policy",
    "onboarding steps",
]

EMAIL_PATTERN = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
PHONE_PATTERN = re.compile(
    r"(\+?1[-.\s]?)?(\(?\d{3}\)?[-.\s]?)\d{3}[-.\s]?\d{4}"
)


def assess_privacy_risk(user_question: str) -> dict:
    """Assess whether a user question may contain sensitive information.

    Args:
        user_question: The question or request entered by the user.

    Returns:
        A dictionary with risk_level, should_refuse, and warning_message.
    """
    question = user_question.lower()

    has_email = bool(EMAIL_PATTERN.search(user_question))
    has_phone = bool(PHONE_PATTERN.search(user_question))
    has_high_risk_keyword = any(keyword in question for keyword in HIGH_RISK_KEYWORDS)
    has_confidential_word = bool(re.search(r"\bconfidential\b", question))
    asks_to_use_public_ai = (
        "paste" in question
        and ("chatgpt" in question or "public ai" in question or "external ai" in question)
    )

    if (
        has_email
        or has_phone
        or has_high_risk_keyword
        or has_confidential_word
        or asks_to_use_public_ai
    ):
        return {
            "risk_level": "high",
            "should_refuse": True,
            "warning_message": (
                "High privacy risk detected. Do not enter real names, addresses, "
                "phone numbers, case notes, medical details, or confidential client "
                "information into this demo or into public AI tools."
            ),
        }

    has_medium_risk_keyword = any(keyword in question for keyword in MEDIUM_RISK_KEYWORDS)

    if has_medium_risk_keyword:
        return {
            "risk_level": "medium",
            "should_refuse": False,
            "warning_message": (
                "Privacy-related question detected. The app can continue because no "
                "obvious confidential details were found, but keep the question general "
                "and use human review for sensitive cases."
            ),
        }

    has_low_risk_keyword = any(keyword in question for keyword in LOW_RISK_KEYWORDS)

    if has_low_risk_keyword:
        return {
            "risk_level": "low",
            "should_refuse": False,
            "warning_message": "No obvious sensitive information was detected.",
        }

    return {
        "risk_level": "low",
        "should_refuse": False,
        "warning_message": (
            "No obvious sensitive information was detected. Avoid entering confidential "
            "or identifiable information."
        ),
    }
