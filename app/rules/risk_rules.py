from typing import List, Dict, Any
from ..schemas.rule_schemas import Rule, RuleCategory, RuleSeverity, RuleAction, RuleEvaluationResult


class RiskRules:
    """Risk-related governance rules."""
    
    @staticmethod
    def get_rules() -> List[Rule]:
        """Get all risk rules."""
        return [
            Rule(
                rule_id="risk_001",
                name="High Risk Mitigation",
                category=RuleCategory.RISK,
                description="High-risk actions require mitigation plan",
                severity=RuleSeverity.HIGH,
                action=RuleAction.REQUIRE_APPROVAL,
                applies_to=["funnel.launch_request", "product.publish_request", "risk.assessment_request"],
                conditions={"check_mitigation": True}
            ),
            Rule(
                rule_id="risk_002",
                name="Risk Threshold",
                category=RuleCategory.RISK,
                description="Actions must not exceed risk threshold",
                severity=RuleSeverity.CRITICAL,
                action=RuleAction.BLOCK,
                applies_to=["*"],
                conditions={"max_risk_score": 0.8}
            ),
            Rule(
                rule_id="risk_003",
                name="Override Justification",
                category=RuleCategory.RISK,
                description="Risk overrides require strong justification",
                severity=RuleSeverity.HIGH,
                action=RuleAction.REQUIRE_APPROVAL,
                applies_to=["risk.override_request"],
                conditions={"min_justification_length": 100}
            ),
        ]
    
    @staticmethod
    async def evaluate(rule: Rule, request_data: Dict[str, Any]) -> RuleEvaluationResult:
        """Evaluate a risk rule."""
        triggered = False
        message = "Rule passed"
        details = {}
        confidence = 0.9
        
        if rule.rule_id == "risk_001":
            # Check mitigation plan
            has_mitigation = request_data.get("context", {}).get("has_mitigation", False)
            mitigation_quality = request_data.get("context", {}).get("mitigation_quality", 0.0)
            triggered = not has_mitigation or mitigation_quality < 0.7
            message = "Missing or inadequate mitigation plan" if triggered else "Mitigation plan adequate"
            details = {"has_mitigation": has_mitigation, "mitigation_quality": mitigation_quality}
        
        elif rule.rule_id == "risk_002":
            # Check risk threshold
            risk_score = request_data.get("context", {}).get("risk_score", 0.0)
            max_risk = rule.conditions.get("max_risk_score", 0.8)
            triggered = risk_score > max_risk
            message = f"Risk score {risk_score} exceeds threshold {max_risk}" if triggered else "Risk within acceptable threshold"
            details = {"risk_score": risk_score, "maximum": max_risk}
        
        elif rule.rule_id == "risk_003":
            # Check override justification
            justification = request_data.get("override_reason", "")
            min_length = rule.conditions.get("min_justification_length", 100)
            triggered = len(justification) < min_length
            message = f"Override justification too short (min: {min_length} chars)" if triggered else "Override justification adequate"
            details = {"justification_length": len(justification), "minimum": min_length}
        
        return RuleEvaluationResult(
            rule_id=rule.rule_id,
            rule_name=rule.name,
            category=rule.category,
            triggered=triggered,
            action=rule.action,
            message=message,
            details=details,
            confidence=confidence
        )
