from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.rag.indexer import IndexPlaybooksOptions, index_playbooks

__all__ = [
    "IndexPlaybooksOptions",
    "index_playbooks",
]


def __getattr__(name: str) -> object:
    if name == "IndexPlaybooksOptions":
        from app.rag.indexer import IndexPlaybooksOptions

        return IndexPlaybooksOptions
    if name == "index_playbooks":
        from app.rag.indexer import index_playbooks

        return index_playbooks
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
