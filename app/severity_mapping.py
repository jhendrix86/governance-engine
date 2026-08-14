"""
Maps this engine's own RuleSeverity onto the fleet's canonical Severity
scale (autonomy-events, added 2026-08-14 - see its severity.py for the
full story of why a canonical scale exists).

RuleSeverity's 5 values (info/low/medium/high/critical) happen to already
match Severity's exactly - not a coincidence, RuleSeverity was the real,
most fine-grained scale the canonical one was modeled on. Still a real,
explicit mapping (not just "use the same enum") rather than importing
Severity as RuleSeverity directly: this engine's own rule vocabulary is
allowed to diverge from the canonical scale in the future without a
silent break at every call site, and every other engine wires up its
mapping the same explicit way regardless of how much or little its local
scale currently overlaps.
"""

from autonomy_events import Severity

from app.schemas.rule_schemas import RuleSeverity

_TO_CANONICAL = {
    RuleSeverity.INFO: Severity.INFO,
    RuleSeverity.LOW: Severity.LOW,
    RuleSeverity.MEDIUM: Severity.MEDIUM,
    RuleSeverity.HIGH: Severity.HIGH,
    RuleSeverity.CRITICAL: Severity.CRITICAL,
}


def to_canonical_severity(severity: RuleSeverity) -> Severity:
    """Convert this engine's RuleSeverity to the fleet's canonical Severity."""
    return _TO_CANONICAL[severity]
