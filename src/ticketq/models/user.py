"""Generic user model with adapter-specific extensions support."""

import json
from typing import Any

from ..core.interfaces.models import BaseUserModel


class User(BaseUserModel):
    """Generic user model that can be extended by adapters.

    This model provides common user fields while allowing adapters
    to store additional data in the adapter_specific_data field.
    """

    def __init__(
        self,
        id: str,
        name: str,
        email: str,
        group_ids: list[str] | None = None,
        adapter_name: str = "",
        adapter_specific_data: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> None:
        """Initialize a generic user.

        Args:
            id: Unique user identifier
            name: User display name
            email: User email address
            group_ids: List of group IDs user belongs to
            adapter_name: Name of the adapter that created this user
            adapter_specific_data: Additional adapter-specific data
            **kwargs: Additional fields stored in adapter_specific_data
        """
        self._id = str(id)
        self._name = name
        self._email = email
        self._group_ids = group_ids or []
        self._adapter_name = adapter_name

        # Combine explicit adapter_specific_data with kwargs
        self._adapter_specific_data = adapter_specific_data or {}
        self._adapter_specific_data.update(kwargs)

    @property
    def id(self) -> str:
        """Unique user identifier."""
        return self._id

    @property
    def name(self) -> str:
        """User display name."""
        return self._name

    @property
    def email(self) -> str:
        """User email address."""
        return self._email

    @property
    def group_ids(self) -> list[str]:
        """List of group IDs user belongs to."""
        return self._group_ids.copy()

    @property
    def adapter_name(self) -> str:
        """Name of the adapter that created this user."""
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

    def add_group(self, group_id: str) -> None:
        """Add user to a group.

        Args:
            group_id: Group ID to add
        """
        if group_id not in self._group_ids:
            self._group_ids.append(group_id)

    def remove_group(self, group_id: str) -> None:
        """Remove user from a group.

        Args:
            group_id: Group ID to remove
        """
        if group_id in self._group_ids:
            self._group_ids.remove(group_id)

    def is_in_group(self, group_id: str) -> bool:
        """Check if user is in a specific group.

        Args:
            group_id: Group ID to check

        Returns:
            True if user is in group, False otherwise
        """
        return group_id in self._group_ids

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        data = {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "group_ids": self.group_ids,
            "adapter_name": self.adapter_name,
            "adapter_specific_data": self.adapter_specific_data,
        }
        return data

    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=2)

    def __str__(self) -> str:
        """String representation."""
        return f"User(id={self.id}, name='{self.name}', email='{self.email}')"

    def __repr__(self) -> str:
        """Developer representation."""
        return (
            f"User(id={self.id}, name='{self.name}', email='{self.email}', "
            f"groups={len(self.group_ids)}, adapter='{self.adapter_name}')"
        )

    def __eq__(self, other: object) -> bool:
        """Check equality based on ID and adapter."""
        if not isinstance(other, User):
            return False
        return self.id == other.id and self.adapter_name == other.adapter_name

    def __hash__(self) -> int:
        """Hash based on ID and adapter."""
        return hash((self.id, self.adapter_name))
