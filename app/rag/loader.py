from pathlib import Path
from typing import Any

from app.schemas import PlaybookIndexError, RawPlaybook


def load_playbooks(playbooks_dir: Path) -> list[RawPlaybook]:
    if not playbooks_dir.exists():
        raise PlaybookIndexError(f"Playbooks directory does not exist: {playbooks_dir}")
    if not playbooks_dir.is_dir():
        raise PlaybookIndexError(f"Playbooks path is not a directory: {playbooks_dir}")

    playbooks = [
        load_playbook(path, playbooks_dir)
        for path in sorted(playbooks_dir.glob("*.md"))
    ]
    if not playbooks:
        raise PlaybookIndexError(f"No Markdown playbooks found in {playbooks_dir}")
    return playbooks


def load_playbook(path: Path, base_dir: Path) -> RawPlaybook:
    if path.suffix.lower() != ".md":
        raise PlaybookIndexError(f"Playbook must be a Markdown file: {path}")

    metadata, content = parse_front_matter(path.read_text(encoding="utf-8"), path)
    doc_type = require_text(metadata, "doc_type", path)
    if doc_type != "playbook":
        raise PlaybookIndexError(f"Unsupported doc_type in {path}: {doc_type!r}")

    return RawPlaybook(
        title=require_text(metadata, "title", path),
        tactic=require_text(metadata, "tactic", path),
        source_file=path.relative_to(base_dir).as_posix(),
        content=content,
        recommended_action_hints=parse_string_list(
            metadata.get("recommended_action_hints"), "recommended_action_hints", path
        ),
        source_refs=parse_source_refs(metadata.get("source_refs"), path),
    )


def parse_front_matter(raw_text: str, path: Path) -> tuple[dict[str, Any], str]:
    if not raw_text.startswith("---"):
        raise PlaybookIndexError(f"Missing front matter: {path}")

    parts = raw_text.split("---", 2)
    if len(parts) != 3:
        raise PlaybookIndexError(f"Invalid front matter delimiter: {path}")

    content = parts[2].strip()
    if not content:
        raise PlaybookIndexError(f"Markdown body is empty: {path}")
    return parse_simple_front_matter(parts[1], path), content


def parse_simple_front_matter(front_matter: str, path: Path) -> dict[str, Any]:
    metadata: dict[str, Any] = {}
    current_key: str | None = None
    current_dict: dict[str, object] | None = None

    for raw_line in front_matter.splitlines():
        if not raw_line.strip():
            continue
        if not raw_line.startswith(" "):
            current_key, current_dict = parse_top_level_line(raw_line, path, metadata)
            continue
        current_dict = parse_nested_line(
            raw_line, path, metadata, current_key, current_dict
        )

    return metadata


def parse_top_level_line(
    raw_line: str,
    path: Path,
    metadata: dict[str, Any],
) -> tuple[str | None, dict[str, object] | None]:
    key, value = parse_key_value(raw_line, path)
    if value == "":
        metadata[key] = []
        return key, None
    metadata[key] = value
    return None, None


def parse_nested_line(
    raw_line: str,
    path: Path,
    metadata: dict[str, Any],
    current_key: str | None,
    current_dict: dict[str, object] | None,
) -> dict[str, object] | None:
    if current_key is None or not isinstance(metadata.get(current_key), list):
        raise PlaybookIndexError(
            f"Unexpected nested front matter line in {path}: {raw_line!r}"
        )

    items = metadata[current_key]
    if not isinstance(items, list):
        raise PlaybookIndexError(
            f"Front matter parser state error in {path}: {current_key}"
        )

    stripped = raw_line.strip()
    if stripped.startswith("- "):
        return append_list_item(stripped[2:].strip(), items, path)

    if current_dict is None:
        raise PlaybookIndexError(
            f"Unexpected nested front matter line in {path}: {raw_line!r}"
        )
    item_key, item_scalar = parse_key_value(stripped, path)
    current_dict[item_key] = item_scalar
    return current_dict


def append_list_item(
    item_value: str,
    items: list[object],
    path: Path,
) -> dict[str, object] | None:
    if ":" not in item_value:
        items.append(item_value)
        return None

    item_key, item_scalar = parse_key_value(item_value, path)
    current_dict: dict[str, object] = {item_key: item_scalar}
    items.append(current_dict)
    return current_dict


def parse_key_value(line: str, path: Path) -> tuple[str, str]:
    if ":" not in line:
        raise PlaybookIndexError(f"Invalid front matter line in {path}: {line!r}")
    key, value = line.split(":", 1)
    key = key.strip()
    if not key:
        raise PlaybookIndexError(f"Invalid blank front matter key in {path}: {line!r}")
    return key, value.strip()


def require_text(metadata: dict[str, Any], key: str, path: Path) -> str:
    value = metadata.get(key)
    if value is None or not str(value).strip():
        raise PlaybookIndexError(f"Missing required front matter '{key}' in {path}")
    return str(value).strip()


def parse_string_list(value: object, key: str, path: Path) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        stripped = value.strip()
        return [stripped] if stripped else []
    if isinstance(value, list) and all(isinstance(item, str) for item in value):
        return [item.strip() for item in value if item.strip()]
    raise PlaybookIndexError(
        f"Front matter '{key}' must be a string or list[str] in {path}"
    )


def parse_source_refs(value: object, path: Path) -> list[dict[str, object]]:
    if value is None:
        return []
    if not isinstance(value, list):
        raise PlaybookIndexError(f"Front matter 'source_refs' must be a list in {path}")

    refs: list[dict[str, object]] = []
    for index, item in enumerate(value):
        if isinstance(item, str):
            refs.append({"title": item})
        elif isinstance(item, dict):
            refs.append({str(key): ref_value for key, ref_value in item.items()})
        else:
            raise PlaybookIndexError(
                f"Unsupported source_refs item at index {index} in {path}"
            )
    return refs
