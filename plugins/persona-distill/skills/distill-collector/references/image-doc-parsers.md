---
contract_version: 0.1.0
applies_to: distill-collector — image & document ingest
status: SCAFFOLDING-ONLY
references:
  - ./cli-spec.md
  - ./redaction-policy.md
  - ../../distill-meta/references/output-spec.md
---

# Image & Document Parsers — Reference

> **[SCAFFOLDING-ONLY]** No OCR / PDF / docx / epub runner ships in v1. This
> document pins the contract so that a user-side script, or a future wave's
> implementation, emits Markdown in the same shape. All third-party tools are
> **[USER-RESPONSIBILITY]** — they must be installed and invoked by the user
> or their script; `distill-collector` only prints command templates and
> exit-20 stubs (see cli-spec.md §3).

## 1. Images (screenshots, photos)

### 1.1 OCR  `[USER-RESPONSIBILITY]`

Tool pointer: [Tesseract OCR](https://github.com/tesseract-ocr/tesseract).

```bash
# English only
tesseract input.jpg output -l eng

# Chinese (simplified) + English — canonical for persona corpora
tesseract input.jpg output -l chi_sim+eng

# Traditional Chinese + English
tesseract input.jpg output -l chi_tra+eng
```

Tesseract writes `output.txt`. The pipeline then wraps it into Markdown (see
§1.3). Install language packs separately (`brew install tesseract-lang`,
`apt install tesseract-ocr-chi-sim`, etc.).

Accuracy is heavily dependent on image resolution; users feeding tiny WeChat
screenshots should expect ≥15% error rate. No confidence filtering is built
into v1.

### 1.2 EXIF & metadata  `[USER-RESPONSIBILITY]`

Tool pointer: [`exiftool`](https://exiftool.org/).

```bash
exiftool -json -G input.jpg
```

Fields to capture:

- `EXIF:DateTimeOriginal` → feeds `captured_at` frontmatter.
- `EXIF:Make` / `EXIF:Model` → device provenance.
- `EXIF:GPSLatitude` / `EXIF:GPSLongitude` → **dropped by default** per
  redaction-policy §4 (location is PII). User must pass `--keep-gps` to
  preserve.
- `IPTC:Caption-Abstract` → used as `title` when present.

### 1.3 Output schema

One file per image: `knowledge/media/image-{YYYYMMDD}-{slug}.md`.

```markdown
---
tier: secondary
tier_reason: ocr'd screenshot; not direct speech
source_policy: user-provided
captured_at: 2024-03-02T14:32:00Z
platform: image
source_path: /absolute/path/redacted
device: "iPhone 14 Pro"
ocr_lang: chi_sim+eng
redaction: applied-v20260414
---

## OCR text

{ocr-text, paragraph-broken, redacted}

## Metadata

- taken: 2024-03-02 14:32
- device: iPhone 14 Pro
- gps: [REDACTED-GEO] (use --keep-gps to preserve)
```

The raw image file is **not** copied into the persona skill; only the
Markdown record is. Users who want the binaries around should symlink to an
external directory.

**Parser status**: spec-only.

---

## 2. PDF  `[USER-RESPONSIBILITY]`

Tool pointers (pick one):

| Tool            | When to use                          | Install |
|-----------------|--------------------------------------|---------|
| `pdftotext`     | layout-free text, fastest            | `brew install poppler` |
| `pdfplumber`    | tables, multi-column layouts         | `pip install pdfplumber` |
| `pypdf`         | simple metadata + text, pure-Python  | `pip install pypdf` |

Canonical template:

```bash
pdftotext -layout input.pdf output.txt
# or, for tables:
python -c "import pdfplumber; ..."   # see pdfplumber README
```

**Output**: `knowledge/articles/pdf/{YYYY}-{title-slug}.md`. Frontmatter
captures page count, declared author (from metadata), capture date.
OCR'd-PDFs (images-only) should be routed through §1.1 per page.

**Parser status**: spec-only.

---

## 3. DOCX  `[USER-RESPONSIBILITY]`

Tool pointer: [`python-docx`](https://pypi.org/project/python-docx/).

Heuristic: iterate `doc.paragraphs`, preserve heading levels (`Heading 1` →
`#`, `Heading 2` → `##`, etc.), tables rendered as Markdown tables, inline
images dropped with `_[image: redacted]_`.

**Output**: `knowledge/articles/docx/{title-slug}.md`. Revision history, if
preserved in the docx, is **not** parsed in v1.

**Parser status**: spec-only.

---

## 4. EPUB  `[USER-RESPONSIBILITY]`

Tool pointer: [`ebooklib`](https://pypi.org/project/EbookLib/) + BeautifulSoup
for the embedded XHTML.

```python
from ebooklib import epub
book = epub.read_epub("input.epub")
# iterate book.get_items_of_type(ebooklib.ITEM_DOCUMENT)
```

**Output**: one file per chapter under
`knowledge/articles/epub/{book-slug}/{NN-chapter}.md`, plus a
`knowledge/articles/epub/{book-slug}/INDEX.md` TOC.

**Parser status**: spec-only.

---

## 5. Notion export  `[USER-RESPONSIBILITY]`

**Input shape**: Notion "Export" → Markdown & CSV → ZIP containing one
`.md` per page plus attachments.

**Tool pointer**: no extra tool required; `unzip` + walk the directory. Each
page already ships as Markdown; the pipeline only needs to:

1. Rewrite Notion's auto-generated UUID filenames to slug-style.
2. Rewrite relative links between pages.
3. Apply frontmatter + redaction.

**Output**: `knowledge/articles/notion/{page-slug}.md`. Nested databases
exported as CSV become `knowledge/articles/notion/{db-slug}-table.md` (CSV
converted to Markdown table).

**Parser status**: spec-only. **Of all entries in this file, Notion is the
easiest to actually implement** (input is already Markdown), so a future
wave may promote it from spec-only to stub without violating the scaffolding
constraint.

---

## 6. Cross-format invariants

- **All outputs** under `knowledge/articles/` or `knowledge/media/` (never
  `chats/` — articles are long-form by definition).
- **All files** carry the frontmatter required by `output-spec.md §2.4`.
- **All text** passes through `redaction-policy.md` before write.
- **All binaries** (`.pdf`, `.docx`, `.epub`, source images) stay outside the
  persona skill unless the user explicitly copies them into `knowledge/media/`.
- **No OCR / parsing / EXIF runners** ship in v1. `distill-collector import
  --format generic` is the fallback for anyone with a plain-text version of
  the document already prepared.

## 7. Non-goals (v1)

- Handwriting recognition (Tesseract is poor at this; use a specialized model
  if needed — out of scope).
- Table-structure recovery beyond what pdfplumber / python-docx give for free.
- Translation.
- Figure / diagram description — the image becomes an opaque
  `_[image: redacted]_` in the output Markdown.
