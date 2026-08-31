from typing import Dict, Any
import uuid
import structlog
from autonomy_events import EventPublisher, EventEnvelope, EventPriority, TraceParent
from ..schemas.decision_schemas import GovernanceDecision, DecisionStatus


logger = structlog.get_logger()


class EventEmitter:
    """Emit governance events to RabbitMQ."""
    
    def __init__(self, rabbitmq_url: str, exchange_name: str = "autonomy.events"):
        self.rabbitmq_url = rabbitmq_url
        self.exchange_name = exchange_name
        self._publisher: EventPublisher = None
    
    async def connect(self):
        """Connect to RabbitMQ."""
        self._publisher = EventPublisher(
            rabbitmq_url=self.rabbitmq_url,
            exchange_name=self.exchange_name
        )
        await self._publisher.connect()
        logger.info("event_emitter_connected")
    
    async def disconnect(self):
        """Disconnect from RabbitMQ."""
        if self._publisher:
            await self._publisher.disconnect()
        logger.info("event_emitter_disconnected")
    
    async def emit_decision(
        self,
        decision: GovernanceDecision,
        trace_parent: TraceParent = None
    ):
        """Emit a governance decision event."""
        event_type = self._map_decision_to_event(decision.status)
        payload = self._build_decision_payload(event_type, decision)

        envelope = EventEnvelope(
            event_type=event_type,
            engine_id=decision.evaluated_by,
            priority=self._map_priority(decision.status),
            payload=payload
        )
        
        # Inject tracing
        if trace_parent:
            envelope.correlation_id = trace_parent.correlation_id
            envelope.causation_id = trace_parent.causation_id
        else:
            envelope.correlation_id = decision.correlation_id
            envelope.causation_id = decision.causation_id
        
        # Publish event. event_type is already the fully dotted key
        # (e.g. "governance.approved") - prefixing it again produced
        # "governance.governance.approved", a 3-segment key that never
        # matched kg-service's single-wildcard "governance.*" binding
        # (topic-exchange "*" matches exactly one word). Every governance
        # event was silently unroutable to kg-service until this fix.
        routing_key = event_type
        result = await self._publisher.publish(envelope, routing_key, trace_parent)

        if result.success:
            logger.info(
                "governance_event_emitted",
                event_type=event_type,
                decision_id=decision.decision_id,
                message_id=result.message_id
            )
        else:
            logger.error(
                "governance_event_emit_failed",
                event_type=event_type,
                decision_id=decision.decision_id,
                error=result.error
            )
    
    async def emit_override(
        self,
        override_type: str,
        entity_id: str,
        reason: str,
        requester: str,
        trace_parent: TraceParent = None
    ):
        """Emit a governance override event."""
        # Payload shape must match autonomy_events' GovernanceOverride
        # schema, not this method's own param names - see emit_decision's
        # docstring for why that mismatch was previously invisible.
        payload = {
            "original_request_id": entity_id,
            "override_by": requester,
            "override_reason": reason,
            "override_token": str(uuid.uuid4()),
            "risk_assessment": {},
            "requires_approval": False,
        }

        envelope = EventEnvelope(
            event_type="governance.override",
            engine_id="governance-engine",
            priority=EventPriority.HIGH,
            payload=payload
        )
        
        if trace_parent:
            envelope.correlation_id = trace_parent.correlation_id
            envelope.causation_id = trace_parent.causation_id
        
        routing_key = "governance.override"
        result = await self._publisher.publish(envelope, routing_key, trace_parent)
        
        logger.info(
            "override_event_emitted",
            override_type=override_type,
            entity_id=entity_id
        )
    
    async def emit_emergency_stop(
        self,
        entity_type: str,
        entity_id: str,
        reason: str,
        severity: str,
        requester: str,
        trace_parent: TraceParent = None
    ):
        """Emit an emergency stop event."""
        # Payload shape must match autonomy_events' GovernanceEmergencyStop
        # schema (scope/triggered_by are required there, not present here).
        payload = {
            "scope": entity_type,
            "scope_id": entity_id,
            "reason": reason,
            "triggered_by": requester,
            "severity": severity,
            "affected_entities": [entity_id],
        }

        envelope = EventEnvelope(
            event_type="governance.emergency_stop",
            engine_id="governance-engine",
            priority=EventPriority.CRITICAL,
            payload=payload
        )
        
        if trace_parent:
            envelope.correlation_id = trace_parent.correlation_id
            envelope.causation_id = trace_parent.causation_id
        
        routing_key = "governance.emergency_stop"
        result = await self._publisher.publish(envelope, routing_key, trace_parent)
        
        logger.info(
            "emergency_stop_event_emitted",
            entity_type=entity_type,
            entity_id=entity_id
        )
    
    async def emit_rollback_triggered(
        self,
        entity_type: str,
        entity_id: str,
        rollback_point: str,
        reason: str,
        requester: str,
        trace_parent: TraceParent = None
    ):
        """Emit a rollback triggered event."""
        # There is no "governance.rollback_triggered" entry in
        # autonomy_events' schema registry at all (only
        # "safety.rollback_triggered" -> SafetyRollbackTriggered) - every
        # publish here failed validation with "Unknown event type", not
        # just a field mismatch. Reusing the existing safety schema
        # instead of inventing a new registry entry unilaterally.
        payload = {
            "rollback_type": entity_type,
            "triggered_by": requester,
            "reason": reason,
            "scope": {"entity_type": entity_type, "entity_id": entity_id, "rollback_point": rollback_point},
            "affected_entities": [entity_id],
        }

        envelope = EventEnvelope(
            event_type="safety.rollback_triggered",
            engine_id="governance-engine",
            priority=EventPriority.HIGH,
            payload=payload
        )

        if trace_parent:
            envelope.correlation_id = trace_parent.correlation_id
            envelope.causation_id = trace_parent.causation_id

        routing_key = "safety.rollback_triggered"
        result = await self._publisher.publish(envelope, routing_key, trace_parent)
        
        logger.info(
            "rollback_event_emitted",
            entity_type=entity_type,
            entity_id=entity_id
        )
    
    def _map_decision_to_event(self, status: DecisionStatus) -> str:
        """Map decision status to event type.

        Must match a key in autonomy_events' EventValidator.SCHEMA_MAPPING
        or every publish fails schema validation ("Unknown event type").
        There is no "governance.conditional" schema in that registry - a
        CONDITIONAL decision is "this request needs further approval",
        which is exactly what GovernanceRequest already models, so it's
        routed there instead of a status-specific type that doesn't exist.
        """
        mapping = {
            DecisionStatus.APPROVED: "governance.approved",
            DecisionStatus.REJECTED: "governance.rejected",
            DecisionStatus.CONDITIONAL: "governance.request",
            DecisionStatus.PENDING: "governance.request",
            DecisionStatus.OVERRIDDEN: "governance.override"
        }
        return mapping.get(status, "governance.request")

    def _build_decision_payload(self, event_type: str, decision: GovernanceDecision) -> Dict[str, Any]:
        """Build a payload conforming to the schema autonomy_events'
        EventValidator will validate `event_type` against.

        These payloads previously used this service's own internal
        GovernanceDecision field names (decision_id, evaluated_by, ...),
        which don't exist on any of the shared autonomy_events schemas -
        every real publish failed schema validation. That failure was
        masked until now by get_governance_service() handing out a
        fresh, unconnected EventEmitter per request (fixed in e4fb96c),
        which crashed on `self._publisher.publish(...)` with an
        AttributeError before validation ever ran.
        """
        if event_type == "governance.approved":
            conditions = decision.conditions or {}
            return {
                "request_id": decision.request_id,
                "approved_by": decision.evaluated_by,
                "conditions": list(conditions.keys()),
                "expires_at": decision.expires_at,
                "approval_token": decision.decision_id,
                "scope": decision.metadata,
            }
        if event_type == "governance.rejected":
            blocking = [
                r for r in decision.rule_evaluations
                if r.get("action") == "block" and r.get("triggered")
            ]
            return {
                "request_id": decision.request_id,
                "rejected_by": decision.evaluated_by,
                "reason": decision.rationale,
                "suggestions": [],
                "violation_type": blocking[0].get("rule_name") if blocking else None,
                "can_retry": True,
            }
        # governance.request (PENDING, and CONDITIONAL - see _map_decision_to_event)
        return {
            "request_id": decision.request_id,
            "action_type": decision.request_type,
            "payload": decision.conditions or {},
            "requester": decision.evaluated_by,
            "priority": "normal",
            "context": decision.metadata,
        }
    
    def _map_priority(self, status: DecisionStatus) -> EventPriority:
        """Map decision status to event priority."""
        if status == DecisionStatus.REJECTED:
            return EventPriority.HIGH
        elif status == DecisionStatus.CONDITIONAL:
            return EventPriority.NORMAL
        elif status == DecisionStatus.APPROVED:
            return EventPriority.NORMAL
        else:
            return EventPriority.NORMAL
    
    async def __aenter__(self):
        await self.connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.disconnect()
