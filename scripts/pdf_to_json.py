"""Turn a folder of paper PDFs into the JSON list AutoSchemaKG expects."""

import argparse
import json
from pathlib import Path

import fitz


def pdf_to_text(path: Path) -> str:
    doc = fitz.open(path)
    try:
        return "\n\n".join(page.get_text() for page in doc).strip()
    finally:
        doc.close()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=Path("papers"))
    parser.add_argument("--output", type=Path, default=Path("data/robotics.json"))
    parser.add_argument("--max-chars", type=int, default=80_000,
                        help="Trim each paper so a small LLM run stays bounded.")
    args = parser.parse_args()

    pdfs = sorted(args.input.glob("*.pdf"))
    if not pdfs:
        raise SystemExit(f"No PDFs in {args.input}")

    docs = []
    for i, pdf in enumerate(pdfs, 1):
        text = pdf_to_text(pdf)
        if args.max_chars and len(text) > args.max_chars:
            text = text[: args.max_chars]
        docs.append({
            "id": str(i),
            "text": text,
            "metadata": {"lang": "en", "source": pdf.name},
        })
        print(f"{pdf.name}: {len(text)} chars")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(docs, ensure_ascii=False, indent=2))
    print(f"wrote {len(docs)} docs to {args.output}")


if __name__ == "__main__":
    main()
