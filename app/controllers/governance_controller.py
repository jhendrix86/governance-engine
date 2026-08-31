from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any, Optional
import structlog
from ..schemas import GovernanceCheckRequest, GovernanceCheckResponse, LogActionRequest
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
    """Dependency for governance service.

    Wires the service to the app-level EventEmitter that `startup_event()`
    in `app/main.py` already `.connect()`ed to RabbitMQ - NOT a fresh one.
    A fresh `EventEmitter(settings.rabbitmq_url)` has `_publisher = None`,
    so `emit_decision()` AttributeErrors on every governance decision
    (currently swallowed by governance_service.py's try/except, so
    decisions silently never emit their audit event). Same pattern as
    global-state-manager's get_state_manager().
    """
    from ..services.governance_service import GovernanceService
    from .. import main as app_main

    # Production path: startup_event() has run, so use its RabbitMQ-connected
    # EventEmitter (and the rule_engine/tracer alongside it).
    if app_main.event_emitter is not None:
        return GovernanceService(app_main.rule_engine, app_main.event_emitter, app_main.tracer)

    # Fallback: startup hasn't run (e.g. TestClient with no lifespan
    # context). Fresh instances; event emission is best-effort here and
    # governance_service.check_governance() already tolerates a failed
    # publish without discarding the decision.
    from ..services.event_emitter import EventEmitter
    from ..utils.config import settings
    from ..tracing import Tracer
    return GovernanceService(RuleEngine(), EventEmitter(settings.rabbitmq_url), Tracer("governance-engine"))


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


@router.post("/log-action")
async def log_action(
    request: LogActionRequest,
    governance_service: GovernanceService = Depends(get_governance_service),
):
    """
    Record an operator execution outcome (distinct from /check's policy
    decisions). Added 2026-08-11 to close a real gap: empire_os's
    GovernanceEngine bridge (engines/governance_engine.py) has called this
    exact path since the Stage 3.2 governance bridge - it always 404'd,
    silently swallowed by a broad except on the caller's side, so this
    audit trail has never actually recorded anything until now.
    """
    try:
        entry = governance_service.log_action(
            operator_name=request.operator_name,
            operator_type=request.operator_type,
            result_success=request.result_success,
            context=request.context,
            logged_by=request.requester,
        )
        return {"success": True, "entry": entry.dict()}
    except Exception as e:
        logger.error("api_log_action_error", error=str(e))
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
