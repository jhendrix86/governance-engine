from typing import List, Dict, Any
from ..schemas.rule_schemas import Rule, RuleCategory, RuleSeverity, RuleAction, RuleEvaluationResult


class CausalRules:
    """Causal-related governance rules."""
    
    @staticmethod
    def get_rules() -> List[Rule]:
        """Get all causal rules."""
        return [
            Rule(
                rule_id="causal_001",
                name="Causal Chain Validation",
                category=RuleCategory.CAUSAL,
                description="Actions must not trigger known negative causal chains",
                severity=RuleSeverity.HIGH,
                action=RuleAction.BLOCK,
                applies_to=["funnel.launch_request", "funnel.mutation_request"],
                conditions={"check_causal_chains": True}
            ),
            Rule(
                rule_id="causal_002",
                name="Historical Pattern Check",
                category=RuleCategory.CAUSAL,
                description="Must check historical patterns for similar actions",
                severity=RuleSeverity.MEDIUM,
                action=RuleAction.WARN,
                applies_to=["funnel.create_request", "funnel.mutation_request"],
                conditions={"check_historical_patterns": True}
            ),
            Rule(
                rule_id="causal_003",
                name="Dependency Validation",
                category=RuleCategory.CAUSAL,
                description="Actions must respect dependency constraints",
                severity=RuleSeverity.MEDIUM,
                action=RuleAction.WARN,
                applies_to=["funnel.launch_request", "product.publish_request"],
                conditions={"check_dependencies": True}
            ),
        ]
    
    @staticmethod
    async def evaluate(rule: Rule, request_data: Dict[str, Any]) -> RuleEvaluationResult:
        """Evaluate a causal rule."""
        triggered = False
        message = "Rule passed"
        details = {}
        confidence = 0.75
        
        if rule.rule_id == "causal_001":
            # Check causal chains
            negative_chains = request_data.get("context", {}).get("negative_causal_chains", [])
            triggered = len(negative_chains) > 0
            message = f"Action triggers {len(negative_chains)} negative causal chains" if triggered else "No negative causal chains detected"
            details = {"negative_chains_count": len(negative_chains)}
        
        elif rule.rule_id == "causal_002":
            # Check historical patterns
            historical_failure_rate = request_data.get("context", {}).get("historical_failure_rate", 0.0)
            triggered = historical_failure_rate > 0.3
            message = f"Historical failure rate {historical_failure_rate} above threshold" if triggered else "Historical patterns acceptable"
            details = {"historical_failure_rate": historical_failure_rate}
        
        elif rule.rule_id == "causal_003":
            # Check dependencies
            missing_dependencies = request_data.get("context", {}).get("missing_dependencies", [])
            triggered = len(missing_dependencies) > 0
            message = f"Missing {len(missing_dependencies)} dependencies"if triggered else "All dependencies satisfied"
            details = {"missing_dependencies": missing_dependencies}
        
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
