"""
Visual Asset Generator - Asset Library
CRUD operations for generated assets with JSON file storage.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Optional

from config import LIBRARY_DB_PATH
from models import Asset, AssetStatus, AssetType


class AssetLibrary:
    """Manages a library of generated visual assets with JSON persistence."""

    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or LIBRARY_DB_PATH
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._assets: dict[str, dict] = {}
        self._load()

    def _load(self) -> None:
        """Load assets from JSON file."""
        if self.db_path.exists():
            try:
                data = json.loads(self.db_path.read_text())
                self._assets = data.get("assets", {})
            except (json.JSONDecodeError, KeyError):
                self._assets = {}
        else:
            self._assets = {}

    def _save(self) -> None:
        """Persist assets to JSON file."""
        data = {
            "version": "1.0",
            "updated_at": datetime.now().isoformat(),
            "count": len(self._assets),
            "assets": self._assets,
        }
        self.db_path.write_text(json.dumps(data, indent=2, default=str))

    def add(self, asset: Asset) -> str:
        """Add an asset to the library.

        Args:
            asset: Asset model to store.

        Returns:
            The asset ID.
        """
        asset_dict = asset.model_dump(mode="json")
        asset_dict["created_at"] = asset.created_at.isoformat()
        self._assets[asset.id] = asset_dict
        self._save()
        return asset.id

    def get(self, asset_id: str) -> Optional[Asset]:
        """Get an asset by ID.

        Args:
            asset_id: Unique asset identifier.

        Returns:
            Asset model or None if not found.
        """
        data = self._assets.get(asset_id)
        if data is None:
            return None
        return Asset(**data)

    def update(self, asset_id: str, **kwargs) -> Optional[Asset]:
        """Update asset fields.

        Args:
            asset_id: Asset to update.
            **kwargs: Fields to update (status, tags, etc.).

        Returns:
            Updated Asset or None if not found.
        """
        if asset_id not in self._assets:
            return None

        for key, value in kwargs.items():
            if key in self._assets[asset_id]:
                if isinstance(value, (AssetStatus, AssetType)):
                    self._assets[asset_id][key] = value.value
                else:
                    self._assets[asset_id][key] = value

        self._save()
        return Asset(**self._assets[asset_id])

    def delete(self, asset_id: str) -> bool:
        """Remove an asset from the library.

        Args:
            asset_id: Asset to delete.

        Returns:
            True if deleted, False if not found.
        """
        if asset_id not in self._assets:
            return False

        # Optionally delete the file
        asset_data = self._assets[asset_id]
        file_path = asset_data.get("file_path")
        if file_path:
            path = Path(file_path)
            if path.exists():
                path.unlink()

        del self._assets[asset_id]
        self._save()
        return True

    def list_all(self) -> list[Asset]:
        """List all assets in the library.

        Returns:
            List of all Asset models.
        """
        return [Asset(**data) for data in self._assets.values()]

    def search(
        self,
        company: Optional[str] = None,
        asset_type: Optional[AssetType] = None,
        platform: Optional[str] = None,
        status: Optional[AssetStatus] = None,
        tags: Optional[list[str]] = None,
        query: Optional[str] = None,
    ) -> list[Asset]:
        """Search assets by various criteria.

        Args:
            company: Filter by company key.
            asset_type: Filter by asset type.
            platform: Filter by platform key.
            status: Filter by status.
            tags: Filter by tags (any match).
            query: Text search in title and tags.

        Returns:
            List of matching Asset models.
        """
        results = []

        for data in self._assets.values():
            # Company filter
            if company and data.get("company") != company:
                continue

            # Type filter
            if asset_type and data.get("type") != asset_type.value:
                continue

            # Platform filter
            if platform and data.get("platform") != platform:
                continue

            # Status filter
            if status and data.get("status") != status.value:
                continue

            # Tags filter (any match)
            if tags:
                asset_tags = set(data.get("tags", []))
                if not asset_tags.intersection(set(tags)):
                    continue

            # Text search
            if query:
                query_lower = query.lower()
                title = data.get("title", "").lower()
                asset_tags_str = " ".join(data.get("tags", [])).lower()
                if query_lower not in title and query_lower not in asset_tags_str:
                    continue

            results.append(Asset(**data))

        return results

    def by_company(self, company_key: str) -> list[Asset]:
        """Get all assets for a specific company.

        Args:
            company_key: Company identifier.

        Returns:
            List of matching assets.
        """
        return self.search(company=company_key)

    def by_type(self, asset_type: AssetType) -> list[Asset]:
        """Get all assets of a specific type.

        Args:
            asset_type: Asset type enum value.

        Returns:
            List of matching assets.
        """
        return self.search(asset_type=asset_type)

    def by_platform(self, platform_key: str) -> list[Asset]:
        """Get all assets for a specific platform.

        Args:
            platform_key: Platform identifier.

        Returns:
            List of matching assets.
        """
        return self.search(platform=platform_key)

    def approve(self, asset_id: str) -> Optional[Asset]:
        """Mark an asset as approved.

        Args:
            asset_id: Asset to approve.

        Returns:
            Updated Asset or None.
        """
        return self.update(asset_id, status=AssetStatus.APPROVED)

    def reject(self, asset_id: str) -> Optional[Asset]:
        """Mark an asset as rejected.

        Args:
            asset_id: Asset to reject.

        Returns:
            Updated Asset or None.
        """
        return self.update(asset_id, status=AssetStatus.REJECTED)

    def stats(self) -> dict[str, int | dict]:
        """Get library statistics.

        Returns:
            Dict with counts by company, type, status, and total.
        """
        total = len(self._assets)
        by_company: dict[str, int] = {}
        by_type: dict[str, int] = {}
        by_status: dict[str, int] = {}
        total_size_bytes = 0

        for data in self._assets.values():
            company = data.get("company", "unknown")
            by_company[company] = by_company.get(company, 0) + 1

            atype = data.get("type", "unknown")
            by_type[atype] = by_type.get(atype, 0) + 1

            status = data.get("status", "unknown")
            by_status[status] = by_status.get(status, 0) + 1

            total_size_bytes += data.get("file_size_bytes", 0) or 0

        return {
            "total": total,
            "total_size_mb": round(total_size_bytes / (1024 * 1024), 2),
            "by_company": by_company,
            "by_type": by_type,
            "by_status": by_status,
        }

    @property
    def count(self) -> int:
        """Total number of assets in the library."""
        return len(self._assets)
