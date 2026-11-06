from authorization import classify_authorization


def test_explicit_positive_and_negative_sponsorship() -> None:
    for text in ["We offer visa sponsorship.", "We can provide immigration sponsorship.", "Visa sponsorship is available.", "We will sponsor work visas."]:
        signal = classify_authorization(text)
        assert signal.visa_signal == "strong", (text, signal)
        assert signal.visa_evidence
    for text in [
        "We do not provide visa sponsorship.", "We cannot sponsor this position.",
        "Visa sponsorship is not available for this position.",
        "Candidates must be authorized to work in the US without current or future visa sponsorship.",
        "Applicants must not require sponsorship now or in the future.",
        "Applicants must work without a requirement for work authorization sponsorship.",
        "Visa sponsorship will not be offered for this role.",
    ]:
        assert classify_authorization(text).visa_signal == "not_likely", text


def test_conditional_and_ambiguous_statements() -> None:
    for text in ["We may offer visa sponsorship.", "Visa sponsorship may be available.", "Visa sponsorship is considered on a case-by-case basis.", "We will sponsor only H1B transfers.", "We do sponsor visas! However, we aren't able to successfully sponsor visas for every role and every candidate."]:
        assert classify_authorization(text).visa_signal == "conditional", text
    for text in ["", "You must be authorized to work in the US.", "Do you now or in the future require visa sponsorship?", "Please indicate whether you need sponsorship.", "We welcome applicants of all citizenship and immigration statuses."]:
        assert classify_authorization(text).visa_signal == "unknown", text
    assert classify_authorization("Visa sponsorship is available at our company. We cannot sponsor this position.").visa_signal == "not_likely"


def test_citizenship_clearance_and_negation() -> None:
    required = classify_authorization("Must be a U.S. citizen. An active security clearance is required.")
    assert required.requires_citizenship and required.requires_clearance
    assert required.citizenship_evidence and required.clearance_evidence
    for text in ["US citizenship is not required.", "No security clearance is required.", "Security clearance may be required for other positions.", "We do not discriminate based on United States citizenship."]:
        signal = classify_authorization(text)
        assert not signal.requires_citizenship and not signal.requires_clearance, (text, signal)


def test_normalization_reads_authorization_after_snippet_cutoff() -> None:
    from normalizer import normalize_job
    description = "<p>" + "Build useful products. " * 30 + "</p><h3>Requirements</h3><p>We cannot provide visa sponsorship for this position.</p>"
    job = normalize_job({"external_id": "1", "title": "Software Engineer", "description": description, "location_raw": "New York, NY"}, {"slug": "example", "name": "Example"}, "2026-11-05T00:00:00Z", "2026-01-01T00:00:00Z")
    assert job["visa_signal"] == "not_likely"
    assert "visa sponsorship" in job["visa_evidence"]
    assert "visa sponsorship" not in job["description_snippet"]
    assert "visa sponsorship" in job["description_text"]


if __name__ == "__main__":
    for name, value in list(globals().items()):
        if name.startswith("test_"): value()
    print("authorization tests passed")
