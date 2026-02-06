"""
Settings Router — System settings, OAuth token status, and company details.
"""

from fastapi import APIRouter, HTTPException
import json
from config import config
from typing import Optional
from pathlib import Path

router = APIRouter()


def load_json(path: Path):
    if path.exists():
        return json.loads(path.read_text())
    return []


def save_json(path: Path, data):
    path.write_text(json.dumps(data, indent=2, default=str))


# ── OAuth Token Status ───────────────────────────────────────────


@router.get("/tokens")
def get_token_status():
    """LinkedIn/Monday OAuth status per company."""
    tokens = load_json(config.TOKENS_FILE)

    if isinstance(tokens, list):
        # Convert list to dict keyed by company if needed
        token_map = {}
        for t in tokens:
            company = t.get("company", "unknown")
            token_map[company] = t
        tokens = token_map
    elif not isinstance(tokens, dict):
        tokens = {}

    return {
        "tokens": tokens,
        "total_companies": len(tokens),
    }


# ── Company Registry ─────────────────────────────────────────────


@router.get("/companies")
def list_companies():
    """Return all companies from config with their details."""
    companies = []
    for key, details in config.COMPANIES.items():
        company = {"key": key, **details}
        company["active"] = details.get("status") != "coming_soon"
        companies.append(company)

    return {
        "companies": companies,
        "total": len(companies),
        "active": sum(1 for c in companies if c["active"]),
    }


@router.get("/companies/{slug}")
def get_company(slug: str):
    """Single company details by slug."""
    for key, details in config.COMPANIES.items():
        if details.get("slug") == slug or key == slug:
            return {
                "key": key,
                **details,
                "active": details.get("status") != "coming_soon",
            }

    raise HTTPException(status_code=404, detail=f"Company '{slug}' not found")


# ── System Info ──────────────────────────────────────────────────


def _dir_size(path: Path) -> dict:
    """Get size info for a directory."""
    if not path.exists():
        return {"exists": False, "files": 0, "size_bytes": 0}

    files = list(path.glob("*"))
    total_bytes = sum(f.stat().st_size for f in files if f.is_file())

    return {
        "exists": True,
        "files": len([f for f in files if f.is_file()]),
        "size_bytes": total_bytes,
        "size_human": _human_size(total_bytes),
    }


def _human_size(num_bytes: int) -> str:
    """Convert bytes to human-readable string."""
    for unit in ["B", "KB", "MB", "GB"]:
        if abs(num_bytes) < 1024:
            return f"{num_bytes:.1f} {unit}"
        num_bytes /= 1024
    return f"{num_bytes:.1f} TB"


@router.get("/system")
def get_system_info():
    """System info: app name, version, demo_mode, data dir sizes."""
    return {
        "app_name": config.APP_NAME,
        "version": config.APP_VERSION,
        "demo_mode": config.DEMO_MODE,
        "debug": config.DEBUG,
        "data_dir": str(config.DATA_DIR),
        "data_dir_info": _dir_size(config.DATA_DIR),
        "host": config.HOST,
        "port": config.PORT,
        "companies_count": len(config.COMPANIES),
        "active_companies_count": len(config.ACTIVE_COMPANIES),
    }
