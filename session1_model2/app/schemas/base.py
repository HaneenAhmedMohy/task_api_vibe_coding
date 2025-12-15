"""Base validators and utilities for schemas."""

from typing import Any, Dict, List, Optional
from pydantic import field_validator, ConfigDict


def create_enum_validator(enum_class, field_name: str):
    """Factory function to create enum validators."""

    @field_validator(field_name)
    @classmethod
    def validate_value(cls, v: Any) -> Any:
        """Validate enum value."""
        if v is not None:
            if not enum_class.is_valid(v):
                allowed_values = enum_class.values()
                raise ValueError(
                    f"{field_name} must be one of: {', '.join(allowed_values)}. "
                    f"Got: {v}"
                )
        return v

    return validate_value


class ResponseModelMixin:
    """Common response model configurations."""

    model_config = ConfigDict(
        from_attributes=True,
        # Additional configurations can be added here
    )