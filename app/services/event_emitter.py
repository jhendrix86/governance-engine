from typing import Dict, Any
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
        
        payload = {
            "decision_id": decision.decision_id,
            "request_id": decision.request_id,
            "request_type": decision.request_type,
            "approved": decision.approved,
            "status": decision.status.value,
            "confidence": decision.confidence,
            "rationale": decision.rationale,
            "conditions": decision.conditions,
            "rule_evaluations": decision.rule_evaluations,
            "evaluated_by": decision.evaluated_by,
            "metadata": decision.metadata
        }
        
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
        
        # Publish event
        routing_key = f"governance.{event_type}"
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
        from datetime import datetime
        payload = {
            "override_type": override_type,
            "entity_id": entity_id,
            "reason": reason,
            "requester": requester,
            "timestamp": datetime.utcnow().isoformat()
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
        payload = {
            "entity_type": entity_type,
            "entity_id": entity_id,
            "reason": reason,
            "severity": severity,
            "requester": requester,
            "affected_entities": [entity_id]
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
        payload = {
            "entity_type": entity_type,
            "entity_id": entity_id,
            "rollback_point": rollback_point,
            "reason": reason,
            "requester": requester,
            "affected_entities": [entity_id]
        }
        
        envelope = EventEnvelope(
            event_type="governance.rollback_triggered",
            engine_id="governance-engine",
            priority=EventPriority.HIGH,
            payload=payload
        )
        
        if trace_parent:
            envelope.correlation_id = trace_parent.correlation_id
            envelope.causation_id = trace_parent.causation_id
        
        routing_key = "governance.rollback_triggered"
        result = await self._publisher.publish(envelope, routing_key, trace_parent)
        
        logger.info(
            "rollback_event_emitted",
            entity_type=entity_type,
            entity_id=entity_id
        )
    
    def _map_decision_to_event(self, status: DecisionStatus) -> str:
        """Map decision status to event type."""
        mapping = {
            DecisionStatus.APPROVED: "governance.approved",
            DecisionStatus.REJECTED: "governance.rejected",
            DecisionStatus.CONDITIONAL: "governance.conditional",
            DecisionStatus.PENDING: "governance.request",
            DecisionStatus.OVERRIDDEN: "governance.override"
        }
        return mapping.get(status, "governance.request")
    
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
