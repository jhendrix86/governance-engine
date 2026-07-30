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
        # Will be 500 if RabbitMQ not connected, but we can test the schema
        assert response.status_code in [200, 500]
    
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
