# AutoSchemaKG on your own papers

Small starter for a knowledge graph from a handful of paper PDFs with [AutoSchemaKG](https://github.com/HKUST-KnowComp/AutoSchemaKG) (MIT). This is not the prebuilt ATLAS-Pes2o graph. You supply the papers.

PDF ingest follows upstream [`example/pdf_md_conversion`](https://github.com/HKUST-KnowComp/AutoSchemaKG/blob/main/example/pdf_md_conversion/readme.md): PDF to Markdown with [pdf_process](https://github.com/Swgj/pdf_process) (Marker), Markdown to JSON, then triple extraction. Use [uv](https://docs.astral.sh/uv/) for both environments. Do not use conda or pip as the package manager.

## What you need

- Python 3.10+ (uv will install it)
- [uv](https://docs.astral.sh/uv/getting-started/installation/)
- An LLM key for Marker (Azure OpenAI or Gemini) and an OpenAI-compatible endpoint for extraction
- 5–20 PDFs

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

## 1. PDF to Markdown

Upstream asks for a separate environment because `marker-pdf` pins old dependencies. Keep that split; only the installer changes.

```bash
git clone https://github.com/Swgj/pdf_process
cd pdf_process
uv venv --python 3.10 .venv
source .venv/bin/activate
uv pip install 'marker-pdf[full]' google-genai
```

On macOS, Marker still needs the system libraries from the [pdf_process README](https://github.com/Swgj/pdf_process) (`brew install weasyprint glib pango harfbuzz fontconfig cairo` and the symlinks). uv does not replace those.

Edit `config.yaml` the same way as upstream:

- `input.path`: a folder of PDFs, or one PDF
- `file_filters.extensions: [".pdf"]`
- `output.base_dir: "md_output"`
- Azure: set `llm_service` to `marker.services.azure_openai.AzureOpenAIService` and `api.api_key_env: "AZURE_API_KEY"`
- Gemini: comment out `llm_service` and set `api.api_key_env: "GEMINI_API_KEY"`
- `extract_images: false` if you want LLM descriptions of figures; `true` to keep image files only
- `page_range`: `null` for the whole paper, or a list of pages

Export the key, then run Marker with the uv environment active:

```bash
export AZURE_API_KEY=...    # or GEMINI_API_KEY
bash run.sh
```

Markdown lands in `md_output/` (one subdirectory per PDF if `create_subdirs: true`).

## 2. Markdown to JSON

Back in this repo, a second uv environment holds `atlas-rag`. Do not install Marker into it.

```bash
cd /path/to/autoschemakg-papers
uv venv --python 3.10
source .venv/bin/activate
uv pip install -r requirements.txt
cp .env.example .env
# edit .env: OPENAI_API_KEY, OPENAI_BASE_URL, OPENAI_MODEL
uv run python -m atlas_rag.kg_construction.utils.md_processing.markdown_to_json \
    --input /path/to/pdf_process/md_output \
    --output data
```

`--input` is the Markdown directory. `--output` is where JSON files are written. If Marker created one subdirectory per paper, point `--input` at the directory that actually contains the `.md` files, or run the command once per paper directory.

`filename_pattern` in the next step is a substring of the JSON filename. Name or copy the file you want to `data/robotics.json` if you keep the default.

## 3. Extract triples

```bash
uv run python scripts/run_extraction.py --input data/robotics.json --output import/robotics
```

Outputs in `import/robotics/`:

- triple JSON from the LLM
- CSV node and edge lists
- a GraphML file

Open the GraphML in NetworkX or Gephi. On a small set, skip schema induction until the triples look right. Pass `--concepts` to run it.

## What to expect

- Cost is linear in pages and chunks. Abstract plus introduction, method, and experiments is usually enough. Set `page_range` in `config.yaml` to drop references.
- Below a few dozen papers, concept induction mostly renames entities already in those papers. Triple extraction is the useful step.
- Default prompts extract generic entities and events. For robotics, edit `ROBOTICS_HINT` in `scripts/run_extraction.py`, or follow upstream `example/example_scripts/custom_extraction/`.
- Tables and equations are still lossy. Marker is better than raw PDF text, not a substitute for the paper.

## Cite

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
PDF conversion: https://github.com/HKUST-KnowComp/AutoSchemaKG/blob/main/example/pdf_md_conversion/readme.md
