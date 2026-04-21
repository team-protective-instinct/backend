from fastapi import APIRouter, Depends
from dependency_injector.wiring import inject, Provide
from app.services.incident_service import IncidentService
from app.core.container import Container


router = APIRouter(prefix="/incidents", tags=["incidents"])


@router.get("/pending")
@inject
def get_pending_incidents(
    incident_service: IncidentService = Depends(Provide[Container.incident_service])
):
    return incident_service.get_pending_incidents()


@router.get("/{incident_idx}")
@inject
def get_incident_by_idx(
    incident_idx: int, 
    incident_service: IncidentService = Depends(Provide[Container.incident_service])
):
    return incident_service.get_incident_by_idx(incident_idx=incident_idx)


@router.post("/{incident_id}/approve")
@inject
def approve_incident(
    incident_id: int, 
    incident_service: IncidentService = Depends(Provide[Container.incident_service])
):
    return incident_service.approve_incident(incident_id)


@router.post("/{incident_id}/deny")
@inject
def deny_incident(
    incident_id: int, 
    incident_service: IncidentService = Depends(Provide[Container.incident_service])
):
    return incident_service.deny_incident(incident_id)
