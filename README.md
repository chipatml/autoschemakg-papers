# AutoSchemaKG on your own papers

Small starter for building a knowledge graph from a handful of paper PDFs with [AutoSchemaKG](https://github.com/HKUST-KnowComp/AutoSchemaKG) (MIT). This is not the prebuilt ATLAS-Pes2o graph. You supply the papers.

ATLAS-Pes2o is abstracts from Semantic Scholar with a January 2023 cutoff. This repo runs the same extraction code on files you choose.

## What you need

- Python 3.10+
- An OpenAI-compatible LLM endpoint (API key and base URL), or a local model the `LLMGenerator` client can call
- 5–20 PDFs in `papers/`

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# edit .env: OPENAI_API_KEY, OPENAI_BASE_URL, OPENAI_MODEL
```

`atlas-rag` is the pip package for AutoSchemaKG.

## 1. PDFs to JSON

The extractor does not read PDFs. It reads a JSON list of `{id, text, metadata}`.

```bash
mkdir -p papers data
# put your PDFs in papers/
python scripts/pdf_to_json.py --input papers --output data/robotics.json
```

PyMuPDF text is enough for a first run. Two-column papers and equations will be messy. If the triples are garbage, convert with Marker (`example/pdf_md_conversion` in the AutoSchemaKG repo) and then `atlas_rag.kg_construction.utils.md_processing.markdown_to_json`.

## 2. Extract triples

```bash
python scripts/run_extraction.py --input data/robotics.json --output import/robotics
```

Outputs land in `import/robotics/`:

- triple JSON from the LLM
- CSV node and edge lists
- a GraphML file

Open the GraphML in NetworkX or Gephi. On a small set, skip schema induction until the triples look right. Pass `--concepts` to run it.

## 3. What to expect

- Cost is linear in pages and chunks. Abstract plus introduction, method, and experiments is usually enough. Full text is optional and more expensive.
- Below a few dozen papers, concept induction mostly renames entities already in those papers. Triple extraction is the useful step.
- Default prompts extract generic entities and events. For robotics, edit the prompt in `scripts/run_extraction.py` (`ROBOTICS_HINT`) or follow `example/example_scripts/custom_extraction/` upstream.
- Tables, figures, and equations are weak. Numerical results will be lossy.

## Cite

If you use this pipeline in research, cite AutoSchemaKG:

```
@misc{bai2025autoschemakgautonomousknowledgegraph,
  title={AutoSchemaKG: Autonomous Knowledge Graph Construction through Dynamic Schema Induction from Web-Scale Corpora},
  author={Jiaxin Bai and Wei Fan and Qi Hu and Qing Zong and Chunyang Li and Hong Ting Tsang and Hongyu Luo and Yauwai Yim and Haoyu Huang and Xiao Zhou and Feng Qin and Tianshi Zheng and Xi Peng and Xin Yao and Huiwen Yang and Leijie Wu and Yi Ji and Gong Zhang and Renhai Chen and Yangqiu Song},
  year={2025},
  eprint={2505.23628},
  archivePrefix={arXiv},
  primaryClass={cs.CL}
}
```

Upstream: https://github.com/HKUST-KnowComp/AutoSchemaKG
