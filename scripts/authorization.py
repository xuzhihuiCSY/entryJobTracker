"""Extract explicit employer statements, never infer sponsorship from silence."""
from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class AuthorizationSignal:
    visa_signal: str = "unknown"
    visa_evidence: str = ""
    requires_citizenship: bool = False
    citizenship_evidence: str = ""
    requires_clearance: bool = False
    clearance_evidence: str = ""


SPONSOR = r"(?:(?:visa|immigration|employment|work(?: authorization| visa)?)\s+)?sponsor(?:ship)?"
NEGATIVE = re.compile(
    rf"\b(?:no\s+{SPONSOR}|(?:cannot|can't|unable to|will not|do not|does not|not able to|not eligible for)\s+(?:provide\s+|offer\s+)?{SPONSOR}|"
    rf"{SPONSOR}\s+(?:is\s+|will be\s+|will\s+)?not\s+(?:be\s+)?(?:available|provided|offered)|"
    rf"(?:must|need to|required to)\b[^.!?]{{0,160}}\bwithout\b[^.!?]{{0,80}}\b{SPONSOR}|"
    rf"(?:not|no)\s+(?:now\s+or\s+)?(?:in\s+the\s+future\s+)?(?:require|need)\b[^.!?]{{0,80}}\b{SPONSOR}|"
    rf"without\s+(?:(?:a|the)\s+)?(?:need|requirement)\s+for\s+{SPONSOR})\b", re.I
)
CONDITIONAL = re.compile(
    rf"\b(?:may|might|can sometimes)\s+(?:provide\s+|offer\s+)?{SPONSOR}|"
    rf"\b{SPONSOR}\b[^.!?]{{0,100}}\b(?:case[- ]by[- ]case|depending|subject to|limited|certain|eligible|only|transfers?|may|might|possible)|"
    rf"\b(?:case[- ]by[- ]case|depending|subject to)\b[^.!?]{{0,100}}\b{SPONSOR}", re.I
)
POSITIVE = re.compile(
    rf"\b(?:we|company|employer)\s+(?:(?:will|can|do|does|are able to)\s+)?(?:provide|offer)\s+{SPONSOR}\b|"
    rf"\b(?:we|company|employer)\s+(?:will|can|do|does)\s+{SPONSOR}\b|"
    rf"\b{SPONSOR}\s+(?:is\s+)?(?:available|provided|offered)\b|"
    r"\bwe sponsor (?:work visas|visas|employment visas)\b", re.I
)
CITIZEN = re.compile(
    r"\b(?:must be|must hold|requires?|required to (?:be|have)|only open to)\b[^.!?]{0,65}"
    r"\b(?:u\.?s\.?|united states)\s+(?:citizens?|citizenship)\b|"
    r"\b(?:u\.?s\.?|united states)\s+citizenship\s+(?:is\s+)?required\b|"
    r"\b(?:u\.?s\.?|united states)\s+citizens?\s+only\b", re.I
)
CLEARANCE = re.compile(
    r"\b(?:must|requires?|required|active|current|ability to obtain|able to obtain)\b[^.!?]{0,100}"
    r"\b(?:security clearance|secret clearance|top secret|ts/sci)\b|"
    r"\b(?:security clearance|secret clearance|top secret|ts/sci)\b[^.!?]{0,45}\b(?:required|mandatory)\b", re.I
)


def classify_authorization(description: str) -> AuthorizationSignal:
    # Keep U.S. together while preserving sentence/question boundaries.
    text = re.sub(r"\bu\.s\.(?:a\.)?", "US", description, flags=re.I)
    sentences = [re.sub(r"\s+", " ", s).strip() for s in re.split(r"(?<=[.!?])\s+|\n+", text)]
    negative: list[str] = []
    conditional: list[str] = []
    positive: list[str] = []
    citizenship = ""
    clearance = ""
    for sentence in sentences:
        if sentence.endswith("?") or re.search(r"\b(?:please indicate|please select|do you|will you|would you)\b", sentence, re.I):
            continue
        limited = re.search(r"\b(?:not|aren't|aren’t|cannot|can't|can’t|unable)\b[^.!?]{0,55}\bsponsor\b[^.!?]{0,100}\b(?:every|all)\s+(?:role|candidate|applicant|position)", sentence, re.I)
        if limited:
            conditional.append(sentence)
        elif NEGATIVE.search(sentence):
            negative.append(sentence)
        elif CONDITIONAL.search(sentence):
            conditional.append(sentence)
        elif POSITIVE.search(sentence):
            positive.append(sentence)
        if not re.search(r"\b(?:not required|no .*required|may be required|not necessary)\b", sentence, re.I):
            if CITIZEN.search(sentence):
                citizenship = sentence[:600]
            if CLEARANCE.search(sentence):
                clearance = sentence[:600]
    status, evidence = "unknown", ""
    for candidate, matches in [("not_likely", negative), ("conditional", conditional), ("strong", positive)]:
        if matches:
            status, evidence = candidate, matches[0][:600]
            break
    return AuthorizationSignal(status, evidence, bool(citizenship), citizenship, bool(clearance), clearance)
