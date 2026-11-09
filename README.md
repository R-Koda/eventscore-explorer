# EventScore Explorer

[![Tests](https://github.com/R-Koda/eventscore-explorer/actions/workflows/tests.yml/badge.svg)](https://github.com/R-Koda/eventscore-explorer/actions/workflows/tests.yml)
**Explain why time-series events match — and why the score changes.**

A small, dependency-free Python toolkit that turns truth and prediction intervals into an interactive HTML report. Inspect one-to-one matches, misses, false alarms, and signed onset offsets. Switch endpoint tolerances without a server.

実際にどのイベントが対応したかを説明する、時系列評価ツールです。許容時間を切り替えてスコアの変化を確認できます。

## Install from PyPI / pipでインストール

Python 3.10 or later. Create and activate a virtual environment first:

```sh
python3 -m venv .venv
```

macOS / Linux: `source .venv/bin/activate`

Windows PowerShell: `.venv\Scripts\Activate.ps1`

```sh
python -m pip install eventscore-explorer
eventscore --help
```

The help screen confirms that the command is available. Install only the tools you need.
[PyPI package](https://pypi.org/project/eventscore-explorer/) · [Source and examples](https://github.com/R-Koda/eventscore-explorer)

サンプルCSV・Notebookなどはpipでは配置されません。公開デモはブラウザで開けます。自分でサンプルを実行する場合はGitHubの「Code → Download ZIP」で取得・展開し、READMEの相対パスをそのフォルダー内から指定してください。

## Article & live demo / 紹介記事と公開デモ

- [個別ガイド / EventScore Explorer：時系列の見逃し・誤検出を確かめる](https://ryu-koda.com/blog/eventscore-explorer-event-evaluation/)
- [紹介記事：データを分ける・評価する・公開する。Pythonの小さな確認ツールを3つ作りました](https://ryu-koda.com/blog/python-tools-splittrace-eventscore-notebook/) — Japanese overview of SplitTrace, EventScore Explorer, and Notebook Publish Check.
- [公開デモをブラウザで開く / Open the live demo](https://ryu-koda.com/articles/python-tools/eventscore-demo.html) — Synthetic data only; no installation required.

公開デモは合成データの出力例です。自分のファイルをアップロードする画面ではありません。
The hosted demo is a sample report, not a file-upload service.

## Try the demo

Open [`examples/demo.html`](https://github.com/R-Koda/eventscore-explorer/blob/main/examples/demo.html) in a browser after downloading the repository. All data is synthetic. At 0 seconds the demo has 2 matches, 3 false alarms and 2 misses. At 0.5 seconds it has 3 matches, 2 false alarms and 1 miss.

```sh
python3 -m venv .venv
. .venv/bin/activate
python -m pip install .
eventscore examples/truth.csv examples/predictions.csv --tolerances 0,0.5,1,2 --output reports/events.html --json reports/events.json
```

Without installing: prefix the same arguments with `PYTHONPATH=src python3 -m eventscore_explorer` instead of `eventscore`.

Python 3.10+. Runtime has no third-party dependencies.

## Input

Each CSV requires `id,start,end`; optional `label,recording` default to `event,default`. IDs must be unique within each input. Times are finite seconds with `0 <= start < end`. The two files must use the same time origin within each recording. Multiple recordings and labels are never matched across boundaries.

```csv
id,start,end,label,recording
T1,10,15,event,recording-1
```

## Exact scoring policy

- Intervals are half-open. At tolerance 0, only positive-duration overlap qualifies.
- At positive tolerance, disjoint or touching intervals qualify when their endpoint gap is at most that tolerance. This is **not** an onset-only collar.
- One truth and one prediction per match; maximum-cardinality bipartite matching maximizes matched count. Sorted traversal is deterministic; it does not optimize overlap or latency. Ambiguous matches are flagged.
- Precision = matches / predictions; recall = matches / truth; F1 = 2 × matches / (truth + predictions). Undefined denominators are reported as `null` / N/A.
- Onset offset = prediction start − truth start. Negative means early; it is not clipped into a positive detection delay.
- No prediction merging, point adjustment, label weighting, true-negative metrics or clinical scoring is applied. Recording duration is not supplied, so false alarms/hour is not computed.

Use the Python API: `from eventscore_explorer.core import Event, evaluate`.

## Scope and limits

Experimental 0.1. Input is capped at 2,000 events per file; matching can be expensive on dense graphs. Every requested tolerance is precomputed. Reports contain event IDs and times: review before publishing. Report files are never overwritten, and input CSVs cannot be output targets.

This tool complements [TimeEval](https://github.com/TimeEval/timeeval) and [affiliation metrics](https://github.com/ahstat/affiliation-metrics-py). It does not implement those metrics or claim equivalence. Its focus is explaining a simple, explicit matching policy.

## Development

```sh
PYTHONPATH=src python3 -m unittest discover -s tests -v
```

Tests cover non-greedy matching, endpoint rules, duplicate alarms, recording/label isolation, empty inputs, determinism, validation and safe HTML data embedding.

MIT licensed. Synthetic examples only; not a validated clinical evaluation standard.
