from typing import List, Dict, Any
from ..schemas.rule_schemas import Rule, RuleCategory, RuleSeverity, RuleAction, RuleEvaluationResult


class ResourceRules:
    """Resource-related governance rules."""
    
    @staticmethod
    def get_rules() -> List[Rule]:
        """Get all resource rules."""
        return [
            Rule(
                rule_id="resource_001",
                name="Compute Resource Limits",
                category=RuleCategory.RESOURCE,
                description="Compute requests must not exceed resource limits",
                severity=RuleSeverity.HIGH,
                action=RuleAction.REQUIRE_APPROVAL,
                applies_to=["resource.compute_request"],
                conditions={"max_compute": 100}
            ),
            Rule(
                rule_id="resource_002",
                name="API Rate Limits",
                category=RuleCategory.RESOURCE,
                description="API requests must respect rate limits",
                severity=RuleSeverity.MEDIUM,
                action=RuleAction.WARN,
                applies_to=["resource.api_request"],
                conditions={"max_rate": 1000}
            ),
            Rule(
                rule_id="resource_003",
                name="Budget Allocation",
                category=RuleCategory.RESOURCE,
                description="Budget requests must be within allocation",
                severity=RuleSeverity.HIGH,
                action=RuleAction.REQUIRE_APPROVAL,
                applies_to=["resource.budget_request"],
                conditions={"max_monthly_budget": 50000.0}
            ),
            Rule(
                rule_id="resource_004",
                name="Resource Priority",
                category=RuleCategory.RESOURCE,
                description="High priority requests require justification",
                severity=RuleSeverity.MEDIUM,
                action=RuleAction.REQUIRE_APPROVAL,
                applies_to=["resource.compute_request", "resource.budget_request"],
                conditions={"high_priority_requires_justification": True}
            ),
        ]
    
    @staticmethod
    async def evaluate(rule: Rule, request_data: Dict[str, Any]) -> RuleEvaluationResult:
        """Evaluate a resource rule."""
        triggered = False
        message = "Rule passed"
        details = {}
        confidence = 1.0
        
        if rule.rule_id == "resource_001":
            # Check compute resource limits
            quantity = request_data.get("quantity", 0)
            max_compute = rule.conditions.get("max_compute", 100)
            triggered = quantity > max_compute
            message = f"Compute request {quantity} exceeds limit {max_compute}" if triggered else "Compute within limits"
            details = {"requested": quantity, "maximum": max_compute}
        
        elif rule.rule_id == "resource_002":
            # Check API rate limits
            rate_limit = request_data.get("rate_limit", 0)
            max_rate = rule.conditions.get("max_rate", 1000)
            triggered = rate_limit > max_rate
            message = f"Rate limit {rate_limit} exceeds {max_rate}" if triggered else "Rate limit within bounds"
            details = {"requested": rate_limit, "maximum": max_rate}
        
        elif rule.rule_id == "resource_003":
            # Check budget allocation
            amount = request_data.get("amount", 0)
            period = request_data.get("period", "monthly")
            max_budget = rule.conditions.get("max_monthly_budget", 50000.0)
            
            if period == "monthly":
                triggered = amount > max_budget
            elif period == "weekly":
                triggered = amount > max_budget / 4
            elif period == "daily":
                triggered = amount > max_budget / 30
            
            message = f"Budget {amount} for {period} exceeds allocation" if triggered else "Budget within allocation"
            details = {"requested": amount, "period": period, "maximum": max_budget}
        
        elif rule.rule_id == "resource_004":
            # Check priority justification
            priority = request_data.get("priority", "normal")
            justification = request_data.get("justification", "")
            triggered = priority == "high" and len(justification) < 50
            message = "High priority requires detailed justification" if triggered else "Priority justification adequate"
            details = {"priority": priority, "justification_length": len(justification)}
        
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
