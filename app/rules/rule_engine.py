from typing import List, Dict, Any, Optional
import uuid
from datetime import datetime, timedelta
import structlog
from ..schemas.rule_schemas import Rule, RuleCategory, RuleAction, RuleEvaluationResult
from ..schemas.decision_schemas import GovernanceDecision, DecisionStatus
from .safety_rules import SafetyRules
from .brand_rules import BrandRules
from .compliance_rules import ComplianceRules
from .resource_rules import ResourceRules
from .strategy_rules import StrategyRules
from .risk_rules import RiskRules
from .market_rules import MarketRules
from .temporal_rules import TemporalRules
from .causal_rules import CausalRules


logger = structlog.get_logger()


class RuleEngine:
    """Main rule engine for governance decisions."""
    
    def __init__(self):
        self._rules: Dict[str, Rule] = {}
        self._rule_handlers = {
            RuleCategory.SAFETY: SafetyRules,
            RuleCategory.BRAND: BrandRules,
            RuleCategory.COMPLIANCE: ComplianceRules,
            RuleCategory.RESOURCE: ResourceRules,
            RuleCategory.STRATEGY: StrategyRules,
            RuleCategory.RISK: RiskRules,
            RuleCategory.MARKET: MarketRules,
            RuleCategory.TEMPORAL: TemporalRules,
            RuleCategory.CAUSAL: CausalRules,
        }
        self._load_rules()
    
    def _load_rules(self):
        """Load all rules from rule handlers."""
        for category, handler in self._rule_handlers.items():
            rules = handler.get_rules()
            for rule in rules:
                self._rules[rule.rule_id] = rule
        
        logger.info("rules_loaded", count=len(self._rules))
    
    def reload_rules(self):
        """Reload all rules."""
        self._rules.clear()
        self._load_rules()
        logger.info("rules_reloaded")
    
    def get_rules(self, category: Optional[RuleCategory] = None) -> List[Rule]:
        """Get rules, optionally filtered by category."""
        if category:
            return [r for r in self._rules.values() if r.category == category]
        return list(self._rules.values())
    
    def get_rule(self, rule_id: str) -> Optional[Rule]:
        """Get a specific rule by ID."""
        return self._rules.get(rule_id)
    
    def enable_rule(self, rule_id: str):
        """Enable a rule."""
        if rule_id in self._rules:
            self._rules[rule_id].enabled = True
            logger.info("rule_enabled", rule_id=rule_id)
    
    def disable_rule(self, rule_id: str):
        """Disable a rule."""
        if rule_id in self._rules:
            self._rules[rule_id].enabled = False
            logger.info("rule_disabled", rule_id=rule_id)
    
    async def evaluate(
        self,
        request_type: str,
        request_data: Dict[str, Any],
        trace_id: str,
        correlation_id: str,
        causation_id: Optional[str] = None
    ) -> GovernanceDecision:
        """Evaluate a governance request against all applicable rules."""
        decision_id = str(uuid.uuid4())
        request_id = request_data.get("request_id", str(uuid.uuid4()))
        
        # Get applicable rules
        applicable_rules = self._get_applicable_rules(request_type)
        
        # Evaluate each rule
        rule_evaluations = []
        for rule in applicable_rules:
            if not rule.enabled:
                continue
            
            handler = self._rule_handlers.get(rule.category)
            if handler:
                result = await handler.evaluate(rule, request_data)
                rule_evaluations.append(result.dict())
        
        # Determine overall decision
        decision = self._make_decision(
            decision_id,
            request_id,
            request_type,
            rule_evaluations,
            trace_id,
            correlation_id,
            causation_id
        )
        
        logger.info(
            "decision_made",
            decision_id=decision_id,
            request_type=request_type,
            approved=decision.approved,
            confidence=decision.confidence
        )
        
        return decision
    
    def _get_applicable_rules(self, request_type: str) -> List[Rule]:
        """Get rules that apply to a request type."""
        applicable = []
        for rule in self._rules.values():
            if not rule.enabled:
                continue
            
            # Check if rule applies to this request type
            applies_to = rule.applies_to
            if "*" in applies_to or request_type in applies_to:
                applicable.append(rule)
        
        return applicable
    
    def _make_decision(
        self,
        decision_id: str,
        request_id: str,
        request_type: str,
        rule_evaluations: List[Dict[str, Any]],
        trace_id: str,
        correlation_id: str,
        causation_id: Optional[str]
    ) -> GovernanceDecision:
        """Make a governance decision based on rule evaluations."""
        # Count triggered rules by action
        block_count = sum(1 for r in rule_evaluations if r.get("action") == RuleAction.BLOCK and r.get("triggered"))
        require_approval_count = sum(1 for r in rule_evaluations if r.get("action") == RuleAction.REQUIRE_APPROVAL and r.get("triggered"))
        warn_count = sum(1 for r in rule_evaluations if r.get("action") == RuleAction.WARN and r.get("triggered"))
        
        # Determine approval
        approved = block_count == 0
        
        # Determine status
        if block_count > 0:
            status = DecisionStatus.REJECTED
            confidence = 1.0
        elif require_approval_count > 0:
            status = DecisionStatus.CONDITIONAL
            confidence = 0.5
        elif warn_count > 0:
            status = DecisionStatus.APPROVED
            confidence = 0.7
        else:
            status = DecisionStatus.APPROVED
            confidence = 1.0
        
        # Build rationale
        rationale_parts = []
        if block_count > 0:
            rationale_parts.append(f"{block_count} blocking rule(s) triggered")
        if require_approval_count > 0:
            rationale_parts.append(f"{require_approval_count} rule(s) require approval")
        if warn_count > 0:
            rationale_parts.append(f"{warn_count} warning(s) issued")
        
        if not rationale_parts:
            rationale = "All rules passed"
        else:
            rationale = "; ".join(rationale_parts)
        
        # Build conditions if conditional
        conditions = None
        if status == DecisionStatus.CONDITIONAL:
            conditions = {
                "requires_approval": True,
                "blocking_rules": [r for r in rule_evaluations if r.get("action") == RuleAction.BLOCK and r.get("triggered")],
                "approval_rules": [r for r in rule_evaluations if r.get("action") == RuleAction.REQUIRE_APPROVAL and r.get("triggered")]
            }
        
        # Set expiration for conditional approvals
        expires_at = None
        if status == DecisionStatus.CONDITIONAL:
            from ..utils.config import settings
            expires_at = datetime.utcnow() + timedelta(seconds=settings.decision_ttl)
        
        return GovernanceDecision(
            decision_id=decision_id,
            request_id=request_id,
            request_type=request_type,
            approved=approved,
            status=status,
            confidence=confidence,
            rationale=rationale,
            conditions=conditions,
            expires_at=expires_at,
            version="1.0.0",
            trace_id=trace_id,
            correlation_id=correlation_id,
            causation_id=causation_id,
            evaluated_by="governance-engine",
            evaluated_at=datetime.utcnow(),
            rule_evaluations=rule_evaluations,
            metadata={
                "total_rules_evaluated": len(rule_evaluations),
                "block_count": block_count,
                "require_approval_count": require_approval_count,
                "warn_count": warn_count
            }
        )
