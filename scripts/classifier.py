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


def _contains_pattern(text: str, patterns: list[str]) -> bool:
    return any(re.search(pattern, text) for pattern in patterns)


def classify_category(title: str, description: str = "") -> str:
    title_text = _text(title)
    if _contains_pattern(
        title_text,
        [
            r"\bsupport specialist\b",
            r"\bsales operations\b",
            r"\bprocurement analyst\b",
            r"\bprogram leader\b",
        ],
    ):
        return "Other"

    checks: list[tuple[str, list[str]]] = [
        ("AI Engineer", ["ai engineer", "llm engineer", "generative ai engineer", "prompt engineer"]),
        ("ML", ["machine learning engineer", "applied scientist", "research engineer", "ml engineer"]),
        ("Data Engineer", ["data engineer", "analytics engineer", "etl engineer", "data platform engineer"]),
        ("DS", ["data scientist", "decision scientist", "product analyst", "data analyst"]),
        ("Frontend", ["frontend engineer", "front end engineer", "front-end engineer"]),
        ("Backend", ["backend engineer", "back end engineer", "back-end engineer"]),
        ("Full Stack", ["full stack engineer", "full-stack engineer", "fullstack engineer"]),
        ("Cloud", ["cloud engineer"]),
        ("DevOps", ["devops engineer", "site reliability engineer", "sre"]),
        ("Security", ["security engineer", "product security engineer", "application security engineer"]),
        ("Quant", ["quant developer", "quantitative developer", "quantitative researcher", "trading engineer"]),
        (
            "SDE",
            [
                "software engineer",
                "software development engineer",
                "sde",
                "platform engineer",
                "infrastructure engineer",
                "product engineer",
            ],
        ),
    ]
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

    if _contains_pattern(title_text, [r"\bmanager\b", r"\bdirector\b", r"\blead\b", r"\bleadership\b"]):
        return "Manager"
    if _contains_pattern(
        title_text,
        [
            r"\bintern\b",
            r"\binternship\b",
            r"\bco-?op\b",
            r"\bsummer intern\b",
        ],
    ):
        return "Intern"
    if _contains(title_text, ["new grad", "university grad", "university graduate", "new college grad", "recent graduate"]):
        return "New Grad"
    if _contains(title_text, ["early career"]):
        return "Early Career"
    if _contains(title_text, ["entry level", "associate software engineer"]):
        return "Entry"

    if _contains_pattern(title_text, [r"\bstaff\b", r"\bprincipal\b"]):
        return "Staff"
    if _contains_pattern(title_text, [r"\bsenior\b", r"\bsr\.?\b"]):
        return "Senior"
    mid_title_patterns = [
        r"\b(?:software(?: development)? engineer|sde|data scientist|data engineer|machine learning engineer|research engineer|applied scientist|engineer|scientist|developer|analyst)\s+(?:ii|2)\b",
        r"\b(?:ii|2)\s*[,/-]\s*(?:software|data|machine learning|research|applied|backend|frontend|full stack)",
    ]
    if any(re.search(pattern, title_text) for pattern in mid_title_patterns):
        return "Mid"
    entry_patterns = [
        r"\b(?:software(?: development)? engineer|sde|data scientist|data engineer|machine learning engineer|research engineer|applied scientist|engineer|scientist|developer|analyst)\s+(?:i|1)\b",
        r"\b0\s*-\s*2 years\b",
        r"\b1\+ years\b",
        r"\b2\+ years\b",
    ]
    if any(re.search(pattern, all_text) for pattern in entry_patterns):
        return "Entry"
    if _contains(all_text, ["graduate software engineer"]):
        return "New Grad"
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

NON_US_COUNTRY_CODE_PREFIXES = {
    "au",
    "br",
    "cn",
    "de",
    "fr",
    "gb",
    "ie",
    "in",
    "jp",
    "kr",
    "mx",
    "nl",
    "sg",
    "uk",
}


def parse_location(location_raw: str, description: str = "") -> ParsedLocation:
    raw = location_raw or ""
    text = raw.lower()
    combined_text = _text(raw, description)
    remote_type = "unknown"
    if _contains_pattern(
        combined_text,
        [
            r"\bvirtual\s*,?\s*(usa|us|united states)\b",
            r"\bremote\s*[-,]?\s*(usa|us|united states)\b",
            r"\b(united states|usa|us)\s+remote\b",
        ],
    ):
        remote_type = "remote"
    elif _contains_pattern(combined_text, [r"\bhybrid\b", r"\b\d+\s+days?\s*/\s*week\s+in-?office\b"]):
        remote_type = "hybrid"
    elif text.strip() in {"united states", "usa", "u.s.", "us", "multiple locations"} or re.fullmatch(
        r"\d+\s+locations?", text.strip()
    ):
        remote_type = "unknown"
    elif raw:
        remote_type = "onsite"

    if any(signal in text for signal in NON_US_SIGNALS):
        return ParsedLocation(raw, "", "", "Unknown", False, remote_type)

    if re.match(rf"^({'|'.join(sorted(NON_US_COUNTRY_CODE_PREFIXES))})[-_/,\s]", text):
        return ParsedLocation(raw, "", "", "Unknown", False, remote_type)

    if "north america" in text:
        return ParsedLocation(raw, "", "", "Unknown", False, remote_type)

    if (
        "remote - us" in text
        or "remote, us" in text
        or "remote us" in text
        or "remote - usa" in text
        or "remote, usa" in text
        or "remote usa" in text
        or "united states remote" in text
        or "remote, united states" in text
        or "united states" in text
        or "united states of america" in text
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
