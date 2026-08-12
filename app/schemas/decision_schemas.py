from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum


class DecisionStatus(str, Enum):
    """Governance decision status."""
    APPROVED = "approved"
    REJECTED = "rejected"
    CONDITIONAL = "conditional"
    PENDING = "pending"
    OVERRIDDEN = "overridden"


class GovernanceDecision(BaseModel):
    """Governance decision with full metadata."""
    decision_id: str = Field(..., description="Unique decision ID")
    request_id: str = Field(..., description="Associated request ID")
    request_type: str = Field(..., description="Type of request")
    approved: bool = Field(..., description="Whether the request was approved")
    status: DecisionStatus = Field(..., description="Decision status")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Decision confidence score")
    rationale: str = Field(..., description="Decision rationale")
    conditions: Optional[Dict[str, Any]] = Field(None, description="Conditions if conditional approval")
    expires_at: Optional[datetime] = Field(None, description="Decision expiration time")
    version: str = Field(default="1.0.0", description="Decision schema version")
    trace_id: str = Field(..., description="Trace ID for distributed tracing")
    correlation_id: str = Field(..., description="Correlation ID")
    causation_id: Optional[str] = Field(None, description="Causation ID")
    evaluated_by: str = Field(..., description="Engine/service that evaluated")
    evaluated_at: datetime = Field(default_factory=datetime.utcnow, description="Decision timestamp")
    rule_evaluations: List[Dict[str, Any]] = Field(default_factory=list, description="Individual rule evaluations")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class GovernanceCheckRequest(BaseModel):
    """Request for governance check."""
    request_type: str = Field(..., description="Type of governance request")
    request_data: Dict[str, Any] = Field(..., description="Request payload")
    requester: str = Field(..., description="Requesting engine/service")
    priority: str = Field(default="normal", description="Request priority")
    trace_id: Optional[str] = Field(None, description="Trace ID if continuing a trace")
    correlation_id: Optional[str] = Field(None, description="Correlation ID")
    causation_id: Optional[str] = Field(None, description="Causation ID")
    context: Dict[str, Any] = Field(default_factory=dict, description="Additional context")


class GovernanceCheckResponse(BaseModel):
    """Response from governance check."""
    success: bool = Field(..., description="Whether the check was successful")
    decision: Optional[GovernanceDecision] = Field(None, description="Governance decision")
    error: Optional[str] = Field(None, description="Error message if failed")
    trace_id: str = Field(..., description="Trace ID for distributed tracing")
    processing_time_ms: float = Field(..., description="Processing time in milliseconds")


class OperatorActionLog(BaseModel):
    """
    Audit record of an operator's execution OUTCOME - distinct from a
    GovernanceDecision, which records a POLICY decision (was this allowed).
    This is the "what actually happened when it ran" side, requested by
    empire_os's GovernanceEngine bridge (engines/governance_engine.py)
    since 2026-08-10's Stage 3.2 work, but with no real endpoint to receive
    it until now - every call 404'd, silently swallowed by a broad except.
    """
    operator_name: str = Field(..., description="Name of the executed operator")
    operator_type: str = Field(..., description="Type of operator")
    result_success: bool = Field(..., description="Whether execution succeeded")
    context: Dict[str, Any] = Field(default_factory=dict, description="Execution context")
    logged_by: str = Field(..., description="Engine/service that logged this")
    logged_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


class LogActionRequest(BaseModel):
    """Request body for POST /governance/log-action - matches exactly what
    empire_os's GovernanceEngine._log_governance_action() sends today
    (which doesn't include a requester field); `requester` is optional so
    other, better-behaved future callers can identify themselves."""
    operator_name: str
    operator_type: str
    result_success: bool
    context: Dict[str, Any] = Field(default_factory=dict)
    requester: str = Field(default="unknown")
