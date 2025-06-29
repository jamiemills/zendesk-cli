"""Generic group model with adapter-specific extensions support."""

import json
from typing import Any

from ..core.interfaces.models import BaseGroupModel


class Group(BaseGroupModel):
    """Generic group/team model that can be extended by adapters.

    This model provides common group fields while allowing adapters
    to store additional data in the adapter_specific_data field.
    """

    def __init__(
        self,
        id: str,
        name: str,
        description: str | None = None,
        adapter_name: str = "",
        adapter_specific_data: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> None:
        """Initialize a generic group.

        Args:
            id: Unique group identifier
            name: Group display name
            description: Group description
            adapter_name: Name of the adapter that created this group
            adapter_specific_data: Additional adapter-specific data
            **kwargs: Additional fields stored in adapter_specific_data
        """
        self._id = str(id)
        self._name = name
        self._description = description
        self._adapter_name = adapter_name

        # Combine explicit adapter_specific_data with kwargs
        self._adapter_specific_data = adapter_specific_data or {}
        self._adapter_specific_data.update(kwargs)

    @property
    def id(self) -> str:
        """Unique group identifier."""
        return self._id

    @property
    def name(self) -> str:
        """Group display name."""
        return self._name

    @property
    def description(self) -> str | None:
        """Group description."""
        return self._description

    @property
    def adapter_name(self) -> str:
        """Name of the adapter that created this group."""
        return self._adapter_name

    @property
    def adapter_specific_data(self) -> dict[str, Any]:
        """Adapter-specific data that doesn't fit common model."""
        return self._adapter_specific_data.copy()

    def get_adapter_field(self, field_name: str, default: Any = None) -> Any:
        """Get a field from adapter-specific data.

        Args:
            field_name: Name of the field to retrieve
            default: Default value if field doesn't exist

        Returns:
            Field value or default
        """
        return self._adapter_specific_data.get(field_name, default)

    def set_adapter_field(self, field_name: str, value: Any) -> None:
        """Set a field in adapter-specific data.

        Args:
            field_name: Name of the field to set
            value: Value to set
        """
        self._adapter_specific_data[field_name] = value

    def has_adapter_field(self, field_name: str) -> bool:
        """Check if adapter-specific field exists.

        Args:
            field_name: Name of the field to check

        Returns:
            True if field exists, False otherwise
        """
        return field_name in self._adapter_specific_data

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        data = {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "adapter_name": self.adapter_name,
            "adapter_specific_data": self.adapter_specific_data,
        }
        return data

    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=2)

    def __str__(self) -> str:
        """String representation."""
        return f"Group(id={self.id}, name='{self.name}')"

    def __repr__(self) -> str:
        """Developer representation."""
        return (
            f"Group(id={self.id}, name='{self.name}', "
            f"description='{self.description}', adapter='{self.adapter_name}')"
        )

    def __eq__(self, other: object) -> bool:
        """Check equality based on ID and adapter."""
        if not isinstance(other, Group):
            return False
        return self.id == other.id and self.adapter_name == other.adapter_name

    def __hash__(self) -> int:
        """Hash based on ID and adapter."""
        return hash((self.id, self.adapter_name))
