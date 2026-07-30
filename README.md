# Governance Engine

The CEO AI of the Autonomous Company OS. This service provides governance and decision-making capabilities, evaluating autonomous actions against safety, brand, compliance, resource, strategy, risk, market, temporal, and causal rules.

## Features

- **Rule Engine** - 9 rule categories with 20+ governance rules
- **Request Types** - 14 governance request types (funnel, product, resource, risk, strategy, emergency)
- **Decision Metadata** - Full decision tracking with confidence scores, rationale, and conditions
- **Event Emission** - Emits governance events (approved, rejected, override, emergency stop, rollback)
- **API Endpoints** - Synchronous governance check, history, rules inspection, override, emergency stop, rollback
- **Distributed Tracing** - OpenTelemetry integration with W3C traceparent support
- **DLQ Management** - Dead letter queue with replay capabilities
- **Override Logic** - Support for decision overrides with justification
- **Kill-Switch** - Emergency stop functionality for critical situations
- **Rollback** - Trigger rollback to previous states

## Architecture

```
┌─────────────┐    Request    ┌──────────────┐
│   Engine    │ ────────────> │ Governance   │
│  (Any)      │              │   Service    │
└─────────────┘              └──────┬───────┘
                                   │
                    ┌──────────────┼──────────────┐
                    │              │              │
            ┌───────▼──────┐ ┌────▼────┐ ┌────▼──────┐
            │  Rule Engine │ │Emitter  │ │  Tracer   │
            │  (9 Categories)│ │(Events) │ │  (OTel)   │
            └──────────────┘ └─────────┘ └───────────┘
                    │
            ┌───────▼──────┐
            │  Decision    │
            │  Metadata    │
            └──────────────┘
                    │
            ┌───────▼──────┐
            │  RabbitMQ    │
            │  (Events)    │
            └──────────────┘
```

## Installation

### Prerequisites

- Python 3.9+
- RabbitMQ 3.12+
- Docker (optional, for containerized deployment)

### Local Development

```bash
# Clone repository
git clone https://github.com/autonomous-company/governance-engine.git
cd governance-engine

# Install dependencies
pip install -r requirements.txt

# Set environment variables
cp .env.example .env
# Edit .env with your configuration

# Run the service
uvicorn app.main:app --reload --port 8033
```

### Docker Deployment

```bash
# Build and start all services
cd docker
docker-compose up -d

# View logs
docker-compose logs -f governance-engine

# Stop services
docker-compose down
```

## Configuration

Configuration is managed via environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `RABBITMQ_URL` | `amqp://localhost:5672` | RabbitMQ connection URL |
| `RABBITMQ_EXCHANGE` | `autonomy.events` | RabbitMQ exchange name |
| `OTEL_ENABLED` | `true` | Enable OpenTelemetry tracing |
| `OTEL_ENDPOINT` | `http://localhost:4318` | OTLP endpoint |
| `DEFAULT_CONFIDENCE_THRESHOLD` | `0.7` | Default confidence threshold |
| `DECISION_TTL` | `3600` | Decision TTL in seconds |

## Rule Categories

### Safety Rules
- No profanity in content
- No illegal activities
- Data privacy compliance
- Rate limit protection
- Budget safety limits

### Brand Rules
- Brand voice consistency
- Logo usage guidelines
- Color scheme compliance
- Competitor references

### Compliance Rules
- GDPR compliance
- Terms of service
- Age restrictions
- FTC disclosure

### Resource Rules
- Compute resource limits
- API rate limits
- Budget allocation
- Resource priority

### Strategy Rules
- Strategic alignment
- Market fit validation
- Resource efficiency
- Competitive differentiation

### Risk Rules
- High risk mitigation
- Risk threshold
- Override justification

### Market Rules
- Market saturation
- Competitive density
- Market size validation

### Temporal Rules
- Business hours only
- Rate limit window
- Cooldown period

### Causal Rules
- Causal chain validation
- Historical pattern check
- Dependency validation

## Request Types

### Funnel Requests
- `funnel.create_request` - Create a new funnel
- `funnel.launch_request` - Launch a funnel
- `funnel.mutation_request` - Mutate a funnel
- `funnel.archive_request` - Archive a funnel

### Product Requests
- `product.create_request` - Create a product
- `product.publish_request` - Publish a product
- `product.update_request` - Update a product

### Resource Requests
- `resource.compute_request` - Request compute resources
- `resource.api_request` - Request API access
- `resource.budget_request` - Request budget allocation

### Risk Requests
- `risk.assessment_request` - Request risk assessment
- `risk.override_request` - Override a risk decision

### Strategy Requests
- `strategy.alignment_request` - Check strategy alignment
- `strategy.override_request` - Override a strategy

### Emergency Requests
- `emergency.stop_request` - Emergency stop
- `emergency.rollback_request` - Emergency rollback

## API Endpoints

### Health & Info
- `GET /health` - Health check
- `GET /` - Service information

### Governance
- `POST /governance/check` - Synchronous governance check
- `GET /governance/history/{entity_id}` - Get governance history
- `GET /governance/rules` - Get all rules
- `GET /governance/rules?category={category}` - Get rules by category
- `POST /governance/override` - Override a decision
- `POST /governance/emergency-stop` - Trigger emergency stop
- `POST /governance/rollback` - Trigger rollback

### DLQ Management
- `GET /dlq/stats` - Get DLQ statistics
- `GET /dlq/messages` - Peek at DLQ messages
- `POST /dlq/replay/{event_id}` - Replay specific message
- `POST /dlq/replay-batch` - Replay batch of messages
- `POST /dlq/purge` - Purge old messages

## Usage Examples

### Governance Check

```python
import httpx

async def check_governance():
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8033/governance/check",
            json={
                "request_type": "funnel.create_request",
                "request_data": {
                    "funnel_id": "funnel-123",
                    "niche": "fitness",
                    "strategy": "content_first",
                    "target_audience": "fitness enthusiasts",
                    "requester": "autonomous-engine",
                    "context": {
                        "gdpr_consent": True,
                        "data_minimization": True
                    }
                },
                "requester": "autonomous-engine"
            }
        )
        return response.json()
```

### Emergency Stop

```python
async def emergency_stop(entity_type: str, entity_id: str, reason: str):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8033/governance/emergency-stop",
            json={
                "entity_type": entity_type,
                "entity_id": entity_id,
                "reason": reason,
                "severity": "critical",
                "requester": "governance-engine"
            }
        )
        return response.json()
```

### Override Decision

```python
async def override_decision(decision_id: str, reason: str):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8033/governance/override",
            json={
                "decision_id": decision_id,
                "override_reason": reason,
                "requester": "admin"
            }
        )
        return response.json()
```

## Decision Metadata

Every governance decision includes:

- `decision_id` - Unique decision identifier
- `request_id` - Associated request ID
- `request_type` - Type of request
- `approved` - Whether the request was approved
- `status` - Decision status (approved, rejected, conditional, pending, overridden)
- `confidence` - Decision confidence score (0-1)
- `rationale` - Decision rationale
- `conditions` - Conditions if conditional approval
- `expires_at` - Decision expiration time
- `version` - Decision schema version
- `trace_id` - Trace ID for distributed tracing
- `correlation_id` - Correlation ID
- `causation_id` - Causation ID
- `evaluated_by` - Engine that evaluated
- `evaluated_at` - Decision timestamp
- `rule_evaluations` - Individual rule evaluations
- `metadata` - Additional metadata

## Event Emission

The service emits the following events:

- `governance.approved` - Request approved
- `governance.rejected` - Request rejected
- `governance.override` - Decision overridden
- `governance.emergency_stop` - Emergency stop triggered
- `governance.rollback_triggered` - Rollback triggered

## Development

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_rule_engine.py
```

### Adding New Rules

1. Create a new rule file in `app/rules/`
2. Implement `get_rules()` and `evaluate()` methods
3. Add the rule handler to `RuleEngine._rule_handlers`
4. Add rule category to `RuleCategory` enum

### Adding New Request Types

1. Add request schema to `app/schemas/request_schemas.py`
2. Add request type to `RequestType` enum
3. Update rule `applies_to` lists as needed

## Monitoring

### OpenTelemetry Tracing

The service exports traces to OTLP endpoint (default: `http://localhost:4318`). View traces in Jaeger UI at `http://localhost:16686`.

### Health Check

```bash
curl http://localhost:8033/health
```

## Troubleshooting

### RabbitMQ Connection Failed

- Check RabbitMQ is running: `docker ps | grep rabbitmq`
- Verify connection URL in environment variables
- Check RabbitMQ logs: `docker logs governance-rabbitmq`

### Rules Not Loading

- Check rule files are in `app/rules/`
- Verify rule handlers are registered in `RuleEngine`
- Check logs for rule loading errors

### Decision Not Emitted

- Check event emitter is connected to RabbitMQ
- Verify exchange exists
- Check DLQ for failed messages

## License

MIT License

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request
