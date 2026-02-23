"""
Website Builder — GitHub Client
Handles branch creation, file pushing, merging, and rollback via GitHub API.
"""

import base64
import os
from typing import Optional

import httpx

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")
API_BASE = "https://api.github.com"


def _headers() -> dict:
    return {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }


def _check_token():
    if not GITHUB_TOKEN:
        raise RuntimeError("GITHUB_TOKEN not configured. Set it in environment variables.")


async def get_file(owner: str, repo: str, path: str, ref: str = "main") -> Optional[dict]:
    """Read a file from a GitHub repo. Returns {content, sha, path} or None."""
    _check_token()
    url = f"{API_BASE}/repos/{owner}/{repo}/contents/{path}"
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.get(url, headers=_headers(), params={"ref": ref})

    if resp.status_code == 404:
        return None
    resp.raise_for_status()

    data = resp.json()
    content = base64.b64decode(data["content"]).decode("utf-8")
    return {"content": content, "sha": data["sha"], "path": data["path"]}


async def create_branch(owner: str, repo: str, branch_name: str, from_branch: str = "main") -> dict:
    """Create a new branch from an existing branch."""
    _check_token()

    # Get the SHA of the source branch
    async with httpx.AsyncClient(timeout=30.0) as client:
        ref_resp = await client.get(
            f"{API_BASE}/repos/{owner}/{repo}/git/refs/heads/{from_branch}",
            headers=_headers(),
        )
    ref_resp.raise_for_status()
    sha = ref_resp.json()["object"]["sha"]

    # Create new branch
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(
            f"{API_BASE}/repos/{owner}/{repo}/git/refs",
            headers=_headers(),
            json={"ref": f"refs/heads/{branch_name}", "sha": sha},
        )
    resp.raise_for_status()
    return {"branch": branch_name, "sha": sha}


async def push_files(
    owner: str, repo: str, branch: str, files: list, message: str
) -> dict:
    """Push multiple file changes to a branch.

    files: list of {"path": str, "content": str}
    """
    _check_token()

    for file_info in files:
        path = file_info["path"]
        content = file_info["content"]
        encoded = base64.b64encode(content.encode("utf-8")).decode("utf-8")

        # Check if file exists to get its SHA
        existing = await get_file(owner, repo, path, ref=branch)
        payload = {
            "message": message,
            "content": encoded,
            "branch": branch,
        }
        if existing:
            payload["sha"] = existing["sha"]

        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.put(
                f"{API_BASE}/repos/{owner}/{repo}/contents/{path}",
                headers=_headers(),
                json=payload,
            )
        resp.raise_for_status()

    return {"files_pushed": len(files), "branch": branch}


async def merge_branch(owner: str, repo: str, branch: str, message: str = "") -> dict:
    """Merge a branch into main."""
    _check_token()
    if not message:
        message = f"Merge {branch} into main via Website Builder"

    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(
            f"{API_BASE}/repos/{owner}/{repo}/merges",
            headers=_headers(),
            json={"base": "main", "head": branch, "commit_message": message},
        )
    resp.raise_for_status()
    data = resp.json()

    # Delete branch after successful merge
    await delete_branch(owner, repo, branch)

    return {"commit_sha": data.get("sha", ""), "merged": True}


async def delete_branch(owner: str, repo: str, branch: str):
    """Delete a branch."""
    _check_token()
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.delete(
            f"{API_BASE}/repos/{owner}/{repo}/git/refs/heads/{branch}",
            headers=_headers(),
        )
    # 204 = success, 422 = already deleted
    if resp.status_code not in (204, 422):
        resp.raise_for_status()


async def revert_commit(owner: str, repo: str, sha: str) -> dict:
    """Revert a commit on main by creating a revert commit."""
    _check_token()

    # Get the commit to revert
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.get(
            f"{API_BASE}/repos/{owner}/{repo}/git/commits/{sha}",
            headers=_headers(),
        )
    resp.raise_for_status()
    commit = resp.json()

    # Get parent commit (the state before this commit)
    parent_sha = commit["parents"][0]["sha"] if commit.get("parents") else None
    if not parent_sha:
        raise RuntimeError("Cannot revert: commit has no parent")

    # Create revert by updating main ref to parent's tree
    # Use the merge API with a revert message
    async with httpx.AsyncClient(timeout=30.0) as client:
        # Get the parent tree
        parent_resp = await client.get(
            f"{API_BASE}/repos/{owner}/{repo}/git/commits/{parent_sha}",
            headers=_headers(),
        )
    parent_resp.raise_for_status()
    parent_tree = parent_resp.json()["tree"]["sha"]

    # Create a new commit with the parent's tree but current main as parent
    async with httpx.AsyncClient(timeout=30.0) as client:
        # Get current main SHA
        main_resp = await client.get(
            f"{API_BASE}/repos/{owner}/{repo}/git/refs/heads/main",
            headers=_headers(),
        )
    main_resp.raise_for_status()
    current_main_sha = main_resp.json()["object"]["sha"]

    # Create revert commit
    async with httpx.AsyncClient(timeout=30.0) as client:
        commit_resp = await client.post(
            f"{API_BASE}/repos/{owner}/{repo}/git/commits",
            headers=_headers(),
            json={
                "message": f"Revert: {commit['message'][:100]}",
                "tree": parent_tree,
                "parents": [current_main_sha],
            },
        )
    commit_resp.raise_for_status()
    revert_sha = commit_resp.json()["sha"]

    # Update main to point to revert commit
    async with httpx.AsyncClient(timeout=30.0) as client:
        update_resp = await client.patch(
            f"{API_BASE}/repos/{owner}/{repo}/git/refs/heads/main",
            headers=_headers(),
            json={"sha": revert_sha},
        )
    update_resp.raise_for_status()

    return {"revert_sha": revert_sha, "reverted_commit": sha}


async def list_commits(owner: str, repo: str, limit: int = 10) -> list:
    """List recent commits on main."""
    _check_token()
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.get(
            f"{API_BASE}/repos/{owner}/{repo}/commits",
            headers=_headers(),
            params={"sha": "main", "per_page": limit},
        )
    resp.raise_for_status()

    commits = []
    for c in resp.json():
        commits.append({
            "sha": c["sha"][:7],
            "full_sha": c["sha"],
            "message": c["commit"]["message"],
            "author": c["commit"]["author"]["name"],
            "date": c["commit"]["author"]["date"],
        })
    return commits
