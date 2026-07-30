from typing import List, Dict, Any
from datetime import datetime
from ..schemas.rule_schemas import Rule, RuleCategory, RuleSeverity, RuleAction, RuleEvaluationResult


class TemporalRules:
    """Temporal-related governance rules."""
    
    @staticmethod
    def get_rules() -> List[Rule]:
        """Get all temporal rules."""
        return [
            Rule(
                rule_id="temporal_001",
                name="Business Hours Only",
                category=RuleCategory.TEMPORAL,
                description="Certain actions restricted to business hours",
                severity=RuleSeverity.LOW,
                action=RuleAction.WARN,
                applies_to=["funnel.launch_request", "product.publish_request"],
                conditions={"business_hours_only": True, "start_hour": 9, "end_hour": 17}
            ),
            Rule(
                rule_id="temporal_002",
                name="Rate Limit Window",
                category=RuleCategory.TEMPORAL,
                description="Actions must respect rate limit time windows",
                severity=RuleSeverity.MEDIUM,
                action=RuleAction.WARN,
                applies_to=["resource.api_request", "funnel.mutation_request"],
                conditions={"window_seconds": 60, "max_per_window": 10}
            ),
            Rule(
                rule_id="temporal_003",
                name="Cooldown Period",
                category=RuleCategory.TEMPORAL,
                description="Must respect cooldown between similar actions",
                severity=RuleSeverity.MEDIUM,
                action=RuleAction.WARN,
                applies_to=["funnel.mutation_request", "resource.compute_request"],
                conditions={"cooldown_seconds": 300}
            ),
        ]
    
    @staticmethod
    async def evaluate(rule: Rule, request_data: Dict[str, Any]) -> RuleEvaluationResult:
        """Evaluate a temporal rule."""
        triggered = False
        message = "Rule passed"
        details = {}
        confidence = 1.0
        
        current_hour = datetime.utcnow().hour
        
        if rule.rule_id == "temporal_001":
            # Check business hours
            start_hour = rule.conditions.get("start_hour", 9)
            end_hour = rule.conditions.get("end_hour", 17)
            triggered = not (start_hour <= current_hour < end_hour)
            message = f"Current hour {current_hour} outside business hours ({start_hour}-{end_hour})" if triggered else "Within business hours"
            details = {"current_hour": current_hour, "business_hours": f"{start_hour}-{end_hour}"}
        
        elif rule.rule_id == "temporal_002":
            # Check rate limit window (simplified - would need actual tracking in production)
            recent_actions = request_data.get("context", {}).get("recent_action_count", 0)
            max_per_window = rule.conditions.get("max_per_window", 10)
            triggered = recent_actions > max_per_window
            message = f"Recent actions {recent_actions} exceed window limit {max_per_window}" if triggered else "Rate limit window respected"
            details = {"recent_actions": recent_actions, "maximum": max_per_window}
        
        elif rule.rule_id == "temporal_003":
            # Check cooldown period
            last_action_time = request_data.get("context", {}).get("last_action_time")
            cooldown_seconds = rule.conditions.get("cooldown_seconds", 300)
            
            if last_action_time:
                last_time = datetime.fromisoformat(last_action_time)
                elapsed = (datetime.utcnow() - last_time).total_seconds()
                triggered = elapsed < cooldown_seconds
                message = f"Cooldown period not met (elapsed: {elapsed}s, required: {cooldown_seconds}s)" if triggered else "Cooldown period respected"
                details = {"elapsed_seconds": elapsed, "required": cooldown_seconds}
            else:
                triggered = False
                message = "No recent action, cooldown not applicable"
        
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
