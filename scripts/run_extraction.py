"""Extract an AutoSchemaKG graph from a JSON paper file.

Expects the list written by the Markdown-to-JSON step. filename_pattern is a
substring of the input filename, so data/robotics.json is selected by 'robotics'.

LLM_PROVIDER selects the client. atlas-rag only needs an OpenAI-compatible
chat.completions endpoint, which both Grok and Claude expose.
"""

import argparse
import os
import shutil
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

from keychain import get_secret

from atlas_rag.kg_construction.triple_config import ProcessingConfig
from atlas_rag.kg_construction.triple_extraction import KnowledgeGraphExtractor
from atlas_rag.llm_generator import LLMGenerator

ROBOTICS_HINT = (
    "Prefer robotics relations: robot or platform, task, method, dataset, "
    "baseline, and metric. Keep entity names as they appear in the paper."
)

PROVIDERS = {
    "grok": {
        "key": "XAI_API_KEY",
        "base_url": "https://api.x.ai/v1",
        "model": "grok-4",
    },
    "claude": {
        "key": "ANTHROPIC_API_KEY",
        "base_url": "https://api.anthropic.com/v1/",
        "model": "claude-sonnet-4-5",
    },
    "openai": {
        "key": "OPENAI_API_KEY",
        "base_url": "https://api.openai.com/v1",
        "model": "gpt-4o-mini",
    },
}


def secret(name: str) -> str | None:
    return get_secret(name) or os.environ.get(name) or None


def build_client():
    provider = (secret("LLM_PROVIDER") or "grok").strip().lower()
    if provider not in PROVIDERS:
        raise SystemExit(f"LLM_PROVIDER must be one of: {', '.join(PROVIDERS)}")
    spec = PROVIDERS[provider]
    api_key = secret(spec["key"])
    if not api_key:
        raise SystemExit(
            f"No {spec['key']} in the Keychain service 'autoschemakg' or in the environment.\n"
            f"Store it with: security add-generic-password -U -s autoschemakg -a {spec['key']} -w"
        )
    base_url = secret("LLM_BASE_URL") or spec["base_url"]
    model_name = secret("LLM_MODEL") or spec["model"]
    client = OpenAI(api_key=api_key, base_url=base_url)
    return provider, client, model_name


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
        raise SystemExit(f"Missing {args.input}. Run the Markdown-to-JSON step first.")

    provider, client, model_name = build_client()
    print(f"provider={provider} model={model_name}")
    print(ROBOTICS_HINT)

    staged = args.output / "_input"
    staged.mkdir(parents=True, exist_ok=True)
    staged_file = staged / args.input.name
    shutil.copyfile(args.input, staged_file)

    generator = LLMGenerator(client, model_name=model_name, backend="custom")
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
