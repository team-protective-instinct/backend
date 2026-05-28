from fastapi import APIRouter, Depends, HTTPException, Query, status
from dependency_injector.wiring import inject, Provide
from app.services.incident_service import IncidentService
from app.services.incident_raw_log_service import IncidentRawLogService
from app.services.incident_report_service import IncidentReportService
from app.services.response_plan_service import ResponsePlanService
from app.core.container import Container
from app.models.constants import IncidentStatus
from app.schemas.incident_schema import (
    IncidentDetailResponse,
    IncidentListItemResponse,
    IncidentListResponse,
    SeverityFilter,
    OverviewSummaryResponse,
)


router = APIRouter(prefix="/incidents", tags=["incidents"])


@router.get("", response_model=IncidentListResponse)
@inject
def get_incidents(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    status: IncidentStatus | None = Query(default=None),
    severity: SeverityFilter | None = Query(default=None),
    q: str | None = Query(default=None),
    incident_service: IncidentService = Depends(Provide[Container.incident_service]),
):
    result = incident_service.get_incidents(
        page=page,
        limit=limit,
        status=status,
        severity=severity.value if severity else None,
        q=q,
    )
    return IncidentListResponse(
        items=[
            IncidentListItemResponse.from_incident(item.incident, item.report)
            for item in result.items
        ],
        page=result.page,
        limit=result.limit,
        total=result.total,
        total_pages=result.total_pages,
    )


@router.get("/pending", response_model=list[IncidentListItemResponse])
@inject
def get_pending_incidents(
    incident_service: IncidentService = Depends(Provide[Container.incident_service]),
):
    incidents = incident_service.get_pending_incidents()
    return [
        IncidentListItemResponse.from_incident(item.incident, item.report)
        for item in incidents
    ]


@router.get("/summary", response_model=OverviewSummaryResponse)
@inject
def get_overview_summary(
    incident_service: IncidentService = Depends(Provide[Container.incident_service]),
):
    result = incident_service.get_summary()
    return OverviewSummaryResponse.from_incident_summary(result)


@router.get("/{incident_idx}", response_model=IncidentDetailResponse)
@inject
def get_incident_by_idx(
    incident_idx: int,
    incident_service: IncidentService = Depends(Provide[Container.incident_service]),
    raw_log_service: IncidentRawLogService = Depends(
        Provide[Container.incident_raw_log_service]
    ),
    report_service: IncidentReportService = Depends(
        Provide[Container.incident_report_service]
    ),
    response_plan_service: ResponsePlanService = Depends(
        Provide[Container.response_plan_service]
    ),
):
    result = incident_service.get_incident_by_idx(incident_idx)
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Incident not found",
        )

    response_plan = response_plan_service.get_by_incident(incident_idx)
    report = report_service.get_latest_by_incident(incident_idx)
    raw_log = raw_log_service.get_latest_by_incident(incident_idx)
    return IncidentDetailResponse.from_incident(
        result,
        report=report,
        raw_log=raw_log,
        response_plan=response_plan,
    )
