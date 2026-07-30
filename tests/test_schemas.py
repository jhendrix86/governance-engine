import pytest
from app.schemas.request_schemas import (
    FunnelCreateRequest,
    FunnelLaunchRequest,
    EmergencyStopRequest,
    RequestType
)
from app.schemas.decision_schemas import (
    GovernanceDecision,
    DecisionStatus,
    GovernanceCheckRequest
)
from app.schemas.rule_schemas import Rule, RuleCategory, RuleSeverity, RuleAction


class TestRequestSchemas:
    def test_funnel_create_request(self):
        request = FunnelCreateRequest(
            funnel_id="funnel-123",
            niche="fitness",
            strategy="content_first",
            target_audience="fitness enthusiasts",
            requester="autonomous-engine"
        )
        
        assert request.funnel_id == "funnel-123"
        assert request.niche == "fitness"
        assert request.strategy == "content_first"
        assert request.estimated_budget == 0.0
    
    def test_funnel_launch_request(self):
        request = FunnelLaunchRequest(
            funnel_id="funnel-123",
            launch_config={"auto_optimize": True},
            channels=["twitter", "linkedin"],
            requester="autonomous-engine"
        )
        
        assert request.funnel_id == "funnel-123"
        assert len(request.channels) == 2
    
    def test_emergency_stop_request(self):
        request = EmergencyStopRequest(
            entity_type="funnel",
            entity_id="funnel-123",
            reason="Critical safety violation",
            severity="critical",
            requester="governance-engine"
        )
        
        assert request.entity_type == "funnel"
        assert request.severity == "critical"
    
    def test_request_type_enum(self):
        assert RequestType.FUNNEL_CREATE == "funnel.create_request"
        assert RequestType.EMERGENCY_STOP == "emergency.stop_request"


class TestDecisionSchemas:
    def test_governance_decision(self):
        from datetime import datetime
        
        decision = GovernanceDecision(
            decision_id="decision-123",
            request_id="request-123",
            request_type="funnel.create_request",
            approved=True,
            status=DecisionStatus.APPROVED,
            confidence=0.9,
            rationale="All rules passed",
            trace_id="trace-123",
            correlation_id="corr-123",
            evaluated_by="governance-engine"
        )
        
        assert decision.decision_id == "decision-123"
        assert decision.approved is True
        assert decision.confidence == 0.9
        assert decision.status == DecisionStatus.APPROVED
    
    def test_governance_check_request(self):
        request = GovernanceCheckRequest(
            request_type="funnel.create_request",
            request_data={"funnel_id": "funnel-123"},
            requester="autonomous-engine"
        )
        
        assert request.request_type == "funnel.create_request"
        assert request.priority == "normal"
    
    def test_decision_status_enum(self):
        assert DecisionStatus.APPROVED == "approved"
        assert DecisionStatus.REJECTED == "rejected"
        assert DecisionStatus.CONDITIONAL == "conditional"


class TestRuleSchemas:
    def test_rule_creation(self):
        from datetime import datetime
        
        rule = Rule(
            rule_id="test_001",
            name="Test Rule",
            category=RuleCategory.SAFETY,
            description="A test rule",
            severity=RuleSeverity.MEDIUM,
            action=RuleAction.WARN
        )
        
        assert rule.rule_id == "test_001"
        assert rule.category == RuleCategory.SAFETY
        assert rule.action == RuleAction.WARN
        assert rule.enabled is True
    
    def test_rule_category_enum(self):
        assert RuleCategory.SAFETY == "safety"
        assert RuleCategory.BRAND == "brand"
        assert RuleCategory.COMPLIANCE == "compliance"
    
    def test_rule_severity_enum(self):
        assert RuleSeverity.INFO == "info"
        assert RuleSeverity.HIGH == "high"
        assert RuleSeverity.CRITICAL == "critical"
    
    def test_rule_action_enum(self):
        assert RuleAction.ALLOW == "allow"
        assert RuleAction.WARN == "warn"
        assert RuleAction.BLOCK == "block"
        assert RuleAction.REQUIRE_APPROVAL == "require_approval"
