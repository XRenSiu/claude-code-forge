---
contract_version: 0.1.0
applies_to: distill-collector — audio/video pipeline
status: SCAFFOLDING-ONLY
references:
  - ./cli-spec.md
  - ./redaction-policy.md
  - ../../distill-meta/references/output-spec.md
---

# Audio / Video Pipeline — Reference

> **[SCAFFOLDING-ONLY]** This document describes the pipeline that
> `distill-collector transcribe` **would** run. v1 prints the command
> templates and exits 20 (see cli-spec.md §4). The binaries themselves
> (`whisper`, `ffmpeg`, `yt-dlp`) are **[USER-RESPONSIBILITY]** — they are not
> bundled and will never be bundled in v1, per risks TEC-01 / EST-02.

The pipeline has three stages: **acquire → extract audio → transcribe**. Any
one of them can be skipped if you already have the intermediate artifact.

```
   URL ───── yt-dlp ────► local video/audio
                               │
   local video ─── ffmpeg ─────► local audio
                               │
   local audio ─── whisper ────► transcript (.txt/.srt/.vtt/.json)
                               │
                   distill-collector
                    (wrap, redact, frontmatter)
                               │
                               ▼
             knowledge/transcripts/{slug}-{ISO8601}.md
             knowledge/media/{slug}.md   (metadata pointer only)
```

---

## 1. Accepted inputs

| Kind        | Extensions                         | Notes |
|-------------|------------------------------------|-------|
| Local audio | `.m4a`, `.mp3`, `.wav`, `.flac`    | Whisper-native. |
| Local video | `.mp4`, `.mov`, `.mkv`, `.webm`    | Must be audio-extracted first. |
| URL         | any `yt-dlp`-supported URL         | YouTube / Bilibili / Podcast feeds / etc. |

`distill-collector transcribe <path-or-url>` auto-detects by extension /
URL-scheme and dispatches to the right sub-pipeline below.

---

## 2. Stage A — URL ingest (`yt-dlp`) `[USER-RESPONSIBILITY]`

Install: `pip install yt-dlp` (or `brew install yt-dlp`).

**Audio-only download** (preferred when you don't need the video):

```bash
yt-dlp --extract-audio --audio-format mp3 \
       --output 'downloads/%(title)s.%(ext)s' \
       "{url}"
```

**Subtitle extraction** (free transcript if the source provides one):

```bash
yt-dlp --write-auto-subs --sub-lang en,zh --skip-download \
       --output 'downloads/%(title)s.%(ext)s' \
       "{url}"
```

If auto-subs are present and of acceptable quality, the pipeline **[SCAFFOLDING-ONLY]** would
prefer them over Whisper to save compute; fall back to Whisper only when the
subtitle file is empty or `--language` does not match `--sub-lang`.

**Output of stage A**: a local media file under `downloads/` (outside the
persona skill root). This directory is **not** `knowledge/media/`.

---

## 3. Stage B — Video → audio extraction (`ffmpeg`) `[USER-RESPONSIBILITY]`

Install: `brew install ffmpeg` / `apt install ffmpeg` / [ffmpeg.org builds].

**Stream copy** (preferred, no re-encode; needs AAC inside the mp4):

```bash
ffmpeg -i video.mp4 -vn -acodec copy audio.aac
```

**Fallback re-encode** (for containers that do not carry AAC):

```bash
ffmpeg -i video.mov -vn -acodec libmp3lame -ab 128k audio.mp3
```

Skip stage B entirely if the input is already audio.

---

## 4. Stage C — Transcription (`whisper`) `[USER-RESPONSIBILITY]`

Install options (pick one):

| Runner                    | Install                                | Notes |
|---------------------------|----------------------------------------|-------|
| `openai-whisper` (Python) | `pip install -U openai-whisper`        | Reference. Torch-heavy. |
| `whisper.cpp`             | build from source                      | CPU-friendly. |
| `faster-whisper`          | `pip install faster-whisper`           | CTranslate2 backend, faster. |

**Canonical command template** (the one `transcribe` will print as
`[SCAFFOLDING-ONLY] would run`):

```bash
whisper {input} \
    --model small \
    --language auto \
    --output_format txt \
    --output_dir knowledge/transcripts/
```

**Model choice guidance**:

| Model      | Use when                                             | Latency |
|------------|------------------------------------------------------|---------|
| `base`     | fastest, English-only content, quick triage         | ~1×     |
| `small`    | **default** — balanced Chinese/English               | ~2×     |
| `medium`   | noisy interviews, multi-speaker                      | ~5×     |
| `large-v3` | production-grade Chinese or code-switched content    | ~10×    |

The `--model` flag on `distill-collector transcribe` maps 1:1 to Whisper's.

### 4.1 Code-switching & known accuracy limits

- **Chinese/English code-switching**: `large-v3` clearly beats `medium`. For
  interviews that switch every other sentence (common in tech persona
  corpora), users should override `--model large-v3` explicitly; the default
  `small` will produce pinyin drift.
- **Dialects**: Cantonese / Wu / Sichuanese accuracy degrades even on
  `large-v3`; consider using `--language yue` where supported.
- **Hallucinated trailers**: Whisper is known to hallucinate a final sentence
  on silence; the pipeline strips trailing lines that repeat verbatim.
- **Diarization**: not built into Whisper. The `--diarize` flag on
  `transcribe` is documented as a **stub** that would shell out to
  `pyannote.audio` if present; otherwise transcripts have no speaker labels
  (single-speaker assumption).

---

## 5. Post-processing (the part distill-collector owns)

After Whisper emits `.txt`, the wrapper that v1 **would** run (but
`[SCAFFOLDING-ONLY]` exits 20 instead):

1. Read the Whisper `.txt` (or `.vtt` if timestamps are needed).
2. Segment into paragraphs every ~5 sentences or every 60s of timestamps.
3. Wrap into Markdown with the frontmatter required by output-spec.md §2.4:

```markdown
---
tier: primary
tier_reason: direct spoken content by subject
source_policy: interview
author_of_record: "{subject}"
captured_at: 2026-04-14T00:00:00Z
platform: audio-video
source_url: "{url-or-local-path-redacted}"
model: small
language: zh
redaction: applied-v20260414
---

## 00:00:00 — 00:01:04
paragraph ...

## 00:01:04 — 00:02:10
paragraph ...
```

4. Run redaction (`redaction-policy.md`) — transcripts are especially
   vulnerable to leaked phone numbers / emails spoken aloud.
5. Write a sibling pointer in `knowledge/media/{slug}.md` with duration,
   bitrate, source URL (redacted of tokens), without the raw bytes.

---

## 6. Known limitations (v1)

- **Requires local install** of at least Whisper + ffmpeg + yt-dlp; the skill
  will never bundle these. Environment failures return exit code 3.
- **GPU is optional but nearly mandatory** for `large-v3`. CPU-only
  transcription of a 1-hour interview at `large-v3` can take 2+ hours.
- **No speaker diarization by default** — transcripts are a single stream.
  Downstream distill-meta Phase 2 is aware of this limitation.
- **Timestamps can drift** on long audio with silence; the pipeline does not
  attempt forced alignment.
- **Subtitle-vs-Whisper quality tradeoff**: user may prefer auto-subs when
  they exist; there is no automatic quality-score comparison in v1.

## 7. Non-goals (v1)

- Live streaming transcription.
- Translation (Whisper's `--task translate` is documented but not used by the
  pipeline; this skill keeps source-language transcripts).
- Video-side OCR of burned-in subtitles (that is an image-pipeline concern;
  see `image-doc-parsers.md`).
- Bundling Whisper model weights. Always downloaded on first user run.
