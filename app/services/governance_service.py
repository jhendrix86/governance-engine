from typing import Dict, Any, Optional
import structlog
from ..rules import RuleEngine
from ..schemas.decision_schemas import GovernanceDecision, GovernanceCheckRequest, GovernanceCheckResponse
from ..tracing import Tracer, TraceParent
from ..services import EventEmitter


logger = structlog.get_logger()


class GovernanceService:
    """Main governance service for evaluating requests."""
    
    def __init__(
        self,
        rule_engine: RuleEngine,
        event_emitter: EventEmitter,
        tracer: Tracer
    ):
        self.rule_engine = rule_engine
        self.event_emitter = event_emitter
        self.tracer = tracer
        
        # Decision history (in production, this would be in a database)
        self._decision_history: Dict[str, GovernanceDecision] = {}
    
    async def check_governance(
        self,
        request: GovernanceCheckRequest,
        trace_parent: Optional[TraceParent] = None
    ) -> GovernanceCheckResponse:
        """Check governance for a request."""
        start_time = structlog.get_logger().bind(service="governance")
        
        # Start trace span
        if trace_parent:
            trace_parent = self.tracer.start_span("governance.check", parent=trace_parent)
        else:
            trace_parent = self.tracer.start_span("governance.check")
        
        trace_id = trace_parent.trace_context.trace_id
        correlation_id = request.correlation_id or trace_parent.trace_context.trace_id
        causation_id = request.causation_id
        
        try:
            # Evaluate request against rules
            decision = await self.rule_engine.evaluate(
                request_type=request.request_type,
                request_data=request.request_data,
                trace_id=trace_id,
                correlation_id=correlation_id,
                causation_id=causation_id
            )
            
            # Store decision in history
            self._decision_history[decision.decision_id] = decision
            
            # Emit governance event
            await self.event_emitter.emit_decision(decision, trace_parent)
            
            # Finish trace
            self.tracer.finish_span(trace_parent, "governance.check", True)
            
            return GovernanceCheckResponse(
                success=True,
                decision=decision,
                trace_id=trace_id,
                processing_time_ms=0.0
            )
        
        except Exception as e:
            logger.error("governance_check_error", error=str(e), trace_id=trace_id)
            self.tracer.finish_span(trace_parent, "governance.check", False, error=str(e))
            
            return GovernanceCheckResponse(
                success=False,
                error=str(e),
                trace_id=trace_id,
                processing_time_ms=0.0
            )
    
    def get_decision_history(self, entity_id: str) -> list:
        """Get governance history for an entity."""
        # In production, this would query a database
        return [
            decision.dict()
            for decision in self._decision_history.values()
            if entity_id in str(decision.request_data)
        ]
    
    def get_decision(self, decision_id: str) -> Optional[GovernanceDecision]:
        """Get a specific decision by ID."""
        return self._decision_history.get(decision_id)
    
    async def override_decision(
        self,
        decision_id: str,
        override_reason: str,
        requester: str,
        trace_parent: Optional[TraceParent] = None
    ) -> bool:
        """Override a governance decision."""
        decision = self._decision_history.get(decision_id)
        if not decision:
            return False
        
        # Update decision status
        from ..schemas.decision_schemas import DecisionStatus
        decision.status = DecisionStatus.OVERRIDDEN
        decision.rationale = f"OVERRIDDEN: {override_reason}"
        
        # Emit override event
        await self.event_emitter.emit_override(
            override_type=decision.request_type,
            entity_id=decision.request_id,
            reason=override_reason,
            requester=requester,
            trace_parent=trace_parent
        )
        
        logger.info("decision_overridden", decision_id=decision_id, requester=requester)
        return True
    
    async def emergency_stop(
        self,
        entity_type: str,
        entity_id: str,
        reason: str,
        severity: str,
        requester: str,
        trace_parent: Optional[TraceParent] = None
    ):
        """Trigger emergency stop for an entity."""
        # Emit emergency stop event
        await self.event_emitter.emit_emergency_stop(
            entity_type=entity_type,
            entity_id=entity_id,
            reason=reason,
            severity=severity,
            requester=requester,
            trace_parent=trace_parent
        )
        
        logger.info("emergency_stop_triggered", entity_type=entity_type, entity_id=entity_id)
    
    async def rollback(
        self,
        entity_type: str,
        entity_id: str,
        rollback_point: str,
        reason: str,
        requester: str,
        trace_parent: Optional[TraceParent] = None
    ):
        """Trigger rollback for an entity."""
        # Emit rollback event
        await self.event_emitter.emit_rollback_triggered(
            entity_type=entity_type,
            entity_id=entity_id,
            rollback_point=rollback_point,
            reason=reason,
            requester=requester,
            trace_parent=trace_parent
        )
        
        logger.info("rollback_triggered", entity_type=entity_type, entity_id=entity_id)
