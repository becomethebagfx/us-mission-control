"""
GBP Automation Module - Location Manager
Multi-location sync, NAP verification, and batch operations
for all five companies.
"""

import re
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from config import ACTIVE_COMPANIES, COMPANIES, CompanyInfo, get_company
from models import Location


# ---------------------------------------------------------------------------
# NAP Verification (Name / Address / Phone)
# ---------------------------------------------------------------------------


@dataclass
class NAPResult:
    """Result of a Name-Address-Phone consistency check."""

    company_key: str
    field: str
    expected: str
    actual: str
    matches: bool
    message: str


def normalize_phone(phone: str) -> str:
    """Strip a phone number to digits only for comparison."""
    return re.sub(r"[^\d]", "", phone)


def normalize_address(address: str) -> str:
    """Lowercase, strip punctuation, collapse whitespace, abbreviate words."""
    addr = address.lower()
    addr = re.sub(r"[.,#]", "", addr)
    addr = re.sub(r"\s+", " ", addr).strip()
    # Common abbreviation normalization using word boundaries
    replacements = {
        r"\bsuite\b": "ste",
        r"\bboulevard\b": "blvd",
        r"\bavenue\b": "ave",
        r"\bstreet\b": "st",
        r"\bdrive\b": "dr",
        r"\blane\b": "ln",
        r"\broad\b": "rd",
        r"\bplace\b": "pl",
    }
    for pattern, abbr in replacements.items():
        addr = re.sub(pattern, abbr, addr)
    return addr


def verify_nap(location: Location, company: CompanyInfo) -> List[NAPResult]:
    """Compare a GBP location's NAP data against the company registry.

    Returns a list of ``NAPResult`` items -- one per field checked.
    """
    results: List[NAPResult] = []

    # Name
    name_match = location.title.strip().lower() == company.name.strip().lower()
    results.append(
        NAPResult(
            company_key=location.company_key,
            field="name",
            expected=company.name,
            actual=location.title,
            matches=name_match,
            message="OK" if name_match else (
                f"Name mismatch: GBP has '{location.title}', "
                f"registry has '{company.name}'"
            ),
        )
    )

    # Phone
    expected_phone = normalize_phone(company.phone)
    actual_phone = normalize_phone(location.phone_number)
    phone_match = expected_phone == actual_phone
    results.append(
        NAPResult(
            company_key=location.company_key,
            field="phone",
            expected=company.phone,
            actual=location.phone_number,
            matches=phone_match,
            message="OK" if phone_match else (
                f"Phone mismatch: GBP has '{location.phone_number}', "
                f"registry has '{company.phone}'"
            ),
        )
    )

    # Address (compare first line against the part before the first comma)
    registry_first_line = company.address.split(",")[0].strip()
    gbp_first_line = (
        location.address_lines[0].strip() if location.address_lines else ""
    )
    addr_match = (
        normalize_address(gbp_first_line) == normalize_address(registry_first_line)
    )
    results.append(
        NAPResult(
            company_key=location.company_key,
            field="address",
            expected=registry_first_line,
            actual=gbp_first_line,
            matches=addr_match,
            message="OK" if addr_match else (
                f"Address mismatch: GBP has '{gbp_first_line}', "
                f"registry has '{registry_first_line}'"
            ),
        )
    )

    return results


# ---------------------------------------------------------------------------
# Multi-Location Sync
# ---------------------------------------------------------------------------


class LocationManager:
    """Manage GBP locations across all registered companies.

    Args:
        client: A ``GBPClient`` instance.
        demo: If True, the client operates in demo mode.
    """

    def __init__(self, client, demo: bool = False) -> None:
        self.client = client
        self.demo = demo
        self._locations: List[Location] = []

    def sync_locations(self) -> List[Location]:
        """Fetch all locations from the API and cache them locally."""
        self._locations = self.client.list_locations()
        return self._locations

    @property
    def locations(self) -> List[Location]:
        if not self._locations:
            self.sync_locations()
        return self._locations

    def get_locations_for_company(
        self, company_key: str
    ) -> List[Location]:
        """Filter cached locations to a single company."""
        return [
            loc for loc in self.locations if loc.company_key == company_key
        ]

    def batch_get(
        self, location_names: List[str]
    ) -> List[Location]:
        """Fetch multiple locations by resource name."""
        return [
            self.client.get_location(name) for name in location_names
        ]

    # -- NAP ----------------------------------------------------------------

    def verify_all_nap(self) -> Dict[str, List[NAPResult]]:
        """Run NAP verification for every synced location.

        Returns a dict keyed by company_key with lists of ``NAPResult``.
        """
        results: Dict[str, List[NAPResult]] = {}
        for loc in self.locations:
            company = get_company(loc.company_key)
            if company is None:
                continue
            checks = verify_nap(loc, company)
            results.setdefault(loc.company_key, []).extend(checks)
        return results

    def nap_summary(self) -> Tuple[int, int, List[str]]:
        """Quick NAP health summary.

        Returns ``(total_checks, mismatches, messages)`` where ``messages``
        lists each mismatch description.
        """
        all_results = self.verify_all_nap()
        total = 0
        mismatches = 0
        messages: List[str] = []
        for company_key, checks in all_results.items():
            for check in checks:
                total += 1
                if not check.matches:
                    mismatches += 1
                    messages.append(f"[{company_key}] {check.message}")
        return total, mismatches, messages

    # -- Demo locations -----------------------------------------------------

    @staticmethod
    def demo_locations() -> List[Location]:
        """Generate demo locations for all active companies."""
        locations: List[Location] = []
        for i, (key, co) in enumerate(ACTIVE_COMPANIES.items(), start=1):
            addr_parts = co.address.split(",")
            locations.append(
                Location(
                    name=f"accounts/demo/locations/{1000 + i}",
                    store_code=co.slug,
                    title=co.name,
                    phone_number=co.phone,
                    address_lines=[addr_parts[0].strip()],
                    city="Dallas",
                    state="TX",
                    postal_code="75201",
                    website_url=f"https://www.{co.slug}.com",
                    primary_category="General Contractor",
                    labels=[f"company:{key}"],
                    company_key=key,
                )
            )
        return locations

    # -- Display helpers ----------------------------------------------------

    def print_status(self, company_filter: Optional[str] = None) -> str:
        """Return a formatted status string for all (or filtered) locations."""
        locs = self.locations
        if company_filter:
            locs = [l for l in locs if l.company_key == company_filter]

        lines: List[str] = []
        lines.append(f"{'='*60}")
        lines.append(f"  GBP Location Status  ({len(locs)} locations)")
        lines.append(f"{'='*60}")
        for loc in locs:
            company = get_company(loc.company_key)
            color = company.accent_color if company else "#000"
            lines.append(f"\n  {loc.title}  [{color}]")
            lines.append(f"    Resource : {loc.name}")
            lines.append(f"    Phone    : {loc.phone_number}")
            lines.append(f"    Address  : {loc.full_address}")
            if loc.website_url:
                lines.append(f"    Website  : {loc.website_url}")
            lines.append(f"    Category : {loc.primary_category or 'N/A'}")

        # NAP health
        total, mismatches, msgs = self.nap_summary()
        lines.append(f"\n{'='*60}")
        lines.append(
            f"  NAP Health: {total - mismatches}/{total} checks passed"
        )
        if msgs:
            for m in msgs:
                lines.append(f"    WARNING: {m}")
        else:
            lines.append("    All NAP data consistent.")
        lines.append(f"{'='*60}")
        return "\n".join(lines)
