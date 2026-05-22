from dataclasses import asdict
from typing import Callable, cast

from sqlalchemy.orm import Session

from app.models import RagPlaybook
from app.rag.embeddings import embed_query
from app.schemas import PlaybookRetrievalResult
from app.services.rag_service import retrieve_playbook_chunks


class PlaybookService:
    def __init__(self, session_factory: Callable[..., Session]):
        self.session_factory: Callable[..., Session] = session_factory

    def list_playbooks(self, active_only: bool = True) -> list[RagPlaybook]:
        with self.session_factory() as db:
            query = db.query(RagPlaybook)
            if active_only:
                query = query.filter(RagPlaybook.is_active.is_(True))
            return query.order_by(RagPlaybook.title.asc()).all()

    def get_playbook_by_idx(self, playbook_idx: int) -> RagPlaybook | None:
        with self.session_factory() as db:
            return db.query(RagPlaybook).filter(RagPlaybook.idx == playbook_idx).first()

    def retrieve_relevant_chunks(
        self,
        query: str,
        limit: int = 5,
        tactic: str | None = None,
    ) -> list[PlaybookRetrievalResult]:
        query_embedding = embed_query(query)
        with self.session_factory() as db:
            return retrieve_playbook_chunks(
                db=db,
                query_embedding=query_embedding,
                limit=limit,
                tactic=tactic,
            )

    def retrieval_result_to_dict(
        self, retrieval_result: PlaybookRetrievalResult
    ) -> dict[str, object]:
        return cast(dict[str, object], asdict(retrieval_result))
