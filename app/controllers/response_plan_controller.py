from fastapi import APIRouter, Depends, HTTPException, status
from dependency_injector.wiring import Provide, inject

from app.core.container import Container
from app.schemas import ResponsePlanDenyRequest, ResponsePlanResponse
from app.services.response_plan_service import ResponsePlanService


router = APIRouter(tags=["response-plans"])


@router.post(
    "/response-plans/{response_plan_idx}/approve",
    response_model=ResponsePlanResponse,
)
@inject
def approve_response_plan(
    response_plan_idx: int,
    response_plan_service: ResponsePlanService = Depends(
        Provide[Container.response_plan_service]
    ),
):
    try:
        response_plan = response_plan_service.approve(response_plan_idx)
    except ValueError as exc:
        raise _response_plan_error(exc) from exc
    return ResponsePlanResponse.from_response_plan(response_plan)


@router.post(
    "/response-plans/{response_plan_idx}/deny",
    response_model=ResponsePlanResponse,
)
@inject
def deny_response_plan(
    response_plan_idx: int,
    request: ResponsePlanDenyRequest,
    response_plan_service: ResponsePlanService = Depends(
        Provide[Container.response_plan_service]
    ),
):
    try:
        response_plan = response_plan_service.deny(
            response_plan_idx=response_plan_idx,
            denied_reason=request.denied_reason,
        )
    except ValueError as exc:
        raise _response_plan_error(exc) from exc
    return ResponsePlanResponse.from_response_plan(response_plan)


def _response_plan_error(exc: ValueError) -> HTTPException:
    message = str(exc)
    if "not found" in message.lower():
        return HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=message,
        )
    return HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail=message,
    )
