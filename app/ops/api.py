"""Administrative FastAPI routes managing GxP system rollback and recovery."""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from typing import List

from app.auth.tenant import UserSession, GxPRole
from app.ops.recovery import GxPSystemRecoveryManager, ValidatedStateSnapshot
from api import get_current_session, require_role

router = APIRouter(
    prefix="/api/v1/admin/recovery",
    tags=["recovery"]
)


class RollbackRequest(BaseModel):
    """Payload to trigger dynamic GxP environment configuration rollback."""
    snapshot_id: str = Field(..., description="Unique UUID of target qualified state snapshot.")
    justification: str = Field(..., description="Regulatory justification for change control documentation.")


class HotfixRequest(BaseModel):
    """Payload to apply an emergency hot-fix prompt change."""
    target_agent: str = Field(..., description="Target subagent prompt name to override.")
    prompt_text: str = Field(..., description="Direct replacement prompt string template.")
    justification: str = Field(..., description="Change control justification.")


@router.post(
    "/rollback",
    status_code=status.HTTP_200_OK,
    summary="Restore system state configuration to last qualified snapshot"
)
async def restore_snapshot(
    payload: RollbackRequest,
    session: UserSession = Depends(require_role({GxPRole.QUALITY_APPROVER}))
):
    """Dynamically restores registry system prompts and model settings to match a target qualified snapshot."""
    try:
        from app.database import AuditLogger
        audit_logger = AuditLogger()
        
        await GxPSystemRecoveryManager.trigger_emergency_rollback(
            target_snapshot_id=payload.snapshot_id,
            operator_id=session.user_id,
            justification=payload.justification,
            audit_logger=audit_logger
        )
        return {"status": "SUCCESS", "message": f"System configuration reverted to snapshot '{payload.snapshot_id}'."}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post(
    "/hotfix",
    status_code=status.HTTP_200_OK,
    summary="Apply emergency prompt hot-fix"
)
async def apply_hotfix(
    payload: HotfixRequest,
    session: UserSession = Depends(require_role({GxPRole.QUALITY_APPROVER}))
):
    """Deploys a prompt hot-fix, executes qualification testing, and enforces self-reversion upon failure."""
    try:
        from app.database import AuditLogger
        audit_logger = AuditLogger()
        
        version = await GxPSystemRecoveryManager.apply_emergency_hot_fix(
            target_agent=payload.target_agent,
            target_prompt_text=payload.prompt_text,
            operator_id=session.user_id,
            justification=payload.justification,
            audit_logger=audit_logger
        )
        return {"status": "QUALIFIED", "active_version": version}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get(
    "/snapshots",
    response_model=List[ValidatedStateSnapshot],
    summary="Get all qualified snapshots"
)
async def list_snapshots(
    session: UserSession = Depends(require_role({GxPRole.QUALITY_APPROVER, GxPRole.AUDITOR}))
):
    """Returns a list of all qualified, historically qualified system state configurations."""
    return GxPSystemRecoveryManager.get_snapshots()
