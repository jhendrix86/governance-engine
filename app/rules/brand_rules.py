from typing import List, Dict, Any
from ..schemas.rule_schemas import Rule, RuleCategory, RuleSeverity, RuleAction, RuleEvaluationResult


class BrandRules:
    """Brand-related governance rules."""
    
    @staticmethod
    def get_rules() -> List[Rule]:
        """Get all brand rules."""
        return [
            Rule(
                rule_id="brand_001",
                name="Brand Voice Consistency",
                category=RuleCategory.BRAND,
                description="Content must maintain consistent brand voice",
                severity=RuleSeverity.MEDIUM,
                action=RuleAction.WARN,
                applies_to=["funnel.create_request", "funnel.mutation_request", "product.publish_request"],
                conditions={"check_brand_voice": True}
            ),
            Rule(
                rule_id="brand_002",
                name="Logo Usage Guidelines",
                category=RuleCategory.BRAND,
                description="Logo usage must follow brand guidelines",
                severity=RuleSeverity.MEDIUM,
                action=RuleAction.WARN,
                applies_to=["funnel.create_request", "product.publish_request"],
                conditions={"check_logo_usage": True}
            ),
            Rule(
                rule_id="brand_003",
                name="Color Scheme Compliance",
                category=RuleCategory.BRAND,
                description="Must use approved brand colors",
                severity=RuleSeverity.LOW,
                action=RuleAction.WARN,
                applies_to=["funnel.create_request", "product.publish_request"],
                conditions={"check_colors": True}
            ),
            Rule(
                rule_id="brand_004",
                name="Competitor References",
                category=RuleCategory.BRAND,
                description="Must not make false claims about competitors",
                severity=RuleSeverity.HIGH,
                action=RuleAction.BLOCK,
                applies_to=["funnel.create_request", "funnel.mutation_request", "product.publish_request"],
                conditions={"check_competitor_claims": True}
            ),
        ]
    
    @staticmethod
    async def evaluate(rule: Rule, request_data: Dict[str, Any]) -> RuleEvaluationResult:
        """Evaluate a brand rule."""
        triggered = False
        message = "Rule passed"
        details = {}
        confidence = 0.9
        
        if rule.rule_id == "brand_001":
            # Check brand voice consistency
            tone = request_data.get("context", {}).get("tone", "neutral")
            approved_tones = ["professional", "friendly", "authoritative"]
            triggered = tone not in approved_tones
            message = f"Tone '{tone}' not in approved list" if triggered else "Brand voice consistent"
            details = {"tone": tone, "approved_tones": approved_tones}
        
        elif rule.rule_id == "brand_002":
            # Check logo usage
            has_logo = request_data.get("context", {}).get("has_logo", False)
            logo_approved = request_data.get("context", {}).get("logo_approved", True)
            triggered = has_logo and not logo_approved
            message = "Logo not approved" if triggered else "Logo usage compliant"
        
        elif rule.rule_id == "brand_003":
            # Check color scheme
            colors = request_data.get("context", {}).get("colors", [])
            brand_colors = ["#0066cc", "#ff6600", "#333333"]  # Example brand colors
            triggered = not any(c in brand_colors for c in colors)
            message = "Non-brand colors detected" if triggered else "Color scheme compliant"
            details = {"colors": colors}
        
        elif rule.rule_id == "brand_004":
            # Check competitor claims
            content = str(request_data).lower()
            competitor_keywords = ["competitor", "rival", "worse than"]
            false_claim_indicators = ["scam", "fraud", "illegal"]
            triggered = any(kw in content for kw in competitor_keywords) and any(ind in content for ind in false_claim_indicators)
            message = "Potential false competitor claims detected" if triggered else "No false competitor claims"
        
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
