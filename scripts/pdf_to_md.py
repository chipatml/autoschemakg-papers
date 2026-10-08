"""Convert PDFs with the sibling pdf_process checkout.

Assumes this repo and pdf_process are next to each other:

    parent/
      autoschemakg-papers/
      pdf_process/

Tables stay in the Markdown. Figures are described in text rather than
written out as separate image files. The Marker LLM pass uses Claude, and
the key is the same Keychain item extraction uses: service autoschemakg,
account ANTHROPIC_API_KEY.
"""

import os
import subprocess
import sys
from pathlib import Path

import yaml

from keychain import get_secret

REPO_ROOT = Path(__file__).resolve().parents[1]
PDF_PROCESS = REPO_ROOT.parent / "pdf_process"
PAPERS = REPO_ROOT / "papers"
OUTPUT = REPO_ROOT / "md_output"
KEY_ACCOUNT = "ANTHROPIC_API_KEY"


def main() -> None:
    if not (PDF_PROCESS / "pdf_to_pure_text.py").is_file():
        raise SystemExit(f"Expected sibling checkout at {PDF_PROCESS}")
    if not PAPERS.is_dir() or not any(PAPERS.glob("*.pdf")):
        raise SystemExit(f"Put PDFs in {PAPERS}")

    api_key = get_secret(KEY_ACCOUNT) or os.environ.get(KEY_ACCOUNT)
    if not api_key:
        raise SystemExit(
            "No ANTHROPIC_API_KEY in Keychain service 'autoschemakg'. "
            "Add it in Keychain Access or with security add-generic-password."
        )

    config = {
        "processing_config": {
            "llm_service": "marker.services.claude.ClaudeService",
            "other_config": {
                "use_llm": True,
                "extract_images": False,
                "page_range": None,
                "max_concurrency": 2,
                "claude_model_name": os.environ.get("LLM_MODEL", "claude-sonnet-4-5"),
            },
        },
        "api": {"api_key_env": "CLAUDE_API_KEY"},
        "input": {
            "path": str(PAPERS),
            "file_filters": {
                "extensions": [".pdf"],
                "recursive": True,
                "exclude_patterns": ["*temp*", "*~*"],
            },
        },
        "output": {
            "base_dir": str(OUTPUT),
            "create_subdirs": True,
            "format": "md",
        },
        "logging": {"level": "INFO", "show_progress": True},
    }
    config_path = REPO_ROOT / ".pdf_process.yaml"
    config_path.write_text(yaml.safe_dump(config, sort_keys=False))

    env = os.environ.copy()
    env["CLAUDE_API_KEY"] = api_key
    env["ANTHROPIC_API_KEY"] = api_key
    python = PDF_PROCESS / ".venv" / "bin" / "python"
    if not python.is_file():
        python = Path(sys.executable)
    print(f"claude pdf_process={PDF_PROCESS}")
    subprocess.run(
        [str(python), "pdf_to_pure_text.py", "--config", str(config_path)],
        cwd=PDF_PROCESS,
        env=env,
        check=True,
    )
    print(f"markdown in {OUTPUT}")


if __name__ == "__main__":
    main()
