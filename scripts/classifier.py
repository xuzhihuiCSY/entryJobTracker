from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class ParsedLocation:
    location_raw: str
    city: str
    state: str
    country: str
    is_us_based: bool
    remote_type: str


def _text(*parts: str | None) -> str:
    return " ".join(part or "" for part in parts).lower()


def _contains(text: str, phrases: list[str]) -> bool:
    return any(phrase in text for phrase in phrases)


def classify_category(title: str, description: str = "") -> str:
    checks: list[tuple[str, list[str]]] = [
        ("AI Engineer", ["ai engineer", "llm engineer", "generative ai engineer", "prompt engineer"]),
        ("ML", ["machine learning engineer", "applied scientist", "research engineer", "ml engineer"]),
        ("Data Engineer", ["data engineer", "analytics engineer", "etl engineer", "data platform engineer"]),
        ("DS", ["data scientist", "decision scientist", "product analyst", "data analyst"]),
        ("Backend", ["backend engineer", "back end engineer"]),
        ("Frontend", ["frontend engineer", "front end engineer"]),
        ("Full Stack", ["full stack engineer", "full-stack engineer"]),
        ("Cloud", ["cloud engineer"]),
        ("DevOps", ["devops engineer", "site reliability engineer", "sre"]),
        ("Quant", ["quant developer", "quantitative developer", "quantitative researcher", "trading engineer"]),
        (
            "SDE",
            [
                "software engineer",
                "software development engineer",
                "sde",
                "platform engineer",
                "infrastructure engineer",
            ],
        ),
    ]
    title_text = _text(title)
    for category, phrases in checks:
        if _contains(title_text, phrases):
            return category
    text = _text(title, description)
    for category, phrases in checks:
        if _contains(text, phrases):
            return category
    return "Other"


def classify_level(title: str, description: str = "") -> str:
    title_text = _text(title)
    all_text = _text(title, description)

    if _contains(title_text, ["manager", "director"]):
        return "Manager"
    if _contains(title_text, ["intern", "internship", "co-op", "summer intern"]):
        return "Intern"
    if _contains(title_text, ["new grad", "university grad", "university graduate", "new college grad", "recent graduate"]):
        return "New Grad"
    if _contains(title_text, ["early career"]):
        return "Early Career"
    if _contains(title_text, ["entry level", "associate software engineer"]):
        return "Entry"

    entry_patterns = [
        r"\bsoftware engineer\s+(i|1)\b",
        r"\bsde\s+(i|1)\b",
        r"\bdata scientist\s+(i|1)\b",
        r"\b0\s*-\s*2 years\b",
        r"\b1\+ years\b",
        r"\b2\+ years\b",
    ]
    if any(re.search(pattern, all_text) for pattern in entry_patterns):
        return "Entry"
    if _contains(all_text, ["graduate software engineer"]):
        return "New Grad"
    if _contains(title_text, ["staff", "principal"]):
        return "Staff"
    if _contains(title_text, ["senior", "sr."]):
        return "Senior"
    if _contains(title_text, ["lead"]):
        return "Manager"
    if re.search(r"\biii\b|\b3\b", title_text):
        return "Mid"
    return "Unknown"


US_CITY_STATE = {
    "seattle": ("Seattle", "WA"),
    "bellevue": ("Bellevue", "WA"),
    "redmond": ("Redmond", "WA"),
    "san francisco": ("San Francisco", "CA"),
    "bay area": ("Bay Area", "CA"),
    "new york": ("New York", "NY"),
    "austin": ("Austin", "TX"),
    "boston": ("Boston", "MA"),
    "los angeles": ("Los Angeles", "CA"),
    "mountain view": ("Mountain View", "CA"),
    "sunnyvale": ("Sunnyvale", "CA"),
    "palo alto": ("Palo Alto", "CA"),
    "san jose": ("San Jose", "CA"),
    "menlo park": ("Menlo Park", "CA"),
    "cupertino": ("Cupertino", "CA"),
    "santa clara": ("Santa Clara", "CA"),
}

NON_US_SIGNALS = [
    "canada",
    "europe",
    "india",
    "china",
    "singapore",
    "united kingdom",
    " uk",
    "germany",
    "france",
    "ireland",
    "netherlands",
    "australia",
]


def parse_location(location_raw: str) -> ParsedLocation:
    raw = location_raw or ""
    text = raw.lower()
    remote_type = "unknown"
    if "remote" in text:
        remote_type = "remote"
    elif "hybrid" in text:
        remote_type = "hybrid"
    elif raw:
        remote_type = "onsite"

    if any(signal in text for signal in NON_US_SIGNALS):
        return ParsedLocation(raw, "", "", "Unknown", False, remote_type)

    if "north america" in text:
        return ParsedLocation(raw, "", "", "Unknown", False, remote_type)

    if (
        "remote - us" in text
        or "remote us" in text
        or "united states remote" in text
        or "remote, united states" in text
        or "united states" in text
        or "usa" in text
        or "u.s." in text
    ):
        return ParsedLocation(raw, "", "", "United States", True, remote_type)

    for key, (city, state) in US_CITY_STATE.items():
        if key in text:
            return ParsedLocation(raw, city, state, "United States", True, remote_type)

    state_match = re.search(r"\b(AL|AK|AZ|AR|CA|CO|CT|DE|FL|GA|HI|IA|ID|IL|IN|KS|KY|LA|MA|MD|ME|MI|MN|MO|MS|MT|NC|ND|NE|NH|NJ|NM|NV|NY|OH|OK|OR|PA|RI|SC|SD|TN|TX|UT|VA|VT|WA|WI|WV|WY)\b", raw)
    if state_match:
        before_state = raw[: state_match.start()].strip(" ,-/")
        city = before_state.split(",")[-1].strip() if before_state else ""
        return ParsedLocation(raw, city, state_match.group(1), "United States", True, remote_type)

    return ParsedLocation(raw, "", "", "Unknown", False, remote_type)


def detect_requires_citizenship(description: str) -> bool:
    text = _text(description)
    phrases = [
        "u.s. citizenship required",
        "us citizenship required",
        "must be a u.s. citizen",
        "u.s. citizen only",
        "united states citizenship",
    ]
    return _contains(text, phrases)


def detect_requires_clearance(description: str) -> bool:
    text = _text(description)
    phrases = ["security clearance", "active clearance", "ts/sci", "top secret", "secret clearance"]
    return _contains(text, phrases)


def detect_visa_signal(description: str) -> str:
    text = _text(description)
    positive = ["visa sponsorship available", "will sponsor", "sponsorship is available"]
    negative = ["no visa sponsorship", "unable to sponsor", "cannot sponsor"]
    if _contains(text, negative):
        return "not_likely"
    if _contains(text, positive):
        return "strong"
    return "unknown"
