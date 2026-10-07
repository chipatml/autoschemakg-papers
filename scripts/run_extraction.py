"""Extract an AutoSchemaKG graph from a JSON paper file.

Expects the list written by pdf_to_json.py. filename_pattern is a substring
of the input filename, so data/robotics.json is selected by 'robotics'.
"""

import argparse
import os
import shutil
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

from atlas_rag.kg_construction.triple_config import ProcessingConfig
from atlas_rag.kg_construction.triple_extraction import KnowledgeGraphExtractor
from atlas_rag.llm_generator import LLMGenerator

ROBOTICS_HINT = (
    "Prefer robotics relations: robot or platform, task, method, dataset, "
    "baseline, and metric. Keep entity names as they appear in the paper."
)


def main() -> None:
    load_dotenv()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=Path("data/robotics.json"))
    parser.add_argument("--output", type=Path, default=Path("import/robotics"))
    parser.add_argument("--concepts", action="store_true",
                        help="Also run schema induction. Skip this on a small set.")
    parser.add_argument("--workers", type=int, default=2)
    args = parser.parse_args()

    if not args.input.is_file():
        raise SystemExit(f"Missing {args.input}. Run scripts/pdf_to_json.py first.")

    api_key = os.environ.get("OPENAI_API_KEY")
    base_url = os.environ.get("OPENAI_BASE_URL")
    model_name = os.environ.get("OPENAI_MODEL")
    if not api_key or not model_name:
        raise SystemExit("Set OPENAI_API_KEY and OPENAI_MODEL in .env")

    # Extractor matches files in a directory by filename substring.
    staged = args.output / "_input"
    staged.mkdir(parents=True, exist_ok=True)
    staged_file = staged / args.input.name
    shutil.copyfile(args.input, staged_file)

    client = OpenAI(api_key=api_key, base_url=base_url or None)
    generator = LLMGenerator(client, model_name=model_name)
    config = ProcessingConfig(
        model_path=model_name,
        data_directory=str(staged),
        filename_pattern=args.input.stem,
        batch_size_triple=2,
        batch_size_concept=8,
        output_directory=str(args.output),
        max_new_tokens=2048,
        max_workers=args.workers,
        remove_doc_spaces=True,
    )
    kg = KnowledgeGraphExtractor(model=generator, config=config)
    print(ROBOTICS_HINT)
    print(f"extracting {staged_file.name} -> {args.output}")
    kg.run_extraction()
    kg.convert_json_to_csv()
    if args.concepts:
        kg.generate_concept_csv_temp(batch_size=8)
        kg.create_concept_csv()
    kg.convert_to_graphml()
    print(f"done: {args.output}")


if __name__ == "__main__":
    main()
