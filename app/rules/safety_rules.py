from typing import List, Dict, Any
from ..schemas.rule_schemas import Rule, RuleCategory, RuleSeverity, RuleAction, RuleEvaluationResult


class SafetyRules:
    """Safety-related governance rules."""
    
    @staticmethod
    def get_rules() -> List[Rule]:
        """Get all safety rules."""
        return [
            Rule(
                rule_id="safety_001",
                name="No Profanity in Content",
                category=RuleCategory.SAFETY,
                description="Content must not contain profanity or offensive language",
                severity=RuleSeverity.HIGH,
                action=RuleAction.BLOCK,
                applies_to=["funnel.create_request", "funnel.mutation_request", "product.publish_request"],
                conditions={"check_profanity": True}
            ),
            Rule(
                rule_id="safety_002",
                name="No Illegal Activities",
                category=RuleCategory.SAFETY,
                description="Actions must not involve illegal activities",
                severity=RuleSeverity.CRITICAL,
                action=RuleAction.BLOCK,
                applies_to=["*"],
                conditions={"check_illegal": True}
            ),
            Rule(
                rule_id="safety_003",
                name="Data Privacy Compliance",
                category=RuleCategory.SAFETY,
                description="Must comply with data privacy regulations",
                severity=RuleSeverity.HIGH,
                action=RuleAction.REQUIRE_APPROVAL,
                applies_to=["funnel.create_request", "resource.api_request"],
                conditions={"check_privacy": True}
            ),
            Rule(
                rule_id="safety_004",
                name="Rate Limit Protection",
                category=RuleCategory.SAFETY,
                description="API requests must respect rate limits",
                severity=RuleSeverity.MEDIUM,
                action=RuleAction.WARN,
                applies_to=["resource.api_request"],
                conditions={"max_rate_limit": 1000}
            ),
            Rule(
                rule_id="safety_005",
                name="Budget Safety Limit",
                category=RuleCategory.SAFETY,
                description="Budget requests must not exceed safety limits",
                severity=RuleSeverity.HIGH,
                action=RuleAction.REQUIRE_APPROVAL,
                applies_to=["resource.budget_request"],
                conditions={"max_budget": 10000.0}
            ),
        ]
    
    @staticmethod
    async def evaluate(rule: Rule, request_data: Dict[str, Any]) -> RuleEvaluationResult:
        """Evaluate a safety rule."""
        triggered = False
        message = "Rule passed"
        details = {}
        confidence = 1.0
        
        if rule.rule_id == "safety_001":
            # Check for profanity in content
            content = request_data.get("context", {}).get("content", "")
            profanity_words = ["profanity", "offensive"]  # Simplified for example
            triggered = any(word in content.lower() for word in profanity_words)
            message = "Content contains profanity" if triggered else "Content is clean"
            details = {"content_length": len(content)}
        
        elif rule.rule_id == "safety_002":
            # Check for illegal activities
            illegal_keywords = ["illegal", "fraud", "scam"]
            context_str = str(request_data).lower()
            triggered = any(keyword in context_str for keyword in illegal_keywords)
            message = "Illegal activity detected" if triggered else "No illegal activities"
        
        elif rule.rule_id == "safety_003":
            # Check privacy compliance
            has_pii = request_data.get("context", {}).get("contains_pii", False)
            triggered = has_pii
            message = "PII detected, requires approval" if triggered else "No PII detected"
        
        elif rule.rule_id == "safety_004":
            # Check rate limit
            rate_limit = request_data.get("rate_limit", 0)
            max_limit = rule.conditions.get("max_rate_limit", 1000)
            triggered = rate_limit > max_limit
            message = f"Rate limit {rate_limit} exceeds {max_limit}" if triggered else "Rate limit within bounds"
            details = {"requested": rate_limit, "maximum": max_limit}
        
        elif rule.rule_id == "safety_005":
            # Check budget limit
            amount = request_data.get("amount", 0)
            max_budget = rule.conditions.get("max_budget", 10000.0)
            triggered = amount > max_budget
            message = f"Budget {amount} exceeds safety limit {max_budget}" if triggered else "Budget within safety limit"
            details = {"requested": amount, "maximum": max_budget}
        
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
