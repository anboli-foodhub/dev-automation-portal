import re
import time
from typing import Any, Dict, List, Optional, Tuple
from app.core.config import settings
from app.core.logging import log_api_call
from app.core.tag_conventions import get_convention
from app.clients.github_client import GithubClient

_TAG_VERSION_RE = re.compile(r"^((?:\d+\.)+)(\d+)(.*)$")
_SIT_MARKER = "sit"

class GithubService:
    # In-memory simulator states for tags, branches, and PRs
    _sim_branches = ["main", "develop", "feature/auth-dashboard", "feature/jira-api-client"]
    _sim_tags = [
        {"name": "0.0.100-MS-SIT-DEMO", "sha": "f8a9d10e", "message": "Initial SIT tag", "date": "2026-06-01"},
        {"name": "0.0.50", "sha": "c3d4e5f6", "message": "Initial main tag", "date": "2026-07-01"}
    ]
    _sim_prs = {
        101: {
            "number": 101,
            "title": "Feature: Integrate material ui dashboard cards",
            "state": "open",
            "user": "developer-jane",
            "html_url": "https://github.com/owner/repo/pull/101",
            "draft": False,
            "mergeable": True,
            "commits": 4,
            "changed_files": 12,
            "additions": 340,
            "deletions": 55,
            "reviews": [],
            "inline_comments": [],
            "head": {"sha": "a1b2c3d4e5f60718293a4b5c6d7e8f9012345678"}
        },
        102: {
            "number": 102,
            "title": "Refactor: Modular BaseAPIClient for retries and logs",
            "state": "open",
            "user": "staff-architect",
            "html_url": "https://github.com/owner/repo/pull/102",
            "draft": False,
            "mergeable": True,
            "commits": 2,
            "changed_files": 3,
            "additions": 98,
            "deletions": 12,
            "reviews": [{"user": "senior-engineer", "state": "APPROVED", "comment": "Excellent refactoring"}],
            "inline_comments": [],
            "head": {"sha": "b2c3d4e5f60718293a4b5c6d7e8f90123456789a"}
        }
    }

    _sim_pr_files = {
        101: [
            {
                "filename": "frontend/src/components/DashboardCard.tsx",
                "status": "modified",
                "additions": 8,
                "deletions": 2,
                "changes": 10,
                "patch": (
                    "@@ -1,6 +1,8 @@\n"
                    " import React from 'react';\n"
                    "-import { Card } from './Card';\n"
                    "+import { Card, CardContent } from './Card';\n"
                    "+import { Chip } from '@mui/material';\n"
                    " \n"
                    " export const DashboardCard = () => {\n"
                    "-  return <Card>Hello</Card>;\n"
                    "+  return (\n"
                    "+    <Card>\n"
                    "+      <CardContent><Chip label=\"New\" /></CardContent>\n"
                    "+    </Card>\n"
                    "+  );\n"
                    " };"
                )
            },
            {
                "filename": "frontend/src/pages/Dashboard.tsx",
                "status": "modified",
                "additions": 3,
                "deletions": 1,
                "changes": 4,
                "patch": (
                    "@@ -12,7 +12,9 @@ export const Dashboard = () => {\n"
                    "   return (\n"
                    "     <Box>\n"
                    "-      <DashboardCard />\n"
                    "+      <DashboardCard variant=\"compact\" />\n"
                    "+      {/* new pinned section */}\n"
                    "+      <PinnedSection />\n"
                    "     </Box>\n"
                    "   );\n"
                    " };"
                )
            }
        ],
        102: [
            {
                "filename": "backend/app/clients/base_client.py",
                "status": "modified",
                "additions": 6,
                "deletions": 3,
                "changes": 9,
                "patch": (
                    "@@ -20,9 +20,12 @@ class BaseAPIClient:\n"
                    "         retries: int = 2,\n"
                    "         backoff_factor: float = 0.5\n"
                    "     ) -> Tuple[int, Any, Optional[str], float]:\n"
                    "-        for attempt in range(retries + 1):\n"
                    "-            async with httpx.AsyncClient(timeout=self.timeout) as client:\n"
                    "-                response = await client.request(method, url, params=params, json=json_data)\n"
                    "+        async with httpx.AsyncClient(timeout=self.timeout) as client:\n"
                    "+            for attempt in range(retries + 1):\n"
                    "+                response = await client.request(method, url, params=params, json=json_data)\n"
                    "+                if 200 <= response.status_code < 300:\n"
                    "+                    break\n"
                    "         return status_code, response_data, error_msg, execution_time_ms"
                )
            }
        ]
    }

    def __init__(self):
        self.client = GithubClient()

    @staticmethod
    def _resolve_repo(owner: Optional[str], repo: Optional[str]) -> tuple:
        """A pasted PR link can point at any repo the token can see, so owner/repo are
        per-call - only fall back to the (usually blank) settings-configured repo."""
        return (owner or settings.GITHUB_OWNER, repo or settings.GITHUB_REPO)

    async def get_pull_request(self, pr_number: int, owner: Optional[str] = None, repo: Optional[str] = None) -> Dict[str, Any]:
        start_time = time.perf_counter()
        resolved_owner, resolved_repo = self._resolve_repo(owner, repo)
        if settings.github_configured and resolved_owner and resolved_repo:
            status_code, data, error, duration = await self.client.get_pull_request(resolved_owner, resolved_repo, pr_number)
            if status_code == 200:
                return {"success": True, "source": "live", "data": data, "execution_time_ms": duration}
            # Real repo/token configured but the live call failed (404 unknown PR, 403 no
            # access, etc) - surface that, don't silently substitute simulated fixture data.
            error_detail = error or (data.get("message") if isinstance(data, dict) else None) or f"GitHub returned HTTP {status_code}"
            return {"success": False, "source": "live", "error": error_detail, "execution_time_ms": duration}

        # Simulation mode (no token, or no repo resolvable at all)
        duration = (time.perf_counter() - start_time) * 1000
        pr = self._sim_prs.get(pr_number)
        if not pr:
            log_api_call("github", f"/repos/{resolved_owner or 'owner'}/{resolved_repo or 'repo'}/pulls/{pr_number}", "GET", duration, 404, None, None, f"PR #{pr_number} not found", is_simulated=True)
            return {"success": False, "source": "simulated", "error": f"PR #{pr_number} not found", "execution_time_ms": duration}

        log_api_call("github", f"/repos/{resolved_owner or 'owner'}/{resolved_repo or 'repo'}/pulls/{pr_number}", "GET", duration, 200, None, pr, is_simulated=True)
        return {"success": True, "source": "simulated", "data": pr, "execution_time_ms": duration}

    async def get_pull_request_files(self, pr_number: int, owner: Optional[str] = None, repo: Optional[str] = None) -> Dict[str, Any]:
        start_time = time.perf_counter()
        resolved_owner, resolved_repo = self._resolve_repo(owner, repo)
        if settings.github_configured and resolved_owner and resolved_repo:
            status_code, data, error, duration = await self.client.get_pull_request_files(resolved_owner, resolved_repo, pr_number)
            if status_code == 200:
                return {"success": True, "source": "live", "data": data, "execution_time_ms": duration}
            error_detail = error or (data.get("message") if isinstance(data, dict) else None) or f"GitHub returned HTTP {status_code}"
            return {"success": False, "source": "live", "error": error_detail, "execution_time_ms": duration}

        # Simulation mode
        duration = (time.perf_counter() - start_time) * 1000
        files = self._sim_pr_files.get(pr_number)
        if files is None:
            return {"success": False, "source": "simulated", "error": f"PR #{pr_number} not found", "execution_time_ms": duration}

        log_api_call("github", f"/repos/{resolved_owner or 'owner'}/{resolved_repo or 'repo'}/pulls/{pr_number}/files", "GET", duration, 200, None, files, is_simulated=True)
        return {"success": True, "source": "simulated", "data": files, "execution_time_ms": duration}

    async def approve_pull_request(
        self,
        pr_number: int,
        comment: str,
        event: str,
        owner: Optional[str] = None,
        repo: Optional[str] = None,
        commit_id: Optional[str] = None,
        comments: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        start_time = time.perf_counter()
        resolved_owner, resolved_repo = self._resolve_repo(owner, repo)
        if settings.github_configured and resolved_owner and resolved_repo:
            status_code, data, error, duration = await self.client.approve_pull_request(
                resolved_owner, resolved_repo, pr_number, comment, event, commit_id=commit_id, comments=comments
            )
            if status_code in (200, 201):
                return {"success": True, "source": "live", "data": data, "execution_time_ms": duration}
            error_detail = error or (data.get("message") if isinstance(data, dict) else None) or f"GitHub returned HTTP {status_code}"
            return {"success": False, "source": "live", "error": error_detail, "execution_time_ms": duration}

        # Simulation Mode
        duration = (time.perf_counter() - start_time) * 1000
        pr = self._sim_prs.get(pr_number)
        if not pr:
            return {"success": False, "source": "simulated", "error": f"PR #{pr_number} not found", "execution_time_ms": duration}

        review = {"user": "current-user", "state": "APPROVED" if event == "APPROVE" else "COMMENT", "comment": comment}
        pr["reviews"].append(review)
        pr.setdefault("inline_comments", []).extend(comments or [])
        if event == "APPROVE":
            pr["state"] = "approved"

        log_api_call("github", f"/repos/{resolved_owner or 'owner'}/{resolved_repo or 'repo'}/pulls/{pr_number}/reviews", "POST", duration, 201, {"body": comment, "event": event, "comments": comments}, review, is_simulated=True)
        return {"success": True, "source": "simulated", "data": review, "execution_time_ms": duration}

    async def list_repos(self) -> Dict[str, Any]:
        start_time = time.perf_counter()
        if settings.github_configured:
            status_code, data, error, duration = await self.client.list_user_repos()
            if status_code == 200 and isinstance(data, list):
                repos = [
                    {
                        "owner": r["owner"]["login"],
                        "name": r["name"],
                        "full_name": r["full_name"],
                        "default_branch": r.get("default_branch", "main"),
                    }
                    for r in data
                ]
                return {"success": True, "source": "live", "data": repos, "execution_time_ms": duration}
            error_detail = error or (data.get("message") if isinstance(data, dict) else None) or f"GitHub returned HTTP {status_code}"
            return {"success": False, "source": "live", "error": error_detail, "execution_time_ms": duration}

        # Simulation Mode (no token configured)
        duration = (time.perf_counter() - start_time) * 1000
        repos = [{"owner": "owner", "name": "repo", "full_name": "owner/repo", "default_branch": "main"}]
        log_api_call("github", "/user/repos", "GET", duration, 200, None, repos, is_simulated=True)
        return {"success": True, "source": "simulated", "data": repos, "execution_time_ms": duration}

    async def list_branches(self, owner: Optional[str] = None, repo: Optional[str] = None) -> Dict[str, Any]:
        start_time = time.perf_counter()
        resolved_owner, resolved_repo = self._resolve_repo(owner, repo)
        if settings.github_configured and resolved_owner and resolved_repo:
            # GitHub's branch listing has no defined sort order and active repos can have
            # hundreds of branches (a common branch like "main" isn't guaranteed to appear
            # even 500 in) - so this is just a cheap first page to seed a free-typing picker,
            # not an exhaustive list. The real validation happens against the exact name at
            # branch-creation time via get_branch_ref.
            status_code, data, error, duration = await self.client.list_branches_page(resolved_owner, resolved_repo, 1)
            if status_code == 200 and isinstance(data, list):
                branches = [b["name"] for b in data]
                return {"success": True, "source": "live", "data": branches, "execution_time_ms": duration}
            error_detail = error or (data.get("message") if isinstance(data, dict) else None) or f"GitHub returned HTTP {status_code}"
            return {"success": False, "source": "live", "error": error_detail, "execution_time_ms": duration}

        # Simulation Mode
        duration = (time.perf_counter() - start_time) * 1000
        log_api_call("github", f"/repos/{resolved_owner or 'owner'}/{resolved_repo or 'repo'}/branches", "GET", duration, 200, None, self._sim_branches, is_simulated=True)
        return {"success": True, "source": "simulated", "data": list(self._sim_branches), "execution_time_ms": duration}

    async def list_tags(self, owner: Optional[str] = None, repo: Optional[str] = None) -> Dict[str, Any]:
        start_time = time.perf_counter()
        resolved_owner, resolved_repo = self._resolve_repo(owner, repo)
        if settings.github_configured and resolved_owner and resolved_repo:
            # Cheap first page only - this feeds a free-typing Autocomplete picker, not the
            # increment-suggestion logic (which needs the full list, see _list_all_tags below).
            status_code, data, error, duration = await self.client.list_repo_tags_page(resolved_owner, resolved_repo, 1)
            if status_code == 200 and isinstance(data, list):
                tags = [t["name"] for t in data]
                return {"success": True, "source": "live", "data": tags, "execution_time_ms": duration}
            error_detail = error or (data.get("message") if isinstance(data, dict) else None) or f"GitHub returned HTTP {status_code}"
            return {"success": False, "source": "live", "error": error_detail, "execution_time_ms": duration}

        # Simulation Mode
        duration = (time.perf_counter() - start_time) * 1000
        tag_names = [t["name"] for t in self._sim_tags]
        log_api_call("github", f"/repos/{resolved_owner or 'owner'}/{resolved_repo or 'repo'}/tags", "GET", duration, 200, None, tag_names, is_simulated=True)
        return {"success": True, "source": "simulated", "data": tag_names, "execution_time_ms": duration}

    async def _list_all_tags(self, owner: str, repo: str, max_pages: int = 20) -> Tuple[Optional[List[str]], Optional[str], float]:
        """Unlike list_tags (cheap first page for a picker), the increment-suggestion logic
        needs the full tag list - SIT and main tags can use entirely independent numbering
        sequences within the same repo, so a SIT tag can be many pages deep. Repos realistically
        have low hundreds to low thousands of tags, so paging through is fast and safe (capped
        at max_pages as a backstop)."""
        names: List[str] = []
        total_duration = 0.0
        page = 1
        while page <= max_pages:
            status_code, data, error, duration = await self.client.list_repo_tags_page(owner, repo, page)
            total_duration += duration
            if status_code != 200 or not isinstance(data, list):
                error_detail = error or (data.get("message") if isinstance(data, dict) else None) or f"GitHub returned HTTP {status_code}"
                return None, error_detail, total_duration
            names.extend(t["name"] for t in data)
            if len(data) < 100:
                break
            page += 1
        return names, None, total_duration

    @staticmethod
    def _parse_tag_version(tag_name: str) -> Optional[Tuple[str, int, str]]:
        m = _TAG_VERSION_RE.match(tag_name)
        if not m:
            return None
        prefix, num, suffix = m.groups()
        return prefix, int(num), suffix

    @staticmethod
    def _matches_bucket(tag_name: str, filter_substr: Optional[str]) -> bool:
        lname = tag_name.lower()
        if filter_substr is None:
            return _SIT_MARKER not in lname
        return filter_substr.lower() in lname

    @classmethod
    def _pick_and_increment(cls, tag_names: List[str], filter_substr: Optional[str]) -> Optional[Tuple[str, str]]:
        """Among tags matching the bucket filter, picks the one with the highest embedded
        version number (a cheap, reliable proxy for "latest" - GitHub's tags API exposes no
        date without an extra call per tag, and these are monotonically-increasing schemes)
        and returns (incremented_tag_name, source_tag_name)."""
        best: Optional[Tuple[int, str, Tuple[str, int, str]]] = None
        for name in tag_names:
            if not cls._matches_bucket(name, filter_substr):
                continue
            parsed = cls._parse_tag_version(name)
            if not parsed:
                continue
            if best is None or parsed[1] > best[0]:
                best = (parsed[1], name, parsed)
        if not best:
            return None
        _, source_name, (prefix, num, suffix) = best
        return f"{prefix}{num + 1}{suffix}", source_name

    async def suggest_next_tag(self, environment: str, owner: Optional[str] = None, repo: Optional[str] = None, source_branch: Optional[str] = None) -> Dict[str, Any]:
        start_time = time.perf_counter()
        resolved_owner, resolved_repo = self._resolve_repo(owner, repo)
        full_name = f"{resolved_owner}/{resolved_repo}" if resolved_owner and resolved_repo else None
        convention = get_convention(full_name, environment)

        if settings.github_configured and resolved_owner and resolved_repo:
            if convention["mode"] == "last_merged_pr":
                base_branch = source_branch or environment
                status_code, data, error, duration = await self.client.list_pull_requests(resolved_owner, resolved_repo, state="closed", base=base_branch)
                if status_code != 200 or not isinstance(data, list):
                    error_detail = error or (data.get("message") if isinstance(data, dict) else None) or f"GitHub returned HTTP {status_code}"
                    return {"success": False, "source": "live", "error": error_detail, "execution_time_ms": duration}
                merged = [pr for pr in data if pr.get("merged_at")]
                if not merged:
                    return {"success": False, "source": "live", "error": f"No merged pull requests found into '{base_branch}' to derive a tag from", "execution_time_ms": duration}
                latest_pr = max(merged, key=lambda pr: pr["number"])
                suggested = f"{convention.get('prefix', '')}{latest_pr['number']}"
                basis = f"Based on latest merged PR #{latest_pr['number']} into {base_branch}"
                return {"success": True, "source": "live", "data": {"suggested_tag": suggested, "basis": basis}, "execution_time_ms": duration}

            tag_names, error, duration = await self._list_all_tags(resolved_owner, resolved_repo)
            if tag_names is None:
                return {"success": False, "source": "live", "error": error, "execution_time_ms": duration}
            result = self._pick_and_increment(tag_names, convention.get("filter"))
            if not result:
                return {"success": False, "source": "live", "error": f"No existing {environment.upper()} tag found to increment from - type the first tag manually", "execution_time_ms": duration}
            suggested, basis_tag = result
            return {"success": True, "source": "live", "data": {"suggested_tag": suggested, "basis": f"Incremented from {basis_tag}"}, "execution_time_ms": duration}

        # Simulation Mode (no token, or no repo resolvable at all)
        duration = (time.perf_counter() - start_time) * 1000
        result = self._pick_and_increment([t["name"] for t in self._sim_tags], convention.get("filter"))
        if not result:
            return {"success": False, "source": "simulated", "error": f"No existing {environment.upper()} tag found to increment from - type the first tag manually", "execution_time_ms": duration}
        suggested, basis_tag = result
        return {"success": True, "source": "simulated", "data": {"suggested_tag": suggested, "basis": f"Incremented from {basis_tag}"}, "execution_time_ms": duration}

    async def create_branch(self, branch_name: str, source_branch: str, owner: Optional[str] = None, repo: Optional[str] = None) -> Dict[str, Any]:
        start_time = time.perf_counter()
        resolved_owner, resolved_repo = self._resolve_repo(owner, repo)
        if settings.github_configured and resolved_owner and resolved_repo:
            # First fetch source branch commit SHA
            status_code, data, error, duration = await self.client.get_branch_ref(resolved_owner, resolved_repo, source_branch)
            if status_code != 200:
                error_detail = error or (data.get("message") if isinstance(data, dict) else None) or f"Could not resolve source branch '{source_branch}' (HTTP {status_code})"
                return {"success": False, "source": "live", "error": error_detail, "execution_time_ms": duration}

            sha = data["object"]["sha"]
            st_code, br_data, err, dur = await self.client.create_branch(resolved_owner, resolved_repo, branch_name, sha)
            if st_code in (200, 201):
                return {"success": True, "source": "live", "data": br_data, "execution_time_ms": duration + dur}
            error_detail = err or (br_data.get("message") if isinstance(br_data, dict) else None) or f"GitHub returned HTTP {st_code}"
            return {"success": False, "source": "live", "error": error_detail, "execution_time_ms": duration + dur}

        # Simulation Mode (no token, or no repo resolvable at all)
        duration = (time.perf_counter() - start_time) * 1000
        if branch_name in self._sim_branches:
            return {"success": False, "source": "simulated", "error": f"Branch {branch_name} already exists", "execution_time_ms": duration}

        self._sim_branches.append(branch_name)
        res_data = {"ref": f"refs/heads/{branch_name}", "object": {"sha": "mocksha1234567890", "type": "commit"}}
        log_api_call("github", f"/repos/{resolved_owner or 'owner'}/{resolved_repo or 'repo'}/git/refs", "POST", duration, 201, {"ref": f"refs/heads/{branch_name}", "sha": "source_sha"}, res_data, is_simulated=True)
        return {"success": True, "source": "simulated", "data": res_data, "execution_time_ms": duration}

    async def generate_release_notes(
        self,
        owner: Optional[str] = None,
        repo: Optional[str] = None,
        tag_name: str = "",
        target_commitish: Optional[str] = None,
        previous_tag_name: Optional[str] = None,
    ) -> Dict[str, Any]:
        start_time = time.perf_counter()
        resolved_owner, resolved_repo = self._resolve_repo(owner, repo)

        if settings.github_configured and resolved_owner and resolved_repo:
            status_code, data, error, duration = await self.client.generate_release_notes(
                resolved_owner, resolved_repo, tag_name, target_commitish, previous_tag_name
            )
            if status_code == 200 and isinstance(data, dict):
                return {"success": True, "source": "live", "data": {"name": data.get("name", tag_name), "body": data.get("body", "")}, "execution_time_ms": duration}
            error_detail = error or (data.get("message") if isinstance(data, dict) else None) or f"GitHub returned HTTP {status_code}"
            return {"success": False, "source": "live", "error": error_detail, "execution_time_ms": duration}

        # Simulation Mode
        duration = (time.perf_counter() - start_time) * 1000
        body = f"## What's Changed\n* Simulated changes leading up to {tag_name}\n\n**Full Changelog**: simulated diff since previous tag"
        return {"success": True, "source": "simulated", "data": {"name": tag_name, "body": body}, "execution_time_ms": duration}

    async def create_tag(
        self,
        tag_name: str,
        owner: Optional[str] = None,
        repo: Optional[str] = None,
        source_branch: Optional[str] = None,
        target_sha: Optional[str] = None,
        notes_template: Optional[str] = None,
        publish_release: bool = False,
    ) -> Dict[str, Any]:
        start_time = time.perf_counter()
        resolved_owner, resolved_repo = self._resolve_repo(owner, repo)

        if settings.github_configured and resolved_owner and resolved_repo:
            total_duration = 0.0
            sha = target_sha
            if not sha:
                status_code, data, error, duration = await self.client.get_branch_ref(resolved_owner, resolved_repo, source_branch or "main")
                total_duration += duration
                if status_code != 200:
                    error_detail = error or (data.get("message") if isinstance(data, dict) else None) or f"Could not resolve source branch '{source_branch}' (HTTP {status_code})"
                    return {"success": False, "source": "live", "error": error_detail, "execution_time_ms": total_duration}
                sha = data["object"]["sha"]

            # Standard Git flow tag creation: tag object then reference
            status_code, data, error, duration = await self.client.create_tag_object(resolved_owner, resolved_repo, tag_name, sha, notes_template or "Release tag")
            total_duration += duration
            if status_code not in (200, 201):
                error_detail = error or (data.get("message") if isinstance(data, dict) else None) or f"GitHub returned HTTP {status_code}"
                return {"success": False, "source": "live", "error": error_detail, "execution_time_ms": total_duration}

            ref_code, ref_data, ref_error, ref_duration = await self.client.create_ref(resolved_owner, resolved_repo, f"refs/tags/{tag_name}", sha)
            total_duration += ref_duration
            if ref_code not in (200, 201):
                error_detail = ref_error or (ref_data.get("message") if isinstance(ref_data, dict) else None) or f"GitHub returned HTTP {ref_code}"
                return {"success": False, "source": "live", "error": error_detail, "execution_time_ms": total_duration}

            result_data = ref_data
            if publish_release:
                # A plain git tag has no visible page on GitHub - publishing a Release on top of it
                # is what actually makes the notes show up under the repo's Releases tab.
                rel_code, rel_data, rel_error, rel_duration = await self.client.create_release(
                    resolved_owner, resolved_repo, tag_name, tag_name, notes_template or "", target_commitish=sha
                )
                total_duration += rel_duration
                if rel_code not in (200, 201):
                    error_detail = rel_error or (rel_data.get("message") if isinstance(rel_data, dict) else None) or f"Tag created, but publishing the GitHub Release failed (HTTP {rel_code})"
                    return {"success": False, "source": "live", "error": error_detail, "execution_time_ms": total_duration}
                result_data = rel_data

            return {"success": True, "source": "live", "data": result_data, "execution_time_ms": total_duration}

        # Simulation Mode (no token, or no repo resolvable at all)
        duration = (time.perf_counter() - start_time) * 1000
        sha = target_sha or "mocksha1234567890"
        for tag in self._sim_tags:
            if tag["name"] == tag_name:
                return {"success": False, "source": "simulated", "error": f"Tag {tag_name} already exists", "execution_time_ms": duration}

        new_tag = {
            "name": tag_name,
            "sha": sha[:8],
            "message": notes_template or f"Release {tag_name}",
            "date": "2026-07-17"
        }
        self._sim_tags.append(new_tag)
        log_api_call("github", f"/repos/{resolved_owner or 'owner'}/{resolved_repo or 'repo'}/git/tags", "POST", duration, 201, {"tag": tag_name, "object": sha}, new_tag, is_simulated=True)
        return {"success": True, "source": "simulated", "data": new_tag, "execution_time_ms": duration}

    async def compare_tags(self, base_tag: str, head_tag: str, owner: Optional[str] = None, repo: Optional[str] = None) -> Dict[str, Any]:
        start_time = time.perf_counter()
        resolved_owner, resolved_repo = self._resolve_repo(owner, repo)
        if settings.github_configured and resolved_owner and resolved_repo:
            status_code, data, error, duration = await self.client.compare_tags(resolved_owner, resolved_repo, base_tag, head_tag)
            if status_code == 200:
                return {"success": True, "source": "live", "data": data, "execution_time_ms": duration}
            error_detail = error or (data.get("message") if isinstance(data, dict) else None) or f"GitHub returned HTTP {status_code}"
            return {"success": False, "source": "live", "error": error_detail, "execution_time_ms": duration}

        # Simulation Mode
        duration = (time.perf_counter() - start_time) * 1000
        # Search mock tags
        tag_names = [t["name"] for t in self._sim_tags]
        if base_tag not in tag_names or head_tag not in tag_names:
            return {"success": False, "source": "simulated", "error": f"One or both tags ({base_tag}, {head_tag}) not found in database", "execution_time_ms": duration}

        compare_data = {
            "status": "ahead",
            "ahead_by": 5,
            "behind_by": 0,
            "total_commits": 5,
            "commits": [
                {"sha": "c1a2b3c4", "commit": {"message": "Merge branch 'feature/itsm-attachment-uploads'", "author": {"name": "developer-jane"}}},
                {"sha": "d5e6f7g8", "commit": {"message": "Fix Reseller tax_id unique check query", "author": {"name": "staff-architect"}}},
                {"sha": "h9i0j1k2", "commit": {"message": "Refactor CRM client order lists parsing", "author": {"name": "developer-jane"}}},
                {"sha": "l3m4n5o6", "commit": {"message": "Implement keyboard shortcuts for command palette", "author": {"name": "developer-jane"}}},
                {"sha": "p7q8r9s0", "commit": {"message": "Draft release notes generation service", "author": {"name": "staff-architect"}}}
            ]
        }
        log_api_call("github", f"/repos/{resolved_owner or 'owner'}/{resolved_repo or 'repo'}/compare/{base_tag}...{head_tag}", "GET", duration, 200, None, compare_data, is_simulated=True)
        return {"success": True, "source": "simulated", "data": compare_data, "execution_time_ms": duration}
