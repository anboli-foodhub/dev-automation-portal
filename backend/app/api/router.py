import os
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from app.core.config import settings
from app.api import jira, github, devops, crm, itsm, logs, release_ticket

router = APIRouter(prefix="/api")

# Include sub-routers
router.include_router(jira.router)
router.include_router(github.router)
router.include_router(devops.router)
router.include_router(crm.router)
router.include_router(itsm.router)
router.include_router(logs.router)
router.include_router(release_ticket.router)

# Settings Schema
class SettingsUpdatePayload(BaseModel):
    JIRA_BASE_URL: Optional[str] = None
    JIRA_EMAIL: Optional[str] = None
    JIRA_API_TOKEN: Optional[str] = None
    GITHUB_TOKEN: Optional[str] = None
    GITHUB_OWNER: Optional[str] = None
    GITHUB_REPO: Optional[str] = None
    JENKINS_URL: Optional[str] = None
    JENKINS_USER: Optional[str] = None
    JENKINS_TOKEN: Optional[str] = None
    OCTOPUS_URL: Optional[str] = None
    OCTOPUS_API_KEY: Optional[str] = None
    CRM_BASE_URL: Optional[str] = None
    CRM_API_KEY: Optional[str] = None
    ITSM_BASE_URL: Optional[str] = None
    ITSM_API_KEY: Optional[str] = None

@router.get("/settings", tags=["Settings"])
async def get_settings():
    def mask(val: Optional[str]) -> Optional[str]:
        if not val:
            return ""
        if len(val) <= 6:
            return "****"
        return f"{val[:3]}...{val[-3:]}"

    return {
        "JIRA_BASE_URL": settings.JIRA_BASE_URL or "",
        "JIRA_EMAIL": settings.JIRA_EMAIL or "",
        "JIRA_API_TOKEN": mask(settings.JIRA_API_TOKEN),
        "GITHUB_TOKEN": mask(settings.GITHUB_TOKEN),
        "GITHUB_OWNER": settings.GITHUB_OWNER or "",
        "GITHUB_REPO": settings.GITHUB_REPO or "",
        "JENKINS_URL": settings.JENKINS_URL or "",
        "JENKINS_USER": settings.JENKINS_USER or "",
        "JENKINS_TOKEN": mask(settings.JENKINS_TOKEN),
        "OCTOPUS_URL": settings.OCTOPUS_URL or "",
        "OCTOPUS_API_KEY": mask(settings.OCTOPUS_API_KEY),
        "CRM_BASE_URL": settings.CRM_BASE_URL or "",
        "CRM_API_KEY": mask(settings.CRM_API_KEY),
        "ITSM_BASE_URL": settings.ITSM_BASE_URL or "",
        "ITSM_API_KEY": mask(settings.ITSM_API_KEY),
        "APP_ENV": settings.APP_ENV,
        "LOG_LEVEL": settings.LOG_LEVEL,
        "is_jira_configured": settings.jira_configured,
        "is_github_configured": settings.github_configured,
        "is_jenkins_configured": settings.jenkins_configured,
        "is_octopus_configured": settings.octopus_configured,
        "is_crm_configured": settings.crm_configured,
        "is_itsm_configured": settings.itsm_configured,
    }

@router.post("/settings", tags=["Settings"])
async def update_settings(payload: SettingsUpdatePayload):
    """
    Dynamically update `.env` file on disk and reload runtime config.
    """
    env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), ".env")
    
    # Read existing lines or start empty
    lines = []
    if os.path.exists(env_path):
        with open(env_path, "r") as f:
            lines = f.readlines()
            
    # Parse key-values from payload
    updates = payload.model_dump(exclude_unset=True)
    
    # Update config in settings object
    for k, v in updates.items():
        if v is not None:
            # Skip update if it was masked and not modified by user
            if v == "****" or (len(v) == 9 and "..." in v):
                continue
            setattr(settings, k, v)
            
            # Update lines in list
            key_found = False
            for idx, line in enumerate(lines):
                if line.strip().startswith(f"{k}="):
                    lines[idx] = f"{k}={v}\n"
                    key_found = True
                    break
            if not key_found:
                lines.append(f"{k}={v}\n")
                
    # Write back to file
    try:
        with open(env_path, "w") as f:
            f.writelines(lines)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to write configuration: {str(e)}")
        
    return {"status": "success", "message": "Configuration updated and saved to .env"}
