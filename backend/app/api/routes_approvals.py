from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.auth_dependencies import READ_ROLES, REVIEWER_ROLES, require_roles
from app.api.dependencies import get_db_session
from app.schemas.common import ErrorResponse
from app.schemas.approval import ApprovalDecision, ApprovalRequestListResponse, ApprovalRequestRead
from app.services.approvals import ApprovalNotFoundError, ApprovalService


router = APIRouter(prefix="/api/approvals", tags=["approvals"])


@router.get(
    "",
    response_model=list[ApprovalRequestRead] | ApprovalRequestListResponse,
    status_code=status.HTTP_200_OK,
    summary="List approval requests",
    description="Return approval requests ordered by newest first so operators can review pending risky actions.",
)
async def list_approvals(
    db: Session = Depends(get_db_session),
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
    include_meta: bool = False,
    _: object = Depends(require_roles(*READ_ROLES)),
) -> list[ApprovalRequestRead] | ApprovalRequestListResponse:
    service = ApprovalService(db)
    approvals = service.list_requests(limit=limit, offset=offset)
    items = [ApprovalRequestRead.model_validate(approval) for approval in approvals]
    if not include_meta:
        return items
    return ApprovalRequestListResponse(
        items=items,
        meta={
            "total": service.count_requests(),
            "limit": limit,
            "offset": offset,
        },
    )


@router.get(
    "/{approval_id}",
    response_model=ApprovalRequestRead,
    status_code=status.HTTP_200_OK,
    summary="Get approval request",
    description="Fetch a single approval request with risk, reason, expected impact, rollback plan, and approval status.",
    responses={404: {"model": ErrorResponse, "description": "Approval request was not found."}},
)
async def get_approval(
    approval_id: int,
    db: Session = Depends(get_db_session),
    _: object = Depends(require_roles(*READ_ROLES)),
) -> ApprovalRequestRead:
    try:
        approval = ApprovalService(db).get_request(approval_id)
    except ApprovalNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return ApprovalRequestRead.model_validate(approval)


@router.post(
    "/{approval_id}/approve",
    response_model=ApprovalRequestRead,
    status_code=status.HTTP_200_OK,
    summary="Approve risky action",
    description="Approve a pending risky action. The backend then executes the simulated remediation path and records timeline and audit entries.",
    responses={404: {"model": ErrorResponse, "description": "Approval request was not found."}},
)
async def approve_request(
    approval_id: int,
    payload: ApprovalDecision,
    db: Session = Depends(get_db_session),
    _: object = Depends(require_roles(*REVIEWER_ROLES)),
) -> ApprovalRequestRead:
    try:
        approval = ApprovalService(db).approve_request(approval_id, payload.approved_by)
    except ApprovalNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return ApprovalRequestRead.model_validate(approval)


@router.post(
    "/{approval_id}/reject",
    response_model=ApprovalRequestRead,
    status_code=status.HTTP_200_OK,
    summary="Reject risky action",
    description="Reject a pending risky action so the remediation is not executed.",
    responses={404: {"model": ErrorResponse, "description": "Approval request was not found."}},
)
async def reject_request(
    approval_id: int,
    payload: ApprovalDecision,
    db: Session = Depends(get_db_session),
    _: object = Depends(require_roles(*REVIEWER_ROLES)),
) -> ApprovalRequestRead:
    try:
        approval = ApprovalService(db).reject_request(approval_id, payload.approved_by)
    except ApprovalNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return ApprovalRequestRead.model_validate(approval)
