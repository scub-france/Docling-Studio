from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from docling_core.types.doc.document import DoclingDocument


def _default_output() -> Path:
    repo_root = Path(__file__).resolve().parents[2]
    return (
        repo_root
        / "frontend"
        / "src"
        / "features"
        / "document"
        / "docling"
        / "docling-document.schema.json"
    )


def _normalize_patterns(value: object) -> object:
    if isinstance(value, dict):
        normalized: dict[object, object] = {}
        for key, item in value.items():
            if key == "pattern" and isinstance(item, str):
                normalized[key] = re.sub(r"\(\?P<([^>]+)>", r"(?<\1>", item)
            else:
                normalized[key] = _normalize_patterns(item)
        return normalized
    if isinstance(value, list):
        return [_normalize_patterns(item) for item in value]
    return value


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Export the DoclingDocument Pydantic model as JSON Schema."
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=_default_output(),
        help="Path to write the generated JSON Schema file.",
    )
    args = parser.parse_args()

    schema = _normalize_patterns(DoclingDocument.model_json_schema())
    output_path = args.output.resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(schema, indent=2, sort_keys=True) + "\n")

    print(f"Wrote DoclingDocument schema to {output_path}")


if __name__ == "__main__":
    main()
