from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum


class RequestType(str, Enum):
    """Governance request types."""
    FUNNEL_CREATE = "funnel.create_request"
    FUNNEL_LAUNCH = "funnel.launch_request"
    FUNNEL_MUTATION = "funnel.mutation_request"
    FUNNEL_ARCHIVE = "funnel.archive_request"
    PRODUCT_CREATE = "product.create_request"
    PRODUCT_PUBLISH = "product.publish_request"
    PRODUCT_UPDATE = "product.update_request"
    RESOURCE_COMPUTE = "resource.compute_request"
    RESOURCE_API = "resource.api_request"
    RESOURCE_BUDGET = "resource.budget_request"
    RISK_ASSESSMENT = "risk.assessment_request"
    RISK_OVERRIDE = "risk.override_request"
    STRATEGY_ALIGNMENT = "strategy.alignment_request"
    STRATEGY_OVERRIDE = "strategy.override_request"
    EMERGENCY_STOP = "emergency.stop_request"
    EMERGENCY_ROLLBACK = "emergency.rollback_request"


class FunnelCreateRequest(BaseModel):
    funnel_id: str = Field(..., description="Funnel ID")
    niche: str = Field(..., description="Target niche")
    strategy: str = Field(..., description="Funnel strategy")
    target_audience: str = Field(..., description="Target audience")
    channels: List[str] = Field(default_factory=list, description="Marketing channels")
    estimated_budget: float = Field(default=0.0, description="Estimated budget")
    requester: str = Field(..., description="Requesting engine/service")
    context: Dict[str, Any] = Field(default_factory=dict, description="Additional context")


class FunnelLaunchRequest(BaseModel):
    funnel_id: str = Field(..., description="Funnel ID")
    launch_config: Dict[str, Any] = Field(default_factory=dict, description="Launch configuration")
    channels: List[str] = Field(default_factory=list, description="Active channels")
    requester: str = Field(..., description="Requesting engine/service")
    context: Dict[str, Any] = Field(default_factory=dict, description="Additional context")


class FunnelMutationRequest(BaseModel):
    funnel_id: str = Field(..., description="Funnel ID")
    mutation_type: str = Field(..., description="Type of mutation")
    mutation_config: Dict[str, Any] = Field(default_factory=dict, description="Mutation configuration")
    source_funnel_id: Optional[str] = Field(None, description="Source funnel if replicating")
    requester: str = Field(..., description="Requesting engine/service")
    context: Dict[str, Any] = Field(default_factory=dict, description="Additional context")


class FunnelArchiveRequest(BaseModel):
    funnel_id: str = Field(..., description="Funnel ID")
    reason: str = Field(..., description="Reason for archiving")
    requester: str = Field(..., description="Requesting engine/service")
    context: Dict[str, Any] = Field(default_factory=dict, description="Additional context")


class ProductCreateRequest(BaseModel):
    product_id: str = Field(..., description="Product ID")
    name: str = Field(..., description="Product name")
    category: str = Field(..., description="Product category")
    price: float = Field(..., description="Product price")
    description: str = Field(default="", description="Product description")
    requester: str = Field(..., description="Requesting engine/service")
    context: Dict[str, Any] = Field(default_factory=dict, description="Additional context")


class ProductPublishRequest(BaseModel):
    product_id: str = Field(..., description="Product ID")
    platform: str = Field(..., description="Publishing platform")
    publish_config: Dict[str, Any] = Field(default_factory=dict, description="Publish configuration")
    requester: str = Field(..., description="Requesting engine/service")
    context: Dict[str, Any] = Field(default_factory=dict, description="Additional context")


class ProductUpdateRequest(BaseModel):
    product_id: str = Field(..., description="Product ID")
    updates: Dict[str, Any] = Field(..., description="Product updates")
    requester: str = Field(..., description="Requesting engine/service")
    context: Dict[str, Any] = Field(default_factory=dict, description="Additional context")


class ResourceComputeRequest(BaseModel):
    resource_type: str = Field(..., description="Type of compute resource")
    quantity: int = Field(..., description="Quantity requested")
    duration: int = Field(..., description="Duration in seconds")
    priority: str = Field(default="normal", description="Request priority")
    requester: str = Field(..., description="Requesting engine/service")
    context: Dict[str, Any] = Field(default_factory=dict, description="Additional context")


class ResourceAPIRequest(BaseModel):
    api_endpoint: str = Field(..., description="API endpoint")
    method: str = Field(default="GET", description="HTTP method")
    rate_limit: Optional[int] = Field(None, description="Required rate limit")
    requester: str = Field(..., description="Requesting engine/service")
    context: Dict[str, Any] = Field(default_factory=dict, description="Additional context")


class ResourceBudgetRequest(BaseModel):
    budget_type: str = Field(..., description="Type of budget (compute, api, marketing)")
    amount: float = Field(..., description="Budget amount")
    period: str = Field(..., description="Budget period (daily, weekly, monthly)")
    justification: str = Field(..., description="Budget justification")
    requester: str = Field(..., description="Requesting engine/service")
    context: Dict[str, Any] = Field(default_factory=dict, description="Additional context")


class RiskAssessmentRequest(BaseModel):
    risk_type: str = Field(..., description="Type of risk")
    severity: str = Field(..., description="Risk severity (low, medium, high, critical)")
    description: str = Field(..., description="Risk description")
    mitigation: str = Field(..., description="Proposed mitigation")
    requester: str = Field(..., description="Requesting engine/service")
    context: Dict[str, Any] = Field(default_factory=dict, description="Additional context")


class RiskOverrideRequest(BaseModel):
    risk_id: str = Field(..., description="Risk ID to override")
    override_reason: str = Field(..., description="Reason for override")
    duration: Optional[int] = Field(None, description="Override duration in seconds")
    requester: str = Field(..., description="Requesting engine/service")
    context: Dict[str, Any] = Field(default_factory=dict, description="Additional context")


class StrategyAlignmentRequest(BaseModel):
    strategy_id: str = Field(..., description="Strategy ID")
    action_type: str = Field(..., description="Action type")
    alignment_check: bool = Field(default=True, description="Whether to check alignment")
    requester: str = Field(..., description="Requesting engine/service")
    context: Dict[str, Any] = Field(default_factory=dict, description="Additional context")


class StrategyOverrideRequest(BaseModel):
    strategy_id: str = Field(..., description="Strategy ID to override")
    override_reason: str = Field(..., description="Reason for override")
    new_parameters: Dict[str, Any] = Field(default_factory=dict, description="New strategy parameters")
    requester: str = Field(..., description="Requesting engine/service")
    context: Dict[str, Any] = Field(default_factory=dict, description="Additional context")


class EmergencyStopRequest(BaseModel):
    entity_type: str = Field(..., description="Type of entity to stop")
    entity_id: str = Field(..., description="Entity ID")
    reason: str = Field(..., description="Reason for emergency stop")
    severity: str = Field(default="critical", description="Severity level")
    requester: str = Field(..., description="Requesting engine/service")
    context: Dict[str, Any] = Field(default_factory=dict, description="Additional context")


class EmergencyRollbackRequest(BaseModel):
    entity_type: str = Field(..., description="Type of entity to rollback")
    entity_id: str = Field(..., description="Entity ID")
    rollback_point: str = Field(..., description="Rollback point (snapshot, version, etc.)")
    reason: str = Field(..., description="Reason for rollback")
    requester: str = Field(..., description="Requesting engine/service")
    context: Dict[str, Any] = Field(default_factory=dict, description="Additional context")
