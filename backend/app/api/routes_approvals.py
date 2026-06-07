from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_db_session
from app.schemas.approval import ApprovalDecision, ApprovalRequestRead
from app.services.approvals import ApprovalNotFoundError, ApprovalService


router = APIRouter(prefix="/api/approvals", tags=["approvals"])


@router.get("", response_model=list[ApprovalRequestRead])
async def list_approvals(db: Session = Depends(get_db_session)) -> list[ApprovalRequestRead]:
    approvals = ApprovalService(db).list_requests()
    return [ApprovalRequestRead.model_validate(approval) for approval in approvals]


@router.get("/{approval_id}", response_model=ApprovalRequestRead)
async def get_approval(approval_id: int, db: Session = Depends(get_db_session)) -> ApprovalRequestRead:
    try:
        approval = ApprovalService(db).get_request(approval_id)
    except ApprovalNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return ApprovalRequestRead.model_validate(approval)


@router.post("/{approval_id}/approve", response_model=ApprovalRequestRead)
async def approve_request(
    approval_id: int,
    payload: ApprovalDecision,
    db: Session = Depends(get_db_session),
) -> ApprovalRequestRead:
    try:
        approval = ApprovalService(db).approve_request(approval_id, payload.approved_by)
    except ApprovalNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return ApprovalRequestRead.model_validate(approval)


@router.post("/{approval_id}/reject", response_model=ApprovalRequestRead)
async def reject_request(
    approval_id: int,
    payload: ApprovalDecision,
    db: Session = Depends(get_db_session),
) -> ApprovalRequestRead:
    try:
        approval = ApprovalService(db).reject_request(approval_id, payload.approved_by)
    except ApprovalNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return ApprovalRequestRead.model_validate(approval)
