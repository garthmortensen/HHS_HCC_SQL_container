import json
import re
from pathlib import Path


def _read_json(path: Path) -> dict:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _write_nojekyll(target_dir: Path) -> None:
    (target_dir / ".nojekyll").write_text("", encoding="utf-8")


def main() -> None:
    target_dir = Path(__file__).parent / "target"
    index_path = target_dir / "index.html"
    manifest_path = target_dir / "manifest.json"
    catalog_path = target_dir / "catalog.json"

    if not index_path.exists() or not manifest_path.exists():
        return

    index_html = index_path.read_text(encoding="utf-8")
    manifest = _read_json(manifest_path)
    catalog = _read_json(catalog_path)

    # Remove internal dbt artifacts from the inlined manifest to reduce noise.
    if "nodes" in manifest:
        manifest["nodes"] = {
            k: v for k, v in manifest["nodes"].items() if not re.search(r"\\.dbt\\.", k)
        }
    if "sources" in manifest:
        manifest["sources"] = {
            k: v for k, v in manifest["sources"].items() if not re.search(r"\\.dbt\\.", k)
        }

    def json_script_tag(script_id: str, payload: dict) -> str:
        return (
            f'<script type="application/json" id="{script_id}">\n'
            + json.dumps(payload)
            + "\n</script>"
        )

    # dbt docs expects these IDs.
    inlined = (
        json_script_tag("manifest", manifest)
        + "\n"
        + json_script_tag("catalog", catalog)
    )

    # Replace existing manifest/catalog placeholders if present, otherwise inject
    # right before closing body.
    replaced = False
    for script_id in ("manifest", "catalog"):
        pattern = re.compile(
            rf'<script[^>]*id="{re.escape(script_id)}"[^>]*>.*?</script>',
            re.DOTALL,
        )
        if pattern.search(index_html):
            index_html = pattern.sub("", index_html)
            replaced = True

    if replaced:
        # Put our inlined data at the end.
        index_html = index_html.replace("</body>", f"{inlined}\n</body>")
    else:
        index_html = index_html.replace("</body>", f"{inlined}\n</body>")

    index_path.write_text(index_html, encoding="utf-8")
    _write_nojekyll(target_dir)


if __name__ == "__main__":
    main()
