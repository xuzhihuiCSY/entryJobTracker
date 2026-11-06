"""Conservative, evidence-backed detection of PhD-only eligibility.

Only a positive requirement hides a posting. Missing descriptions and ambiguous
mentions remain unknown; a master's/bachelor's alternative is never PhD-only.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from html import unescape

from bs4 import BeautifulSoup


PHD = re.compile(r"\b(?:ph\s*\.?\s*d\b\.?|d\s*\.?\s*phil\b\.?|doctor of philosophy\b|doctorate\b|doctoral\b)", re.I)
OTHER_DEGREE = re.compile(
    r"\b(?:master(?:['’]s|s)?|bachelor(?:['’]s|s)?|mba|ms|msc|bs|bsc|(?:other|another|equivalent) degree)\b", re.I
)
PREFERRED = re.compile(r"\b(?:prefer(?:red|ably)?|desired|desirable|ideally|a plus|nice[- ]to[- ]have|bonus)\b", re.I)
NEGATED = re.compile(
    r"\b(?:no PhD (?:is )?(?:required|needed|necessary)|PhD (?:is )?not (?:required|needed|necessary)|"
    r"PhD (?:isn't|isn’t) (?:required|needed|necessary)|(?:do not|don't|don’t) (?:need|require) (?:a )?PhD|"
    r"without (?:a |an )?PhD|PhD (?:is )?optional)\b", re.I
)
EQUIVALENT = re.compile(
    r"\b(?:or|and/or)\s+(?:(?:have|possess|with)\s+)?(?:an?\s+)?"
    r"(?:(?:equivalent|comparable|relevant|significant|substantial|strong|demonstrated|practical|professional|industry|work|research|applied)\s+){0,5}"
    r"(?:experience|expertise|track record)\b",
    re.I,
)
REQUIRED = re.compile(
    r"\b(?:required|requirement|must|minimum|need|hold|have|earned|completed|possess|"
    r"pursuing|enrolled|working toward|working towards|currently undertaking|"
    r"expected to (?:complete|obtain)|will (?:complete|obtain))\b", re.I
)
REQUIRED_HEADING = re.compile(
    r"^(?:(?:basic|minimum|required|essential) qualifications|qualifications|requirements|"
    r"what you (?:bring|have|need)|who you are|your (?:skills|background)|"
    r"you(?:'|’)ll (?:need|bring)|we(?:'|’)re looking for)\s*:?$", re.I
)
PREFERRED_HEADING = re.compile(
    r"^(?:(?:preferred|desired|additional) qualifications|preferred requirements|"
    r"nice[- ]to[- ]haves?|bonus(?: points)?|ideally you(?:'|’)ll have)\s*:?$", re.I
)


@dataclass(frozen=True)
class EducationSignal:
    phd_requirement: str = "unknown"
    phd_evidence: str = ""


def _normalize(text: str) -> str:
    text = PHD.sub("PhD", text)
    # Normalize dotted abbreviations before splitting sentences.
    text = re.sub(r"\bM\s*\.\s*S\b\.?", "MS", text, flags=re.I)
    text = re.sub(r"\bB\s*\.\s*S\b\.?", "BS", text, flags=re.I)
    return re.sub(r"[ \t\r\f\v]+", " ", text).strip()


def _requirement_lines(description: str) -> list[str]:
    decoded = unescape(description)
    if "<" not in decoded:
        return [line.strip(" \t-*•:") for line in _normalize(decoded).splitlines() if line.strip(" \t-*•:")]
    soup = BeautifulSoup(decoded, "html.parser")
    for element in soup.find_all(["p", "li", "div", "h1", "h2", "h3", "h4", "br"]):
        element.insert_before("\n")
        element.insert_after("\n")
    text = _normalize(soup.get_text(" "))
    return [line.strip(" \t-*•:") for line in text.splitlines() if line.strip(" \t-*•:")]


def _alternative(text: str) -> bool:
    if EQUIVALENT.search(text):
        return True
    if not OTHER_DEGREE.search(text):
        return False
    # A degree list or explicit "or" allows another qualification. Merely
    # mentioning an earlier bachelor's degree does not waive a required PhD.
    degree_list = re.sub(OTHER_DEGREE, "DEGREE", text)
    degree_list = degree_list.replace("PhD", "DEGREE")
    return bool(re.search(r"DEGREE[^.!?;]*\bor\b[^.!?;]*DEGREE|DEGREE\s*[/,]\s*DEGREE", degree_list, re.I))


def classify_phd_requirement(title: str, description: str = "") -> EducationSignal:
    title = _normalize(title)
    title_signal = EducationSignal()
    if "PhD" in title and not re.search(r"\brecruit(?:er|ing)\b|talent acquisition", title, re.I):
        if NEGATED.search(title) or _alternative(title):
            title_signal = EducationSignal("optional", title)
        elif PREFERRED.search(title):
            title_signal = EducationSignal("preferred", title)
        else:
            title_signal = EducationSignal("required", title)

    signals: list[EducationSignal] = []
    section = "unknown"
    lines = _requirement_lines(description)
    for index, line in enumerate(lines):
        if PREFERRED_HEADING.fullmatch(line):
            section = "preferred"
            continue
        if "PhD" not in line and len(line) < 150 and PREFERRED.search(line):
            section = "preferred"
            continue
        if REQUIRED_HEADING.fullmatch(line):
            section = "required"
            continue
        # Do not let a qualifications section bleed into benefits/team copy.
        if re.fullmatch(r"(?:responsibilities|what you(?:'|’)ll do|about (?:us|the team|you)|benefits|compensation|our team|your impact)", line, re.I):
            section = "unknown"
            continue
        # Alternative eligibility paths are sometimes separate bullets joined
        # by "OR". Keep that connection without treating an entire JD as one
        # qualifications list.
        context = " ".join(lines[max(0, index - 2):index + 2])
        line_alternative = "PhD" in line and _alternative(line.replace(";", ","))
        adjacent_alternative = "PhD" in line and bool(re.search(r"\bor\s+(?:PhD|an?\s+PhD)|\bOR\b", context)) and _alternative(context.replace(";", ",").replace(".", ","))
        experience_path = bool(re.match(r"^(?:for\s+)?PhD(?:\s+holders?)?\s*:", line, re.I)) and bool(OTHER_DEGREE.search(context))
        for sentence in re.split(r"(?<=[.!?;])\s+", line):
            if "PhD" not in sentence:
                continue
            evidence = sentence[:500]
            if NEGATED.search(sentence) or _alternative(sentence) or line_alternative or adjacent_alternative or experience_path:
                signals.append(EducationSignal("optional", evidence))
            elif PREFERRED.search(sentence) or section == "preferred":
                signals.append(EducationSignal("preferred", evidence))
            elif REQUIRED.search(sentence) or section == "required" or re.match(
                r"^PhD\s+(?:in\b|degree\b|from\b|with\b|students?\b|candidates?\b)", sentence, re.I
            ):
                # Team biographies are not applicant requirements.
                if not re.search(r"\b(?:our|the) (?:team|researchers|scientists)|\bwork(?:ing)? (?:with|alongside)\b", sentence, re.I):
                    signals.append(EducationSignal("required", evidence))

    # An explicit alternative in the JD can clarify a short "PhD" title.
    # An independent hard requirement still wins over a preferred mention.
    if title_signal.phd_requirement == "optional":
        return title_signal
    for status in ("required", "optional"):
        match = next((signal for signal in signals if signal.phd_requirement == status), None)
        if match:
            return match
    if title_signal.phd_requirement == "required":
        return title_signal
    preferred = next((signal for signal in signals if signal.phd_requirement == "preferred"), None)
    if preferred:
        return preferred
    return title_signal
