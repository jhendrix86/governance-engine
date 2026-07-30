from typing import List, Dict, Any
from ..schemas.rule_schemas import Rule, RuleCategory, RuleSeverity, RuleAction, RuleEvaluationResult


class ComplianceRules:
    """Compliance-related governance rules."""
    
    @staticmethod
    def get_rules() -> List[Rule]:
        """Get all compliance rules."""
        return [
            Rule(
                rule_id="compliance_001",
                name="GDPR Compliance",
                category=RuleCategory.COMPLIANCE,
                description="Must comply with GDPR requirements",
                severity=RuleSeverity.CRITICAL,
                action=RuleAction.BLOCK,
                applies_to=["funnel.create_request", "resource.api_request", "product.publish_request"],
                conditions={"check_gdpr": True}
            ),
            Rule(
                rule_id="compliance_002",
                name="Terms of Service",
                category=RuleCategory.COMPLIANCE,
                description="Must have valid Terms of Service",
                severity=RuleSeverity.HIGH,
                action=RuleAction.REQUIRE_APPROVAL,
                applies_to=["funnel.create_request", "product.publish_request"],
                conditions={"check_tos": True}
            ),
            Rule(
                rule_id="compliance_003",
                name="Age Restrictions",
                category=RuleCategory.COMPLIANCE,
                description="Must respect age restrictions for content",
                severity=RuleSeverity.HIGH,
                action=RuleAction.BLOCK,
                applies_to=["funnel.create_request", "product.publish_request"],
                conditions={"min_age": 18}
            ),
            Rule(
                rule_id="compliance_004",
                name="FTC Disclosure",
                category=RuleCategory.COMPLIANCE,
                description="Must include FTC disclosure for affiliate content",
                severity=RuleSeverity.MEDIUM,
                action=RuleAction.WARN,
                applies_to=["funnel.create_request", "product.publish_request"],
                conditions={"check_ftc": True}
            ),
        ]
    
    @staticmethod
    async def evaluate(rule: Rule, request_data: Dict[str, Any]) -> RuleEvaluationResult:
        """Evaluate a compliance rule."""
        triggered = False
        message = "Rule passed"
        details = {}
        confidence = 1.0
        
        if rule.rule_id == "compliance_001":
            # Check GDPR compliance
            has_consent = request_data.get("context", {}).get("gdpr_consent", False)
            data_minimization = request_data.get("context", {}).get("data_minimization", False)
            triggered = not (has_consent and data_minimization)
            message = "GDPR requirements not met" if triggered else "GDPR compliant"
            details = {"has_consent": has_consent, "data_minimization": data_minimization}
        
        elif rule.rule_id == "compliance_002":
            # Check Terms of Service
            has_tos = request_data.get("context", {}).get("has_tos", False)
            tos_version = request_data.get("context", {}).get("tos_version", "")
            triggered = not has_tos or not tos_version
            message = "Missing or invalid Terms of Service" if triggered else "Terms of Service valid"
            details = {"has_tos": has_tos, "tos_version": tos_version}
        
        elif rule.rule_id == "compliance_003":
            # Check age restrictions
            target_audience = request_data.get("target_audience", "").lower()
            min_age = rule.conditions.get("min_age", 18)
            age_restricted_keywords = ["kids", "children", "minors", "teens"]
            triggered = any(kw in target_audience for kw in age_restricted_keywords)
            message = f"Age-restricted content detected (min age: {min_age})" if triggered else "Age restrictions met"
        
        elif rule.rule_id == "compliance_004":
            # Check FTC disclosure
            is_affiliate = request_data.get("context", {}).get("is_affiliate", False)
            has_disclosure = request_data.get("context", {}).get("has_ftc_disclosure", False)
            triggered = is_affiliate and not has_disclosure
            message = "Missing FTC disclosure for affiliate content" if triggered else "FTC disclosure compliant"
            details = {"is_affiliate": is_affiliate, "has_disclosure": has_disclosure}
        
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
