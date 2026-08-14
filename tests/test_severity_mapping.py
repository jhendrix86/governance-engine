"""
Tests app/severity_mapping.py's conversion of this engine's own
RuleSeverity onto the fleet's canonical Severity scale (autonomy-events,
added 2026-08-14).
"""

import pytest
from autonomy_events import Severity

from app.schemas.rule_schemas import RuleSeverity
from app.severity_mapping import to_canonical_severity


class TestSeverityMapping:
    @pytest.mark.parametrize(
        "rule_severity,expected",
        [
            (RuleSeverity.INFO, Severity.INFO),
            (RuleSeverity.LOW, Severity.LOW),
            (RuleSeverity.MEDIUM, Severity.MEDIUM),
            (RuleSeverity.HIGH, Severity.HIGH),
            (RuleSeverity.CRITICAL, Severity.CRITICAL),
        ],
    )
    def test_every_rule_severity_maps_to_its_canonical_counterpart(self, rule_severity, expected):
        assert to_canonical_severity(rule_severity) == expected

    def test_every_rule_severity_value_is_covered(self):
        # If a new RuleSeverity value is ever added without updating the
        # mapping table, this fails loudly instead of KeyError-ing at
        # runtime the first time someone hits the new value.
        for rule_severity in RuleSeverity:
            to_canonical_severity(rule_severity)
