import pytest
from app.rules.rule_engine import RuleEngine
from app.rules.safety_rules import SafetyRules
from app.rules.brand_rules import BrandRules
from app.schemas.rule_schemas import RuleCategory, RuleAction


class TestRuleEngine:
    def test_load_rules(self):
        engine = RuleEngine()
        rules = engine.get_rules()
        
        assert len(rules) > 0
        
        # Check for rules from different categories
        categories = set(r.category for r in rules)
        assert RuleCategory.SAFETY in categories
        assert RuleCategory.BRAND in categories
        assert RuleCategory.COMPLIANCE in categories
    
    def test_get_rules_by_category(self):
        engine = RuleEngine()
        safety_rules = engine.get_rules(RuleCategory.SAFETY)
        
        assert all(r.category == RuleCategory.SAFETY for r in safety_rules)
        assert len(safety_rules) > 0
    
    def test_enable_disable_rule(self):
        engine = RuleEngine()
        
        # Get a rule
        rules = engine.get_rules()
        rule = rules[0]
        
        # Disable it
        engine.disable_rule(rule.rule_id)
        assert not engine.get_rule(rule.rule_id).enabled
        
        # Enable it
        engine.enable_rule(rule.rule_id)
        assert engine.get_rule(rule.rule_id).enabled
    
    @pytest.mark.asyncio
    async def test_evaluate_request(self):
        engine = RuleEngine()
        
        request_data = {
            "request_id": "test-123",
            "funnel_id": "funnel-123",
            "niche": "fitness",
            "strategy": "content_first",
            "context": {
                "contains_profanity": False,
                "gdpr_consent": True,
                "data_minimization": True
            }
        }
        
        decision = await engine.evaluate(
            request_type="funnel.create_request",
            request_data=request_data,
            trace_id="trace-123",
            correlation_id="corr-123"
        )
        
        assert decision.decision_id is not None
        assert decision.request_id == "test-123"
        assert decision.approved is not None
        assert decision.confidence >= 0.0
        assert decision.confidence <= 1.0
        assert decision.rationale is not None
        assert len(decision.rule_evaluations) > 0


class TestSafetyRules:
    @pytest.mark.asyncio
    async def test_profanity_rule(self):
        rule = SafetyRules.get_rules()[0]  # First rule is profanity check
        
        # Test with profanity
        request_data = {"context": {"content": "This has profanity"}}
        result = await SafetyRules.evaluate(rule, request_data)
        assert result.triggered is True
        assert result.action == RuleAction.BLOCK
        
        # Test without profanity
        request_data = {"context": {"content": "This is clean content"}}
        result = await SafetyRules.evaluate(rule, request_data)
        assert result.triggered is False
    
    @pytest.mark.asyncio
    async def test_budget_rule(self):
        rule = SafetyRules.get_rules()[4]  # Budget safety rule
        
        # Test with budget over limit
        request_data = {"amount": 15000.0}
        result = await SafetyRules.evaluate(rule, request_data)
        assert result.triggered is True
        
        # Test with budget under limit
        request_data = {"amount": 5000.0}
        result = await SafetyRules.evaluate(rule, request_data)
        assert result.triggered is False


class TestBrandRules:
    @pytest.mark.asyncio
    async def test_brand_voice_rule(self):
        rule = BrandRules.get_rules()[0]  # Brand voice rule
        
        # Test with approved tone
        request_data = {"context": {"tone": "professional"}}
        result = await BrandRules.evaluate(rule, request_data)
        assert result.triggered is False
        
        # Test with unapproved tone
        request_data = {"context": {"tone": "casual"}}
        result = await BrandRules.evaluate(rule, request_data)
        assert result.triggered is True
    
    @pytest.mark.asyncio
    async def test_competitor_claims_rule(self):
        rule = BrandRules.get_rules()[3]  # Competitor claims rule
        
        # Test with false claim
        request_data = {"context": {"content": "Our competitor is a scam"}}
        result = await BrandRules.evaluate(rule, request_data)
        assert result.triggered is True
        assert result.action == RuleAction.BLOCK
