from typing import List, Dict, Any
from ..schemas.rule_schemas import Rule, RuleCategory, RuleSeverity, RuleAction, RuleEvaluationResult


class StrategyRules:
    """Strategy-related governance rules."""
    
    @staticmethod
    def get_rules() -> List[Rule]:
        """Get all strategy rules."""
        return [
            Rule(
                rule_id="strategy_001",
                name="Strategic Alignment",
                category=RuleCategory.STRATEGY,
                description="Actions must align with overall company strategy",
                severity=RuleSeverity.HIGH,
                action=RuleAction.REQUIRE_APPROVAL,
                applies_to=["funnel.create_request", "funnel.launch_request", "strategy.alignment_request"],
                conditions={"check_alignment": True}
            ),
            Rule(
                rule_id="strategy_002",
                name="Market Fit Validation",
                category=RuleCategory.STRATEGY,
                description="New funnels must validate market fit",
                severity=RuleSeverity.MEDIUM,
                action=RuleAction.WARN,
                applies_to=["funnel.create_request"],
                conditions={"check_market_fit": True}
            ),
            Rule(
                rule_id="strategy_003",
                name="Resource Efficiency",
                category=RuleCategory.STRATEGY,
                description="Strategies must be resource-efficient",
                severity=RuleSeverity.MEDIUM,
                action=RuleAction.WARN,
                applies_to=["funnel.mutation_request", "strategy.alignment_request"],
                conditions={"min_efficiency": 0.7}
            ),
            Rule(
                rule_id="strategy_004",
                name="Competitive Differentiation",
                category=RuleCategory.STRATEGY,
                description="Must maintain competitive differentiation",
                severity=RuleSeverity.MEDIUM,
                action=RuleAction.WARN,
                applies_to=["funnel.create_request", "product.publish_request"],
                conditions={"check_differentiation": True}
            ),
        ]
    
    @staticmethod
    async def evaluate(rule: Rule, request_data: Dict[str, Any]) -> RuleEvaluationResult:
        """Evaluate a strategy rule."""
        triggered = False
        message = "Rule passed"
        details = {}
        confidence = 0.8
        
        if rule.rule_id == "strategy_001":
            # Check strategic alignment
            alignment_score = request_data.get("context", {}).get("alignment_score", 0.0)
            triggered = alignment_score < 0.7
            message = f"Strategic alignment score {alignment_score} below threshold" if triggered else "Strategic alignment adequate"
            details = {"alignment_score": alignment_score}
        
        elif rule.rule_id == "strategy_002":
            # Check market fit
            market_fit = request_data.get("context", {}).get("market_fit_score", 0.0)
            triggered = market_fit < 0.6
            message = f"Market fit score {market_fit} below threshold" if triggered else "Market fit validated"
            details = {"market_fit_score": market_fit}
        
        elif rule.rule_id == "strategy_003":
            # Check resource efficiency
            efficiency = request_data.get("context", {}).get("efficiency", 0.0)
            min_efficiency = rule.conditions.get("min_efficiency", 0.7)
            triggered = efficiency < min_efficiency
            message = f"Efficiency {efficiency} below threshold {min_efficiency}" if triggered else "Resource efficiency adequate"
            details = {"efficiency": efficiency, "minimum": min_efficiency}
        
        elif rule.rule_id == "strategy_004":
            # Check competitive differentiation
            differentiation = request_data.get("context", {}).get("differentiation_score", 0.0)
            triggered = differentiation < 0.5
            message = f"Differentiation score {differentiation} below threshold" if triggered else "Competitive differentiation maintained"
            details = {"differentiation_score": differentiation}
        
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
