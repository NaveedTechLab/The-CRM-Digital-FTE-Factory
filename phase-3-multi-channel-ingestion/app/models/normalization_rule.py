from datetime import datetime
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field, validator
import uuid


class NormalizationRule(BaseModel):
    """Model for normalization transformation rules"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    channel_type: str = Field(..., pattern=r"^(gmail|whatsapp|webform)$", description="Type of channel this rule applies to")
    rule_name: str = Field(..., description="Descriptive name for the rule")
    input_field: str = Field(..., description="The field in the raw payload to transform")
    output_field: str = Field(..., description="The field in the InboundMessage to populate")
    transformation_type: str = Field(..., pattern=r"^(direct|mapping|regex|function)$", description="Type of transformation to apply")
    transformation_params: Dict[str, Any] = Field(default={}, description="Parameters for the transformation")
    priority: int = Field(default=0, ge=0, description="Order in which rules are applied")
    enabled: bool = Field(default=True, description="Whether the rule is currently active")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    @validator('channel_type')
    def validate_channel_type(cls, v):
        """Validate that channel_type is one of the allowed values"""
        if v not in ['gmail', 'whatsapp', 'webform']:
            raise ValueError('Channel type must be one of: gmail, whatsapp, webform')
        return v

    @validator('transformation_type')
    def validate_transformation_type(cls, v):
        """Validate that transformation_type is one of the allowed values"""
        if v not in ['direct', 'mapping', 'regex', 'function']:
            raise ValueError('Transformation type must be one of: direct, mapping, regex, function')
        return v

    @validator('rule_name', 'input_field', 'output_field')
    def validate_not_empty(cls, v):
        """Validate that required fields are not empty"""
        if not v or not v.strip():
            raise ValueError('Field cannot be empty')
        return v

    @validator('priority')
    def validate_priority(cls, v):
        """Validate that priority is non-negative"""
        if v < 0:
            raise ValueError('Priority must be non-negative')
        return v

    @validator('enabled')
    def validate_enabled(cls, v):
        """Validate that enabled is a boolean"""
        if not isinstance(v, bool):
            raise ValueError('Enabled must be a boolean')
        return v

    def __init__(self, **data):
        super().__init__(**data)
        self.updated_at = datetime.utcnow()