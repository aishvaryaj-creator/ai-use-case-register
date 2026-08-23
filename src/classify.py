"""Classify a register entry against the EU AI Act.

Order of evaluation matters and mirrors the Act's own structure:
  1. Art. 5   prohibited practices        -> stop, nothing else matters
  2. Role     Art. 3 / Art. 25            -> who bears which obligations
  3. Annex III enumeration                -> candidate high-risk
  4. Art. 6(3) filter + profiling carve-out
  5. Art. 50  transparency (independent of tier)
  6. GPAI     Chapter V flags

Every decision returns a rationale string naming the provision relied on.
Timeline constants reflect Regulation (EU) 2026/1744 (Digital Omnibus on AI),
in force 27 July 2026. Update DEADLINES if the position changes.
"""

from dataclasses import dataclass, field

DEADLINES = {
    "annex_iii_high_risk": "2027-12-02",
    "annex_i_high_risk": "2028-08-02",
    "art_50_transparency": "2026-08-02",
    "art_50_2_legacy_and_new_prohibitions": "2026-12-02",
}

ANNEX_III_LABELS = {
    "1": "biometrics",
    "2": "critical infrastructure",
    "3": "education and vocational training",
    "4": "employment, workers management, access to self-employment",
    "5": "access to essential private and public services",
    "6": "law enforcement",
    "7": "migration, asylum, border control",
    "8": "administration of justice and democratic processes",
}


@dataclass
class Result:
    system_id: str
    tier: str
    effective_role: str
    rationale: list[str] = field(default_factory=list)
    obligations: list[str] = field(default_factory=list)
    deadline: str | None = None
    flags: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "system_id": self.system_id,
            "tier": self.tier,
            "effective_role": self.effective_role,
            "deadline": self.deadline,
            "rationale": self.rationale,
            "obligations": self.obligations,
            "flags": self.flags,
        }


def effective_role(e: dict) -> tuple[str, str]:
    """Art. 25: a deployer becomes a provider in three situations."""
    stated = e["our_role"]
    if stated == "deployer":
        triggers = []
        if e.get("placed_under_own_name"):
            triggers.append("system placed on the market under our own name or trademark")
        if e.get("substantially_modified"):
            triggers.append("system substantially modified")
        if e.get("intended_purpose_changed"):
            triggers.append("intended purpose changed such that the system becomes high-risk")
        if triggers:
            return "provider", (
                "Recorded as deployer, but treated as PROVIDER under Art. 25(1): "
                + "; ".join(triggers)
            )
    return stated, f"Role recorded as {stated}; no Art. 25(1) trigger present."


def annex_iii_point(e: dict) -> str | None:
    return e.get("annex_iii")


def classify(e: dict) -> Result:
    r = Result(system_id=e["id"], tier="undetermined", effective_role=e["our_role"])

    # 1. Prohibited practices short-circuit everything else.
    if e.get("prohibited_practice"):
        r.tier = "prohibited"
        r.rationale.append(
            f"Art. 5 point {e['prohibited_practice']} engaged. The practice is banned; "
            "no conformity route exists. Escalate for cessation, do not risk-assess."
        )
        r.obligations.append("Cease or do not deploy.")
        return r

    # 2. Effective role.
    role, role_reason = effective_role(e)
    r.effective_role = role
    r.rationale.append(role_reason)

    # 3-4. High-risk determination.
    point = annex_iii_point(e)
    if point is None:
        r.tier = "not-high-risk"
        r.rationale.append(
            "Not enumerated in Annex III and not an Annex I safety component; "
            "Chapter III obligations do not apply."
        )
    else:
        area = ANNEX_III_LABELS.get(point.split("(")[0], "unmapped area")
        claimed = e.get("art_6_3_filter")
        if claimed and e.get("profiling"):
            r.tier = "high-risk"
            r.rationale.append(
                f"Falls within Annex III point {point} ({area}). Art. 6(3) derogation "
                f"'{claimed}' was claimed but is UNAVAILABLE: the system performs profiling "
                "of natural persons, which Art. 6(3) excludes from the derogation in all cases."
            )
        elif claimed:
            r.tier = "not-high-risk (Art. 6(3) derogation)"
            r.rationale.append(
                f"Falls within Annex III point {point} ({area}), but derogated under Art. 6(3) "
                f"on the ground '{claimed}'. Justification of record: "
                f"{e.get('art_6_3_justification')}"
            )
            r.obligations.append(
                "Document the Art. 6(3) assessment before placing on the market or putting "
                "into service, and register the system where required by Art. 6(4)."
            )
            r.flags.append("derogation-claimed: re-review on any change of intended purpose")
        else:
            r.tier = "high-risk"
            r.rationale.append(
                f"Falls within Annex III point {point} ({area}); no Art. 6(3) filter condition claimed."
            )

    if r.tier == "high-risk":
        r.deadline = DEADLINES["annex_iii_high_risk"]
        if role == "provider":
            r.obligations += [
                "Risk management system (Art. 9)",
                "Data and data governance (Art. 10)",
                "Technical documentation (Art. 11, Annex IV)",
                "Logging (Art. 12)",
                "Instructions for use / transparency to deployers (Art. 13)",
                "Human oversight design (Art. 14)",
                "Accuracy, robustness, cybersecurity (Art. 15)",
                "QMS, conformity assessment, CE marking, EU database registration",
            ]
        elif role == "deployer":
            r.obligations += [
                "Use in accordance with instructions for use (Art. 26(1))",
                "Assign competent, trained human oversight (Art. 26(2))",
                "Ensure input data relevance (Art. 26(4))",
                "Retain logs (Art. 26(6))",
                "Inform workers and their representatives before workplace use (Art. 26(7))",
                "Fundamental rights impact assessment where Art. 27 applies",
            ]

    # 5. Transparency obligations run independently of tier.
    if e.get("interacts_with_humans"):
        r.obligations.append("Disclose AI interaction to the person (Art. 50(1))")
        r.deadline = r.deadline or DEADLINES["art_50_transparency"]
    if e.get("generates_synthetic_content"):
        r.obligations.append("Machine-readable marking of synthetic output (Art. 50(2))")
        r.flags.append(f"art-50(2) legacy cut-off {DEADLINES['art_50_2_legacy_and_new_prohibitions']}")
    if e.get("emotion_recognition"):
        r.obligations.append("Inform exposed persons of emotion recognition use (Art. 50(3))")

    # 6. GPAI.
    if e.get("gpai_model"):
        r.flags.append(
            f"built on GPAI model '{e['gpai_model']}' — confirm upstream provider's "
            "Chapter V documentation is on file"
        )

    # Cross-framework hooks.
    if e.get("personal_data") and (r.tier == "high-risk" or e.get("special_category")):
        r.flags.append("DPIA likely required (GDPR Art. 35) — link the assessment reference")

    return r
