from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List, Callable
from datetime import datetime
from enum import Enum


class RuleCategory(str, Enum):
    """Rule categories."""
    SAFETY = "safety"
    BRAND = "brand"
    COMPLIANCE = "compliance"
    RESOURCE = "resource"
    STRATEGY = "strategy"
    RISK = "risk"
    MARKET = "market"
    TEMPORAL = "temporal"
    CAUSAL = "causal"


class RuleSeverity(str, Enum):
    """Rule severity levels."""
    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class RuleAction(str, Enum):
    """Actions to take when rule is triggered."""
    ALLOW = "allow"
    WARN = "warn"
    BLOCK = "block"
    REQUIRE_APPROVAL = "require_approval"
    CONDITIONAL = "conditional"


class Rule(BaseModel):
    """Governance rule definition."""
    rule_id: str = Field(..., description="Unique rule ID")
    name: str = Field(..., description="Rule name")
    category: RuleCategory = Field(..., description="Rule category")
    description: str = Field(..., description="Rule description")
    severity: RuleSeverity = Field(default=RuleSeverity.MEDIUM, description="Rule severity")
    action: RuleAction = Field(default=RuleAction.WARN, description="Action to take")
    enabled: bool = Field(default=True, description="Whether the rule is enabled")
    conditions: Dict[str, Any] = Field(default_factory=dict, description="Rule conditions")
    applies_to: List[str] = Field(default_factory=list, description="Request types this applies to")
    version: str = Field(default="1.0.0", description="Rule version")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Rule creation time")
    updated_at: Optional[datetime] = Field(None, description="Rule update time")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class RuleEvaluationResult(BaseModel):
    """Result of rule evaluation."""
    rule_id: str = Field(..., description="Rule ID that was evaluated")
    rule_name: str = Field(..., description="Rule name")
    category: RuleCategory = Field(..., description="Rule category")
    triggered: bool = Field(..., description="Whether the rule was triggered")
    action: RuleAction = Field(..., description="Action taken")
    message: str = Field(..., description="Evaluation message")
    details: Dict[str, Any] = Field(default_factory=dict, description="Evaluation details")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Evaluation confidence")
