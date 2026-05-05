import hashlib
import re

from app.schemas import PlaybookChunk, PlaybookIndexError, RawPlaybook


HEADING_PATTERN = re.compile(r"^(#{1,3})\s+(.+?)\s*$")


def split_playbook(
    playbook: RawPlaybook,
    chunk_size: int,
    chunk_overlap: int,
) -> list[PlaybookChunk]:
    chunks: list[PlaybookChunk] = []
    for section, section_content in split_by_headings(playbook.content, playbook.title):
        for text_part in split_long_text(section_content, chunk_size, chunk_overlap):
            chunk_index = len(chunks) + 1
            chunks.append(
                PlaybookChunk(
                    chunk_id=chunk_id_for(playbook, section, chunk_index),
                    section=section,
                    content=text_part,
                    metadata={
                        "split_method": "markdown_heading_recursive",
                        "chunk_size": chunk_size,
                        "chunk_overlap": chunk_overlap,
                        "chunk_index": chunk_index,
                        "source_file": playbook.source_file,
                        "tactic": playbook.tactic,
                    },
                )
            )
    if not chunks:
        raise PlaybookIndexError(f"No chunks produced for {playbook.source_file}")
    return chunks


def split_by_headings(content: str, fallback_section: str) -> list[tuple[str, str]]:
    sections: list[tuple[str, list[str]]] = []
    current_title = fallback_section
    current_lines: list[str] = []

    for line in content.splitlines():
        match = HEADING_PATTERN.match(line)
        if match:
            if current_lines:
                sections.append((current_title, current_lines))
            current_title = match.group(2).strip()
            current_lines = []
            continue
        current_lines.append(line)

    if current_lines:
        sections.append((current_title, current_lines))

    return [
        (section, "\n".join(lines).strip())
        for section, lines in sections
        if "\n".join(lines).strip()
    ]


def split_long_text(text_value: str, chunk_size: int, chunk_overlap: int) -> list[str]:
    if len(text_value) <= chunk_size:
        return [text_value]

    chunks: list[str] = []
    start = 0
    while start < len(text_value):
        end = min(start + chunk_size, len(text_value))
        if end < len(text_value):
            paragraph_break = text_value.rfind("\n\n", start, end)
            if paragraph_break > start:
                end = paragraph_break

        chunk = text_value[start:end].strip()
        if chunk:
            chunks.append(chunk)

        if end >= len(text_value):
            break
        start = max(end - chunk_overlap, start + 1)
    return chunks


def chunk_id_for(playbook: RawPlaybook, section: str | None, chunk_index: int) -> str:
    raw_identity = "|".join(
        [playbook.source_file, playbook.tactic, section or "", str(chunk_index)]
    )
    slug = "_".join(
        part
        for part in [
            slugify(playbook.source_file),
            slugify(playbook.tactic),
            slugify(section),
        ]
        if part
    )
    if not slug:
        slug = "playbook_chunk"
    if len(slug) > 120:
        slug = slug[:120].strip("_")
    return f"{slug}_{chunk_index:04d}_{short_hash(raw_identity)}"


def slugify(value: str | None) -> str:
    if value is None:
        return ""
    return re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")


def short_hash(value: str) -> str:
    return hashlib.sha1(value.encode("utf-8")).hexdigest()[:8]
