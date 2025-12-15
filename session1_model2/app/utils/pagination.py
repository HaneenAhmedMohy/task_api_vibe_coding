"""Pagination utilities for API responses."""

from typing import Dict, Any, Optional
from math import ceil


class PaginationParams:
    """Pagination parameters for API requests."""

    def __init__(
        self,
        skip: int = 0,
        limit: int = 100,
        max_limit: int = 1000
    ):
        self.skip = max(0, skip)
        self.limit = min(max(1, limit), max_limit)

    @property
    def offset(self) -> int:
        """Get database offset value."""
        return self.skip

    @property
    def page_size(self) -> int:
        """Get page size."""
        return self.limit

    def get_pagination_info(self, total: int, base_url: str) -> Dict[str, Any]:
        """
        Generate pagination metadata.

        Args:
            total: Total number of items
            base_url: Base URL for generating links

        Returns:
            Dictionary with pagination information
        """
        current_page = (self.skip // self.limit) + 1 if self.limit > 0 else 1
        total_pages = ceil(total / self.limit) if self.limit > 0 else 1

        return {
            "total_items": total,
            "total_pages": total_pages,
            "current_page": current_page,
            "page_size": self.limit,
            "has_next": current_page < total_pages,
            "has_previous": current_page > 1,
            "items_on_page": min(self.limit, max(0, total - self.skip))
        }


class PaginatedResponse:
    """Helper for creating paginated responses."""

    @staticmethod
    def create(
        items: list,
        total: int,
        pagination: PaginationParams
    ) -> Dict[str, Any]:
        """
        Create a paginated response.

        Args:
            items: List of items for current page
            total: Total number of items
            pagination: Pagination parameters

        Returns:
            Paginated response dictionary
        """
        pagination_info = pagination.get_pagination_info(total, "")

        return {
            "items": items,
            "pagination": pagination_info
        }