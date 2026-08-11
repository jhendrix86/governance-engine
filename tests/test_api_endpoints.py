import pytest
from fastapi.testclient import TestClient
from app.main import app


client = TestClient(app)


class TestHealthEndpoints:
    def test_health_check(self):
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "service" in data
        assert "status" in data
        assert data["status"] == "healthy"
    
    def test_root(self):
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "service" in data
        assert "version" in data
        assert "docs" in data


class TestGovernanceEndpoints:
    def test_check_governance(self):
        request_data = {
            "request_type": "funnel.create_request",
            "request_data": {
                "request_id": "test-123",
                "funnel_id": "funnel-123",
                "niche": "fitness",
                "strategy": "content_first",
                "target_audience": "fitness enthusiasts",
                "requester": "autonomous-engine",
                "context": {
                    "contains_profanity": False,
                    "gdpr_consent": True,
                    "data_minimization": True
                }
            },
            "requester": "autonomous-engine"
        }
        
        response = client.post("/governance/check", json=request_data)
        # Real bug fixed 2026-08-11: get_governance_service() builds a
        # fresh, never-connected EventEmitter per request, so publishing
        # the decision used to raise AttributeError and this endpoint
        # always returned success=False regardless of the real rule
        # outcome - this assertion used to hedge with `in [200, 500]`
        # because nobody had actually confirmed which one happened. It's
        # always 200 with a real decision now: event-emission failures are
        # caught and logged, not allowed to discard an already-computed
        # decision (see governance_service.py's check_governance()).
        assert response.status_code == 200
        body = response.json()
        assert body["success"] is True
        assert body["decision"] is not None
        assert body["decision"]["request_type"] == "funnel.create_request"
        # Real rule evaluation, not a canned response: this specific
        # request_data (no ToS acceptance, no explicit strategic alignment
        # signal) genuinely triggers real require_approval rules.
        assert body["decision"]["status"] == "conditional"
        assert body["decision"]["approved"] is False

    def test_check_governance_operator_execute_request(self):
        """
        The request_type empire_os's engines/governance_engine.py bridge
        actually sends (added 2026-08-11 alongside the bridge's own fix -
        see request_schemas.py's RequestType.OPERATOR_EXECUTE docstring).
        No operator-specific rule exists, only the two "*"-scoped ones
        (safety_002, risk_002) - proving those still apply to a request
        type with no dedicated rules of its own.
        """
        response = client.post("/governance/check", json={
            "request_type": "operator.execute_request",
            "request_data": {"operator_name": "SomeOperator", "operator_type": "generic"},
            "requester": "empire_os",
            "context": {},
        })
        assert response.status_code == 200
        body = response.json()
        assert body["success"] is True
        assert body["decision"]["approved"] is True
        evaluated_rule_ids = {r["rule_id"] for r in body["decision"]["rule_evaluations"]}
        assert evaluated_rule_ids == {"safety_002", "risk_002"}

    def test_get_rules(self):
        response = client.get("/governance/rules")
        assert response.status_code == 200
        data = response.json()
        assert "rules" in data
        assert "count" in data
        assert data["count"] > 0
    
    def test_get_rules_by_category(self):
        response = client.get("/governance/rules?category=safety")
        assert response.status_code == 200
        data = response.json()
        assert "rules" in data
        assert "category" in data
        assert data["category"] == "safety"
    
    def test_get_history(self):
        response = client.get("/governance/history/test-entity")
        assert response.status_code == 200
        data = response.json()
        assert "entity_id" in data
        assert "history" in data


class TestDLQEndpoints:
    def test_get_dlq_stats(self):
        response = client.get("/dlq/stats")
        assert response.status_code in [200, 500]
    
    def test_peek_dlq_messages(self):
        response = client.get("/dlq/messages?limit=10")
        assert response.status_code in [200, 500]
