"""
Website Builder — API Router
Chat interface, file uploads, preview/deploy pipeline.
"""

import re
import time
from typing import Optional

from fastapi import APIRouter, HTTPException, Request, UploadFile, File, Form
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from modules import llm_client, session_store, site_context, file_manager, github_client, code_generator

router = APIRouter(prefix="/api/builder", tags=["Website Builder"])


# ── Request Models ────────────────────────────────────────────

class ChatRequest(BaseModel):
    session_id: Optional[str] = None
    message: str
    site_slug: str


class PreviewRequest(BaseModel):
    session_id: str


class DeployRequest(BaseModel):
    session_id: str
    branch_name: str


class DiscardRequest(BaseModel):
    session_id: str
    branch_name: str


class RollbackRequest(BaseModel):
    site_slug: str
    commit_sha: str


# ── Helpers ───────────────────────────────────────────────────

def _check_ownership(request: Request, session: dict):
    """Verify the requesting user owns the session."""
    user = getattr(request.state, "user", {}).get("username", "anonymous")
    if session.get("user") and session["user"] != user:
        raise HTTPException(status_code=403, detail="Access denied")


# ── Chat ──────────────────────────────────────────────────────

@router.post("/chat")
async def chat(request: Request, body: ChatRequest):
    """Send a message to the AI website builder."""
    user = getattr(request.state, "user", {}).get("username", "anonymous")

    # Get or create session
    if body.session_id:
        session = session_store.get_session(body.session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        _check_ownership(request, session)
    else:
        session = session_store.create_session(user, body.site_slug)

    # Get site context
    ctx = site_context.get_site_context(body.site_slug)
    if not ctx:
        raise HTTPException(status_code=404, detail=f"Site '{body.site_slug}' not found")

    # Add user message to session
    session_store.add_message(session["id"], "user", body.message)

    # Call LLM
    result = await llm_client.chat(
        message=body.message,
        session_messages=session.get("messages", []),
        site_context=ctx,
        session_id=session["id"],
    )

    # Add assistant response to session
    session_store.add_message(session["id"], "assistant", result["response"])

    # If plan was extracted, store it
    if result.get("plan"):
        session_store.set_proposed_changes(session["id"], result["plan"])

    return {
        "session_id": session["id"],
        "response": result["response"],
        "plan": result.get("plan"),
        "usage": result.get("usage"),
    }


# ── File Upload ───────────────────────────────────────────────

@router.post("/upload")
async def upload_file(
    request: Request,
    file: UploadFile = File(...),
    session_id: str = Form(...),
):
    """Upload a file (image) for use in website changes."""
    # Verify session ownership
    session = session_store.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    _check_ownership(request, session)

    content = await file.read()

    # Validate
    error = file_manager.validate_file(file.filename, len(content), session_id)
    if error:
        raise HTTPException(status_code=400, detail=error)

    # Save
    file_info = await file_manager.save_file(session_id, file.filename, content)

    # Add to session
    session_store.add_file(session_id, file_info)

    return file_info


# ── Sessions ──────────────────────────────────────────────────

@router.get("/sessions")
async def list_sessions(request: Request):
    """List chat sessions for the current user."""
    user = getattr(request.state, "user", {}).get("username", "anonymous")
    return session_store.list_sessions(user)


@router.get("/sessions/{session_id}")
async def get_session(request: Request, session_id: str):
    """Get a specific session with full message history."""
    session = session_store.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    _check_ownership(request, session)
    return session


# ── Sites ─────────────────────────────────────────────────────

@router.get("/sites")
async def list_sites():
    """List available websites that can be edited."""
    return site_context.get_available_sites()


# ── Preview & Deploy ──────────────────────────────────────────

@router.post("/preview")
async def create_preview(request: Request, body: PreviewRequest):
    """Create a preview branch with proposed changes."""
    session = session_store.get_session(body.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    _check_ownership(request, session)

    plan = session.get("proposed_changes")
    if not plan:
        raise HTTPException(status_code=400, detail="No changes to preview. Chat with the AI first.")

    site_slug = session["site_slug"]
    site_info = site_context.SITE_REGISTRY.get(site_slug)
    if not site_info:
        raise HTTPException(status_code=404, detail="Site not found")

    repo_parts = site_info["repo"].split("/")
    owner, repo = repo_parts[0], repo_parts[1]

    # Read current site HTML from GitHub
    site_html = {}
    for change in plan:
        file_path = change.get("file", "")
        if not file_path.startswith("public/"):
            file_path = f"public/{file_path}"
        try:
            result = await github_client.get_file(owner, repo, file_path)
            if result:
                site_html[file_path] = result["content"]
        except Exception:
            pass

    # Apply plan
    changes = code_generator.apply_plan(plan, site_html)
    errors = [c for c in changes if c["action"] == "error"]
    if errors:
        return {"status": "error", "errors": [e["description"] for e in errors]}

    valid_changes = [c for c in changes if c["action"] != "error" and c["content"]]
    if not valid_changes:
        raise HTTPException(status_code=400, detail="No valid changes to apply")

    # Create branch
    branch_name = f"preview/update-{int(time.time())}"
    await github_client.create_branch(owner, repo, branch_name)

    # Push changes
    files_to_push = [{"path": c["path"], "content": c["content"]} for c in valid_changes]
    await github_client.push_files(owner, repo, branch_name, files_to_push, "Website Builder: preview changes")

    return {
        "status": "ready",
        "branch_name": branch_name,
        "files_changed": len(valid_changes),
        "changes": [{"path": c["path"], "action": c["action"], "description": c["description"]} for c in valid_changes],
    }


@router.post("/deploy")
async def deploy_changes(request: Request, body: DeployRequest):
    """Merge preview branch to main (triggers auto-deploy on Render)."""
    # Validate branch name format
    if not re.match(r'^preview/update-\d+$', body.branch_name):
        raise HTTPException(status_code=400, detail="Invalid branch name format")

    session = session_store.get_session(body.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    _check_ownership(request, session)

    site_slug = session["site_slug"]
    site_info = site_context.SITE_REGISTRY.get(site_slug)
    if not site_info:
        raise HTTPException(status_code=404, detail="Site not found")

    repo_parts = site_info["repo"].split("/")
    owner, repo = repo_parts[0], repo_parts[1]

    result = await github_client.merge_branch(
        owner, repo, body.branch_name,
        message="Website Builder: deploy approved changes"
    )

    # Clear proposed changes
    session_store.clear_proposed_changes(body.session_id)

    return {
        "status": "deployed",
        "commit_sha": result["commit_sha"],
        "message": "Changes deployed! Render will auto-deploy in ~30 seconds.",
    }


@router.post("/discard")
async def discard_preview(request: Request, body: DiscardRequest):
    """Discard preview branch without merging."""
    # Validate branch name format
    if not re.match(r'^preview/update-\d+$', body.branch_name):
        raise HTTPException(status_code=400, detail="Invalid branch name format")

    session = session_store.get_session(body.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    _check_ownership(request, session)

    site_slug = session["site_slug"]
    site_info = site_context.SITE_REGISTRY.get(site_slug)
    if not site_info:
        raise HTTPException(status_code=404, detail="Site not found")

    repo_parts = site_info["repo"].split("/")
    owner, repo = repo_parts[0], repo_parts[1]

    await github_client.delete_branch(owner, repo, body.branch_name)
    session_store.clear_proposed_changes(body.session_id)

    return {"status": "discarded", "message": "Preview discarded. No changes were made."}


@router.post("/rollback")
async def rollback(request: Request, body: RollbackRequest):
    """Rollback to a previous commit."""
    # Validate commit SHA format
    if not re.match(r'^[0-9a-f]{7,40}$', body.commit_sha):
        raise HTTPException(status_code=400, detail="Invalid commit SHA format")

    site_info = site_context.SITE_REGISTRY.get(body.site_slug)
    if not site_info:
        raise HTTPException(status_code=404, detail="Site not found")

    repo_parts = site_info["repo"].split("/")
    owner, repo = repo_parts[0], repo_parts[1]

    result = await github_client.revert_commit(owner, repo, body.commit_sha)

    return {
        "status": "rolled_back",
        "revert_sha": result["revert_sha"],
        "message": "Rollback complete. Render will auto-deploy the reverted version.",
    }


@router.get("/deploys")
async def list_deploys(site_slug: str):
    """List recent deploys (from GitHub commits)."""
    site_info = site_context.SITE_REGISTRY.get(site_slug)
    if not site_info:
        raise HTTPException(status_code=404, detail="Site not found")

    repo_parts = site_info["repo"].split("/")
    owner, repo = repo_parts[0], repo_parts[1]

    try:
        commits = await github_client.list_commits(owner, repo, limit=10)
        return commits
    except Exception as e:
        return []


@router.get("/usage")
async def get_usage():
    """Get current API usage statistics."""
    return llm_client.get_usage_stats()
