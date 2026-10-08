# AutoSchemaKG on your own papers

Small starter for a knowledge graph from a handful of paper PDFs with [AutoSchemaKG](https://github.com/HKUST-KnowComp/AutoSchemaKG) (MIT). This is not the prebuilt ATLAS-Pes2o graph. You supply the papers.

PDF ingest follows upstream [`example/pdf_md_conversion`](https://github.com/HKUST-KnowComp/AutoSchemaKG/blob/main/example/pdf_md_conversion/readme.md): PDF to Markdown, Markdown to JSON, then triple extraction. Use [uv](https://docs.astral.sh/uv/) for both environments. Do not use conda.

Grok and Claude are the extraction backends. Marker does not need either of them.

## What you need

- Python 3.10+ (uv will install it)
- [uv](https://docs.astral.sh/uv/getting-started/installation/)
- A Grok or Claude API key for extraction
- 5–20 PDFs

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

## 1. PDF to Markdown

Marker converts the PDF with its own layout model. Leave `use_llm: false` unless a paper has tables you need. The LLM pass in upstream `pdf_process` is Azure or Gemini only; it is not required, and it is not how Grok or Claude enter this pipeline.

```bash
git clone https://github.com/Swgj/pdf_process
cd pdf_process
uv venv --python 3.10 .venv
source .venv/bin/activate
uv pip install 'marker-pdf[full]'
```

On macOS, Marker still needs the system libraries from the [pdf_process README](https://github.com/Swgj/pdf_process) (`brew install weasyprint glib pango harfbuzz fontconfig cairo` and the symlinks). uv does not replace those.

In `config.yaml`:

- `input.path`: a folder of PDFs, or one PDF
- `file_filters.extensions: [".pdf"]`
- `output.base_dir: "md_output"`
- `use_llm: false`
- `page_range`: `null` for the whole paper, or a list of pages to drop references

```bash
bash run.sh
```

Markdown lands in `md_output/` (one subdirectory per PDF if `create_subdirs: true`).

To have Grok or Claude read a PDF instead of Marker, use the CLI on a single file and save the reply as Markdown. That login is a subscription session, not the API key used in the next step.

```bash
# Grok CLI, after `grok login`
grok -p "Convert this PDF to Markdown. Keep headings, tables, and equations as text. Skip references." papers/one.pdf > one.md

# Claude Code
claude -p "Convert this PDF to Markdown. Keep headings, tables, and equations as text. Skip references." papers/one.pdf > one.md
```

Do this only for a few hard papers. It is not the batch path.

## 2. Markdown to JSON

Back in this repo, a second uv environment holds `atlas-rag`. Do not install Marker into it.

```bash
cd /path/to/autoschemakg-papers
uv venv --python 3.10
source .venv/bin/activate
uv pip install -r requirements.txt
cp .env.example .env
```

Pick a provider. Extraction calls `chat.completions` on an OpenAI client. Grok and Claude both expose that. A `grok login` or `claude` browser session is not accepted here; those are subscription tokens.

On a Mac, store the key in the Keychain. The script checks the service `autoschemakg` before `.env`.

From the terminal, `-w` with no value prompts, so the key is not saved in shell history:

```bash
security add-generic-password -U -s autoschemakg -a LLM_PROVIDER -w grok
security add-generic-password -U -s autoschemakg -a XAI_API_KEY -w
# Claude instead:
# security add-generic-password -U -s autoschemakg -a LLM_PROVIDER -w claude
# security add-generic-password -U -s autoschemakg -a ANTHROPIC_API_KEY -w
```

Or add the item by hand in Keychain Access:

1. Open Keychain Access and select the login keychain.
2. File → New Password Item.
3. Keychain Item Name: `autoschemakg`. This is the service the script looks up.
4. Account Name: `XAI_API_KEY`, `ANTHROPIC_API_KEY`, or `OPENAI_API_KEY`.
5. Password: the API key.
6. Add a second item with account `LLM_PROVIDER` and password `grok` or `claude` if you do not want that in `.env`.

Confirm the GUI item has a service, not only a label:

```bash
security find-generic-password -s autoschemakg -a XAI_API_KEY -w
```

That should print the key. If it says the item could not be found, Get Info on the item and set the service to `autoschemakg`. The script searches by service and account, not by the displayed label.

Optional items are `LLM_MODEL` and `LLM_BASE_URL`. If `security` is missing, or the item is not there, the script falls back to the environment and `.env`.

| Provider | Keychain account | Endpoint | Default model |
| --- | --- | --- | --- |
| `grok` | `XAI_API_KEY` | `https://api.x.ai/v1` | `grok-4` |
| `claude` | `ANTHROPIC_API_KEY` | `https://api.anthropic.com/v1/` | `claude-sonnet-4-5` |
| `openai` | `OPENAI_API_KEY` | `https://api.openai.com/v1` | `gpt-4o-mini` |

Then:

```bash
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

The script prints `provider=grok` or `provider=claude` and the model name. Outputs in `import/robotics/`:

- triple JSON from the LLM
- CSV node and edge lists
- a GraphML file

Open the GraphML in Gephi (Layout → ForceAtlas 2) or NetworkX. On a small set, skip schema induction until the triples look right. Pass `--concepts` to run it.

For 50 papers of about 25 pages, triple extraction is on the order of $10–40 with Grok 4.6 ($2 / $6 per million input / output tokens) and $20–90 with Claude Sonnet 4.5 ($3 / $15). Full text plus `--concepts` is the high end. Marker with `use_llm: false` adds nothing to that bill.

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
