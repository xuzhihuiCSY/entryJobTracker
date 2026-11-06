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
        ("ML", ["machine learning engineer", "applied scientist", "research engineer", "ml engineer", "research scientist", "machine learning intern", "machine learning research", "ai researcher"]),
        (
            "Data Engineer",
            ["data engineer", "data engineering intern", "analytics engineer", "etl engineer", "data platform engineer", "database administrator"],
        ),
        ("DS", ["data scientist", "data science intern", "decision scientist", "product analyst", "data analyst"]),
        ("Frontend", ["frontend engineer", "front end engineer", "front-end engineer"]),
        ("Backend", ["backend engineer", "back end engineer", "back-end engineer"]),
        ("Full Stack", ["full stack engineer", "full-stack engineer", "fullstack engineer"]),
        ("Cloud", ["cloud engineer"]),
        ("DevOps", ["devops engineer", "site reliability engineer", "sre"]),
        (
            "Security",
            [
                "security engineer",
                "product security engineer",
                "application security engineer",
                "cyber security",
                "cybersecurity",
                "incident responder",
                "security analyst",
            ],
        ),
        ("Quant", ["quant developer", "quantitative developer", "quantitative researcher", "trading engineer", "algorithm developer"]),
        (
            "SDE",
            [
                "software engineer",
                "software engineering",
                "software developer",
                "software architect",
                "software development engineer",
                "firmware engineer",
                "embedded software",
                "sde",
                "platform engineer",
                "infrastructure engineer",
                "product engineer",
                "technology development program",
                "technology internship program",
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
    if _contains_pattern(title_text, [r"\bstaff\b", r"\bprincipal\b"]):
        return "Staff"
    if _contains_pattern(title_text, [r"\bsenior\b", r"\bsr\.?\b"]):
        return "Senior"
    if _contains(title_text, ["new grad", "university grad", "university graduate", "new college grad", "recent graduate"]):
        return "New Grad"
    if _contains_pattern(title_text, [r"\bgraduates?\b", r"\bgrads\b", r"\btechnology development program\b", r"\bsoftware engineer(?:ing)? program\b.*\bfull[ -]time\b"]):
        return "New Grad"
    if _contains_pattern(title_text, [r"[-–—,|]\s*campus\s*$", r"\b(?:campus|university) (?:hire|hiring|recruiting)\b"]):
        return "New Grad"
    if _contains_pattern(title_text, [r"\bearly[- ](?:in[- ])?career\b"]):
        return "Early Career"
    if _contains_pattern(title_text, [r"\bentry[- ]level\b", r"\bassociate software engineer\b", r"\bjunior\b", r"\bjr\.?\b"]):
        return "Entry"

    if _contains_pattern(description.lower(), [
        r"\bthis (?:role|position|opportunity) is (?:designed |intended )?for (?:new|recent|university|college) grad(?:uate)?s\b",
        r"\b(?:as an?|this is an?)\s+(?:software engineering |research |summer )?intern\b",
    ]):
        return "Intern" if re.search(r"\bintern\b", description, re.I) else "New Grad"
    mid_title_patterns = [
        r"\b(?:software(?: development)? engineer|sde|data scientist|data engineer|machine learning engineer|research engineer|applied scientist|engineer|scientist|developer|analyst)\s+(?:ii|iii|2|3)\b",
        r"\b(?:ii|2)\s*[,/-]\s*(?:software|data|machine learning|research|applied|backend|frontend|full stack)",
    ]
    if any(re.search(pattern, title_text) for pattern in mid_title_patterns):
        return "Mid"
    entry_title = [
        r"\b(?:software(?: development)? engineer|sde|data scientist|data engineer|machine learning engineer|research engineer|applied scientist|engineer|scientist|developer|analyst)\s+(?:i|1)\b",
    ]
    if any(re.search(pattern, title_text) for pattern in entry_title):
        return "Entry"
    experience = re.findall(r"\b(\d+)\s*(?:\+|[-–]\s*\d+|to\s+\d+)?\s*(?:years?|yrs?)\s+(?:of\s+)?(?:(?:professional|industry|relevant|related|hands-on|software|engineering|programming|development|work|technical)\s+){0,4}experience\b", all_text)
    if experience:
        # A short preferred skill requirement must not erase a longer overall
        # experience requirement elsewhere in the JD.
        years = max(int(value) for value in experience)
        return "Mid" if years >= 3 else "Entry"
    if _contains(all_text, ["graduate software engineer"]):
        return "New Grad"
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
    from authorization import classify_authorization
    return classify_authorization(description).requires_citizenship


def detect_requires_clearance(description: str) -> bool:
    from authorization import classify_authorization
    return classify_authorization(description).requires_clearance


def detect_visa_signal(description: str) -> str:
    from authorization import classify_authorization
    return classify_authorization(description).visa_signal
