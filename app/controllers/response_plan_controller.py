from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from dependency_injector.wiring import Provide, inject

from app.core.container import Container
from app.schemas import ResponsePlanDenyRequest, ResponsePlanResponse
from app.services.response_plan_action_executor import ResponsePlanActionExecutor
from app.services.response_plan_action_service import ResponsePlanActionService
from app.services.response_plan_service import ResponsePlanService


router = APIRouter(tags=["response-plans"])


@router.post(
    "/response-plans/{response_plan_idx}/approve",
    response_model=ResponsePlanResponse,
)
@inject
async def approve_response_plan(
    response_plan_idx: int,
    background_tasks: BackgroundTasks,
    response_plan_service: ResponsePlanService = Depends(
        Provide[Container.response_plan_service]
    ),
    response_plan_action_executor: ResponsePlanActionExecutor = Depends(
        Provide[Container.response_plan_action_executor]
    ),
):
    try:
        response_plan_service.approve(response_plan_idx)
    except ValueError as exception:
        raise _response_plan_error(exception) from exception

    background_tasks.add_task(
        _execute_response_plan_actions,
        response_plan_idx,
        response_plan_action_executor,
    )

    response_plan = response_plan_service.get_by_idx(response_plan_idx)
    if response_plan is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Response plan not found",
        )
    return ResponsePlanResponse.from_response_plan(response_plan)


async def _execute_response_plan_actions(
    response_plan_idx: int,
    response_plan_action_executor: ResponsePlanActionExecutor,
) -> None:
    await response_plan_action_executor.execute_pending_actions(response_plan_idx)


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
    response_plan_action_service: ResponsePlanActionService = Depends(
        Provide[Container.response_plan_action_service]
    ),
):
    try:
        response_plan_service.deny(
            response_plan_idx=response_plan_idx,
            denied_reason=request.denied_reason,
        )
        response_plan_action_service.skip_pending_actions(
            response_plan_idx=response_plan_idx,
            reason="Response plan denied",
        )
    except ValueError as exception:
        raise _response_plan_error(exception) from exception

    response_plan = response_plan_service.get_by_idx(response_plan_idx)
    if response_plan is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Response plan not found",
        )
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
