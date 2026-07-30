from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any, Optional
import structlog
from ..schemas import GovernanceCheckRequest, GovernanceCheckResponse
from ..rules import RuleEngine
from ..services import GovernanceService
from ..tracing import Tracer, TraceParent


logger = structlog.get_logger()
router = APIRouter(prefix="/governance", tags=["Governance"])


def get_rule_engine():
    """Dependency for rule engine."""
    from ..rules.rule_engine import RuleEngine
    return RuleEngine()


def get_governance_service():
    """Dependency for governance service."""
    from ..services.governance_service import GovernanceService
    from ..services.event_emitter import EventEmitter
    from ..utils.config import settings
    from ..tracing import Tracer
    
    tracer = Tracer("governance-engine")
    rule_engine = RuleEngine()
    event_emitter = EventEmitter(settings.rabbitmq_url)
    
    return GovernanceService(rule_engine, event_emitter, tracer)


def get_tracer():
    """Dependency for tracer."""
    from ..tracing import Tracer
    return Tracer("governance-engine")


@router.post("/check", response_model=GovernanceCheckResponse)
async def check_governance(
    request: GovernanceCheckRequest,
    governance_service: GovernanceService = Depends(get_governance_service),
    tracer: Tracer = Depends(get_tracer)
):
    """Synchronous governance check for a request."""
    trace_parent = tracer.start_span("api.check_governance")
    
    # Extract tracing from request if provided
    if request.trace_id:
        trace_parent.trace_context.trace_id = request.trace_id
    if request.correlation_id:
        trace_parent.correlation_id = request.correlation_id
    if request.causation_id:
        trace_parent.causation_id = request.causation_id
    
    try:
        result = await governance_service.check_governance(request, trace_parent)
        tracer.finish_span(trace_parent, "api.check_governance", True)
        return result
    except Exception as e:
        logger.error("api_check_error", error=str(e))
        tracer.finish_span(trace_parent, "api.check_governance", False, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history/{entity_id}")
async def get_governance_history(
    entity_id: str,
    governance_service: GovernanceService = Depends(get_governance_service),
    tracer: Tracer = Depends(get_tracer)
):
    """Get governance history for an entity."""
    trace_parent = tracer.start_span("api.get_governance_history")
    
    try:
        history = governance_service.get_decision_history(entity_id)
        tracer.finish_span(trace_parent, "api.get_governance_history", True)
        return {"entity_id": entity_id, "history": history, "count": len(history)}
    except Exception as e:
        logger.error("api_history_error", error=str(e))
        tracer.finish_span(trace_parent, "api.get_governance_history", False, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/rules")
async def get_rules(
    category: Optional[str] = None,
    rule_engine: RuleEngine = Depends(get_rule_engine),
    tracer: Tracer = Depends(get_tracer)
):
    """Get governance rules."""
    trace_parent = tracer.start_span("api.get_rules")
    
    try:
        from ..schemas.rule_schemas import RuleCategory
        filter_category = RuleCategory(category) if category else None
        rules = rule_engine.get_rules(filter_category)
        
        tracer.finish_span(trace_parent, "api.get_rules", True)
        
        return {
            "rules": [rule.dict() for rule in rules],
            "count": len(rules),
            "category": category
        }
    except Exception as e:
        logger.error("api_rules_error", error=str(e))
        tracer.finish_span(trace_parent, "api.get_rules", False, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/override")
async def override_decision(
    decision_id: str,
    override_reason: str,
    requester: str,
    governance_service: GovernanceService = Depends(get_governance_service),
    tracer: Tracer = Depends(get_tracer)
):
    """Override a governance decision."""
    trace_parent = tracer.start_span("api.override_decision")
    
    try:
        success = await governance_service.override_decision(
            decision_id=decision_id,
            override_reason=override_reason,
            requester=requester,
            trace_parent=trace_parent
        )
        
        tracer.finish_span(trace_parent, "api.override_decision", True)
        
        if not success:
            raise HTTPException(status_code=404, detail="Decision not found")
        
        return {
            "success": True,
            "decision_id": decision_id,
            "overridden_by": requester
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error("api_override_error", error=str(e))
        tracer.finish_span(trace_parent, "api.override_decision", False, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/emergency-stop")
async def emergency_stop(
    entity_type: str,
    entity_id: str,
    reason: str,
    severity: str = "critical",
    requester: str = "governance-engine",
    governance_service: GovernanceService = Depends(get_governance_service),
    tracer: Tracer = Depends(get_tracer)
):
    """Trigger emergency stop for an entity."""
    trace_parent = tracer.start_span("api.emergency_stop")
    
    try:
        await governance_service.emergency_stop(
            entity_type=entity_type,
            entity_id=entity_id,
            reason=reason,
            severity=severity,
            requester=requester,
            trace_parent=trace_parent
        )
        
        tracer.finish_span(trace_parent, "api.emergency_stop", True)
        
        return {
            "success": True,
            "entity_type": entity_type,
            "entity_id": entity_id,
            "stopped_by": requester
        }
    except Exception as e:
        logger.error("api_emergency_stop_error", error=str(e))
        tracer.finish_span(trace_parent, "api.emergency_stop", False, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/rollback")
async def rollback(
    entity_type: str,
    entity_id: str,
    rollback_point: str,
    reason: str,
    requester: str = "governance-engine",
    governance_service: GovernanceService = Depends(get_governance_service),
    tracer: Tracer = Depends(get_tracer)
):
    """Trigger rollback for an entity."""
    trace_parent = tracer.start_span("api.rollback")
    
    try:
        await governance_service.rollback(
            entity_type=entity_type,
            entity_id=entity_id,
            rollback_point=rollback_point,
            reason=reason,
            requester=requester,
            trace_parent=trace_parent
        )
        
        tracer.finish_span(trace_parent, "api.rollback", True)
        
        return {
            "success": True,
            "entity_type": entity_type,
            "entity_id": entity_id,
            "rollback_point": rollback_point,
            "rolled_back_by": requester
        }
    except Exception as e:
        logger.error("api_rollback_error", error=str(e))
        tracer.finish_span(trace_parent, "api.rollback", False, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))
