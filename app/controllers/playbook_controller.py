from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.core.container import Container
from app.schemas.playbook_schema import (
    PlaybookDetailResponse,
    PlaybookListItemResponse,
)
from app.services.playbook_service import PlaybookService


router = APIRouter(prefix="/playbooks", tags=["playbooks"])


@router.get("", response_model=list[PlaybookListItemResponse])
@inject
def get_playbooks(
    active_only: bool = Query(default=True),
    playbook_service: PlaybookService = Depends(Provide[Container.playbook_service]),
):
    playbooks = playbook_service.list_playbooks(active_only=active_only)
    return [PlaybookListItemResponse.from_playbook(playbook) for playbook in playbooks]


@router.get("/{playbook_idx}", response_model=PlaybookDetailResponse)
@inject
def get_playbook_by_idx(
    playbook_idx: int,
    playbook_service: PlaybookService = Depends(Provide[Container.playbook_service]),
):
    playbook = playbook_service.get_playbook_by_idx(playbook_idx)
    if playbook is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Playbook not found",
        )

    return PlaybookDetailResponse.from_playbook(playbook)
