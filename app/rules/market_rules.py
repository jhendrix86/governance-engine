from typing import List, Dict, Any
from ..schemas.rule_schemas import Rule, RuleCategory, RuleSeverity, RuleAction, RuleEvaluationResult


class MarketRules:
    """Market-related governance rules."""
    
    @staticmethod
    def get_rules() -> List[Rule]:
        """Get all market rules."""
        return [
            Rule(
                rule_id="market_001",
                name="Market Saturation",
                category=RuleCategory.MARKET,
                description="Must avoid oversaturated markets",
                severity=RuleSeverity.MEDIUM,
                action=RuleAction.WARN,
                applies_to=["funnel.create_request", "funnel.launch_request"],
                conditions={"check_saturation": True}
            ),
            Rule(
                rule_id="market_002",
                name="Competitive Density",
                category=RuleCategory.MARKET,
                description="Must consider competitive density",
                severity=RuleSeverity.MEDIUM,
                action=RuleAction.WARN,
                applies_to=["funnel.create_request", "niche.selection"],
                conditions={"max_competitors": 50}
            ),
            Rule(
                rule_id="market_003",
                name="Market Size Validation",
                category=RuleCategory.MARKET,
                description="Markets must have sufficient size",
                severity=RuleSeverity.LOW,
                action=RuleAction.WARN,
                applies_to=["funnel.create_request"],
                conditions={"min_market_size": 1000000}
            ),
        ]
    
    @staticmethod
    async def evaluate(rule: Rule, request_data: Dict[str, Any]) -> RuleEvaluationResult:
        """Evaluate a market rule."""
        triggered = False
        message = "Rule passed"
        details = {}
        confidence = 0.7
        
        if rule.rule_id == "market_001":
            # Check market saturation
            saturation = request_data.get("context", {}).get("market_saturation", 0.0)
            triggered = saturation > 0.8
            message = f"Market saturation {saturation} above threshold" if triggered else "Market saturation acceptable"
            details = {"saturation": saturation}
        
        elif rule.rule_id == "market_002":
            # Check competitive density
            competitor_count = request_data.get("context", {}).get("competitor_count", 0)
            max_competitors = rule.conditions.get("max_competitors", 50)
            triggered = competitor_count > max_competitors
            message = f"Competitor count {competitor_count} exceeds {max_competitors}" if triggered else "Competitive density acceptable"
            details = {"competitor_count": competitor_count, "maximum": max_competitors}
        
        elif rule.rule_id == "market_003":
            # Check market size
            market_size = request_data.get("context", {}).get("market_size", 0)
            min_size = rule.conditions.get("min_market_size", 1000000)
            triggered = market_size < min_size
            message = f"Market size {market_size} below minimum {min_size}" if triggered else "Market size adequate"
            details = {"market_size": market_size, "minimum": min_size}
        
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
