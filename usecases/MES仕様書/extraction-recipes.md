# ENAA Excel / PDF 抽出レシピ集

ENAA「MES/MOM 導入のための標準業務一覧」（G25-029 シリーズ）から、Claude が `/MES仕様書` 各 Stage で必要となる情報を取り出すための **Bash ワンライナー集**。

## 設計思想

3 層分離アーキテクチャの **Layer 2 (Query 層)** に相当：

```
Layer 3: Orchestrator    definition.md / commands/MES仕様書.md
              │
              │ 「Division=製造 の Sub BC を見せて」
              ▼
Layer 2: Query           本ファイル（extraction-recipes.md）
              │
              │ openpyxl / pypdf
              ▼
Layer 1: Read-only DB    reference/ENAA/*.xlsx, *.pdf
```

各レシピは Stage 毎に必要なものだけ呼び出す。
**v0.2 でメモリキャッシュ化を実装済み**（`cache.py`）。Excel は 1 度だけ読まれ、以降のレシピ呼び出しは JSON キャッシュから取得する（性能 ~3 倍）。

## 実行前提

- ENAA 5 資料が `reference/ENAA/` 直下に正しい名前で配置済み
  - 配置確認 → R0 を最初に実行
  - 不備があれば `core/rules.md` の「ENAA 資料の状態確認とフォールバック」へ
- `uv` が利用可能（依存パッケージは `--with` で都度取得）
- 本ファイルは現在のリポジトリ構造に合わせて `reference/ENAA/...` を使用
  - public 昇格時は `reference/ENAA/...` に置換

## 共通の実行パターン

すべてのレシピは以下の形：

```bash
PYTHONIOENCODING=utf-8 uv run --with <package> --no-project python -c "<script>"
```

- `PYTHONIOENCODING=utf-8` は Windows cp932 で ENAA Copyright 記号 (©) が出力エラーになる対策（必須）
- `--no-project` は親ディレクトリの `pyproject.toml` を無視（uv が無関係な依存を解決しないように）
- 出力は基本 JSON。Claude はそのまま `json.loads` 等で解釈

## v0.2 キャッシュ機構

Excel 系レシピ（R1-R5）は `cache.py` 経由でキャッシュ済みデータを使う：

```
1 回目の get_cache() 呼び出し:
  ENAA Excel を openpyxl で読む → outputs/.cache/enaa_full.json に保存

2 回目以降:
  Excel mtime が変わっていなければ JSON から即時ロード（~3 倍速）
  mtime が変わっていれば自動再構築
```

**キャッシュファイル**: `outputs/.cache/enaa_full.json`（gitignored、自動生成）
**自動無効化**: ENAA Excel の mtime と size を `_meta` に保存、次回呼び出し時に照合
**API**: `from cache import get_cache, filter_by_division, filter_by_subbc, get_by_id, has_custom_data, get_custom_rows`

レシピは `usecases/MES仕様書` を sys.path に追加してから cache.py をインポートする前提。

---

## R0: 配置確認 + バージョン取得

**用途**: `/MES仕様書` または `2) ENAA 資料の確認` の起動直後、ENAA 5 資料が揃っているかと、どのバージョンかを確認する。

**前提**: なし（このレシピが最初に走る）

**コマンド**:

```bash
PYTHONIOENCODING=utf-8 uv run --with openpyxl --no-project python -c "
import sys, os, json
sys.path.insert(0, 'usecases/MES仕様書')
ENAA = 'reference/ENAA'
expected = ['mes_g25-029-1.pdf','mes_g25-029-2.xlsx','mes_g25-029-3.pdf','mes_g25-029-4.pdf','mes_g25-029-5.pdf']
present = {f: os.path.exists(f'{ENAA}/{f}') for f in expected}
all_ok = all(present.values())
version = None
if present['mes_g25-029-2.xlsx']:
    from cache import get_cache
    cache = get_cache()  # 初回ならここでキャッシュ構築、以降ヒット
    version = cache['_meta'].get('version')
print(json.dumps({'configured': all_ok, 'present': present, 'version': version}, ensure_ascii=False, indent=2))
"
```

**出力例**:

```json
{
  "configured": true,
  "present": {
    "mes_g25-029-1.pdf": true,
    "mes_g25-029-2.xlsx": true,
    "mes_g25-029-3.pdf": true,
    "mes_g25-029-4.pdf": true,
    "mes_g25-029-5.pdf": true
  },
  "version": "2025-09-01"
}
```

**失敗時**: `configured: false` の場合、`core/rules.md` 「ENAA 資料の状態確認とフォールバック」フローへ。`version` が `null` の場合は Excel の発行日表記が変わった可能性 → ENAA 公式サイトで確認。

---

## R1: 全 Division × Business Category × MES 対象比率の動的抽出

**用途**: Stage 0 の構造把握 / Stage 1 で 12 大分類を MES 対象比率順に並べて利用者に提示する。

**前提**: R0 が `configured: true` を返している。

**コマンド**（v0.2.1〜：MES対象記号 4 値対応）:

```bash
PYTHONIOENCODING=utf-8 uv run --with openpyxl --no-project python -c "
import sys, json
sys.path.insert(0, 'usecases/MES仕様書')
from cache import get_cache, classify_mes_target
from collections import OrderedDict
cache = get_cache()
divs = OrderedDict()
for row in cache['rows']:
    div = row['Division']
    d = divs.setdefault(div, {'total': 0, 'on': 0, 'partial': 0, 'off': 0, 'reference': 0, 'BCs': OrderedDict()})
    d['total'] += 1
    cat = classify_mes_target(row.get('MES対象'))
    if cat in d: d[cat] += 1
    bc = row.get('BC')
    if bc:
        bcd = d['BCs'].setdefault(bc, {'total': 0, 'on': 0, 'partial': 0, 'off': 0, 'reference': 0})
        bcd['total'] += 1
        if cat in bcd: bcd[cat] += 1
print(json.dumps(divs, ensure_ascii=False, indent=2))
"
```

**出力例**（一部抜粋）:

```json
{
  "生産管理": {
    "total": 30,
    "on": 13,
    "partial": 0,
    "off": 16,
    "reference": 0,
    "BCs": { ... }
  },
  "製造": {
    "total": 78,
    "on": 78,
    "partial": 0,
    "off": 0,
    "reference": 0,
    "BCs": { ... }
  }
}
```

**ENAA MES対象記号 4 値の意味**（出典: ENAA G25-029-1 P9-10 表 3-2）:

| キー | ENAA 記号 | 意味 |
|---|:---:|---|
| `on` | ○ | MES/MOM で対応可能（必須対象） |
| `partial` | △ | 対象の場合あり（任意） |
| `off` | × | MES では対象としない |
| `reference` | ※ | 別 Division で記載（重複参照） |

**MES 対象比率順**: Claude は `(on + partial * 0.5) / total` で重み付けソートし、「中核（70% 以上）→ 中間（30-70%）→ 周辺（30% 未満）」のグループ分けを行う。partial を 0.5 重みで含めるのは、△ も部分的に MES 対象であるため。

---

## R2: 特定 Division の Business Category × Sub Business Category 階層

**用途**: Stage 1 で利用者がある Division を「必須」「任意」と回答した際、その配下の BC × SubBC を一覧表示して深掘り対話を始める。

**前提**: R1 で当該 Division 名が確認できている。

**コマンド**:

```bash
TARGET_DIV="製造"  # ← 利用者の回答に応じて変える
PYTHONIOENCODING=utf-8 uv run --with openpyxl --no-project python -c "
import sys, os, json
sys.path.insert(0, 'usecases/MES仕様書')
from cache import get_cache, filter_by_division
from collections import OrderedDict
cache = get_cache()
target = os.environ['TARGET_DIV']
out = OrderedDict()
for row in filter_by_division(cache, target):
    bc, sbc = row.get('BC'), row.get('SubBC')
    if bc and sbc:
        out.setdefault(bc, [])
        if sbc not in out[bc]:
            out[bc].append(sbc)
print(json.dumps(out, ensure_ascii=False, indent=2))
"
```

**出力例** (`TARGET_DIV=製造`):

```json
{
  "製造準備": ["製造指図受領・確認", "差立/ディスパッチング", "作業指示確認"],
  "製造実行": ["チェックリスト確認・実行", "部材投入", "製造実施", "工程内検査"],
  "製造完了品対応": ["製造実績報告", "設備稼働報告", "品質実績報告", "後段取"],
  "工程間搬送": ["半製品（中間品）対応", "製品・完成品対応"],
  "工程進捗管理": ["工程進捗管理"]
}
```

**注意**: Sub Business Category 名にはまれに改行が含まれる（例 `治工具準備\n(含む型/切削工具/検査工具)`）。Claude は表示時に整形する。

---

## R3: 特定 Sub Business Category の Business Process 詳細

**用途**: Stage 1〜2 で利用者がある Sub BC を選び、その配下の個々の業務プロセス（業務オペレーション・補足込み）を確認したいとき。

**前提**: R2 で当該 SubBC 名が確認できている。

**コマンド**:

```bash
TARGET_SBC="製造実施"  # ← 利用者の選択に応じて変える
PYTHONIOENCODING=utf-8 uv run --with openpyxl --no-project python -c "
import sys, os, json
sys.path.insert(0, 'usecases/MES仕様書')
from cache import get_cache, filter_by_subbc
cache = get_cache()
target = os.environ['TARGET_SBC']
out = []
for row in filter_by_subbc(cache, target):
    out.append({
        'id': row.get('id'),
        'Division': row.get('Division'),
        'BC': row.get('BC'),
        'BP': row.get('BP'),
        'MES対象': row.get('MES対象'),
        '業務オペレーション': row.get('業務オペレーション'),
        '補足': row.get('補足'),
    })
print(json.dumps(out, ensure_ascii=False, indent=2))
"
```

**出力例** (`TARGET_SBC=製造実施`): 6 件の Business Process 行が返る。各々に id, Division, BC, BP 名, MES対象フラグ, 業務オペレーション説明, 補足が含まれる。

**注意**: 同名の SubBC が複数 Division に存在する可能性があるため、出力には Division / BC を含めて Claude が表示時に文脈を示す。

---

## R4: 特定 Business Process ID の代替可能システム情報

**用途**: Stage 2 で「この機能は既存システム何でカバーできるか」の照合が必要になったとき。

**前提**: R3 で BP_ID（例 `B-30-30-01`）を取得済み。

**コマンド**:

```bash
TARGET_ID="B-30-30-01"  # ← 利用者が深掘りしたい BP の ID
PYTHONIOENCODING=utf-8 uv run --with openpyxl --no-project python -c "
import sys, os, json
sys.path.insert(0, 'usecases/MES仕様書')
from cache import get_cache, get_by_id
cache = get_cache()
target = os.environ['TARGET_ID']
row = get_by_id(cache, target)
result = None
if row:
    result = {
        'id': target,
        'Division': row.get('Division'),
        'BC': row.get('BC'),
        'SubBC': row.get('SubBC'),
        'BP': row.get('BP'),
        'MES対象': row.get('MES対象'),
        '代替可能システム': row.get('代替可能システム'),
        'ERP': row.get('ERP'),
        'PLM': row.get('PLM'),
        'スケジューラー': row.get('スケジューラー'),
        'コントロールシステム': row.get('コントロールシステム'),
        'その他システム': row.get('その他システム'),
    }
print(json.dumps(result, ensure_ascii=False, indent=2))
"
```

**出力例**:

```json
{
  "id": "B-30-30-01",
  "Division": "製造",
  "BC": "製造実行",
  "SubBC": "製造実施",
  "BP": "製造着手",
  "MES対象": "〇",
  "代替可能システム": "ERP",
  "ERP": null,
  "PLM": null,
  "スケジューラー": null,
  "コントロールシステム": "I:/O:製造開始データ",
  "その他システム": null
}
```

**読み方**: 各システム列の `I:` は Input、`O:` は Output、`I/O:` は双方向のサンプルデータ。null は ENAA が代替不可と判断した（または未記載の）箇所。

---

## R5: P 列以降の利用者カスタム書き込み読み取り

**用途**: 利用者が ENAA Excel の P 列以降（列 16 以降）に自社情報（担当部門・該当業務有無・現状・課題・To-Be 等）を書き込んでいる場合、それを読み取って Stage 1〜2 の対話に流用する。

**前提**:

- ENAA Quick Start (G25-029-3 p13) は P 列以降に「担当部門名 / 該当業務あり○・なし× / 現業務媒体 / 現状業務 / 現状課題 / 改善・実現したいこと（To-Be）」を追加することを推奨
- 初期状態では空（max_column=16 で P 列は空）。利用者が手動で書き込むまで何も返らない

**コマンド**:

```bash
PYTHONIOENCODING=utf-8 uv run --with openpyxl --no-project python -c "
import sys, json
sys.path.insert(0, 'usecases/MES仕様書')
from cache import get_cache, has_custom_data, get_custom_rows
cache = get_cache()
custom_rows = get_custom_rows(cache)
headers = set()
rows_out = []
for row in custom_rows:
    custom = row.get('_custom', {})
    headers.update(custom.keys())
    rows_out.append({'id': row.get('id'), **custom})
print(json.dumps({
    'has_custom_data': has_custom_data(cache),
    'headers': sorted(headers),
    'rows': rows_out,
}, ensure_ascii=False, indent=2))
"
```

**出力例**（利用者がまだ何も書き込んでいない場合）:

```json
{
  "has_custom_data": false,
  "headers": [],
  "rows": []
}
```

**書き込み済みの場合**: `has_custom_data: true` となり、`headers` に利用者が定義した列名、`rows` に各行のデータが入る。

**Claude の振る舞い**: `has_custom_data: true` なら「Excel に既に書き込みがありますが、引き継いで対話を続けますか？それともゼロから始めますか？」と確認。

---

## R6: PDF からのキーワード検索（解説資料 / How to Use 共通）

**用途**:

- 用語確認（例「ISA-95」「MOM」「MESA」が ENAA 資料でどう定義されているか）
- 利用者が「ENAA は ◯◯ をどう扱っている？」と聞いてきたときの根拠探し
- ISA-95 / IEC 62264 等の業界標準への言及箇所の特定

**前提**: 対象 PDF が `reference/ENAA/` に配置済み。

**コマンド**:

```bash
TARGET_PDF="reference/ENAA/mes_g25-029-1.pdf"  # 解説資料 / How to Use を指定
KEYWORD="ISA"
PYTHONIOENCODING=utf-8 uv run --with pypdf --no-project python -c "
import os, json
from pypdf import PdfReader
target_pdf = os.environ['TARGET_PDF']
keyword = os.environ['KEYWORD']
r = PdfReader(target_pdf)
hits = []
for i, pg in enumerate(r.pages, 1):
    txt = pg.extract_text() or ''
    if keyword in txt:
        idx = txt.find(keyword)
        excerpt = txt[max(0,idx-60):idx+200].replace(chr(10), ' / ')
        hits.append({'page': i, 'excerpt': excerpt})
print(json.dumps({'pdf': os.path.basename(target_pdf), 'keyword': keyword, 'hits': hits}, ensure_ascii=False, indent=2))
"
```

**出力例** (`TARGET_PDF=...g25-029-1.pdf`, `KEYWORD=ISA`):

```json
{
  "pdf": "mes_g25-029-1.pdf",
  "keyword": "ISA",
  "hits": [
    {"page": 2, "excerpt": "...ISA-95, IEC 62264, ISO 22400 等..."},
    {"page": 11, "excerpt": "...コントロールシステムは所謂 ISA95 の Level2 領域を想定..."},
    {"page": 20, "excerpt": "...12 品質管理 L2 / ISA-95 のレベル 2 層に該当し..."}
  ]
}
```

**よく使うキーワード例**: `ISA`, `MES`, `MOM`, `MESA`, `IEC 62264`, `Level 2`, `星取`, `ROI`, `カーナビ`（3 効果軸の説明用）

**注意**: pypdf のテキスト抽出は完璧でなく、表組み・図中文字は欠落することがある。重要な引用は実際の PDF を確認するよう Claude が促す。

### R6 の用語集向け活用パターン

ENAA 用語集（G25-029-1 P20-22）には 38 用語が Division 別に整理されている。
利用者から「◯◯ ってどういう意味？」「ENAA は ◯◯ をどう定義している？」と聞かれた場合：

1. `TARGET_PDF=reference/ENAA/mes_g25-029-1.pdf` を指定
2. `KEYWORD=<用語名>` で R6 を実行
3. 多くの用語は P20〜P22 にヒットする（用語集本体）。本文中に出てくる用語は別ページに散らばる

**用語集に含まれる主な用語**（38 用語、開発時の確認用）:
- 生産管理: 製造指図, MBOM, BOP, BOE
- 製造: 工程展開, ディスパッチング, バックフラッシュ, CAPA, リワーク・リペア
- 品質管理: QMS, **L2（ISA-95 関連）**, SPC
- 在庫管理: WMS, EDI, ASN, VMI, WCS, AMR ほか
- 保全: PLM, CMMS, **SCADA**, **DCS**, OEE
- HSE: HSE, カーボンフットプリント
- 品質保証: トレースバック, トレースフォワード
- 生産技術: SOP, FMEA, Control Plan
- 設計: EBOM
- 購買・資材: MRP

開発時は `usecases/MES仕様書/ENAA-用語集.md`（private 限定）に即時参照可能な完全リストあり。
public モードでは本レシピ R6 で都度 PDF 直読する。

---

## レシピの拡張ガイドライン

新規レシピを追加する際は：

1. **目的・前提・コマンド・出力例・失敗時** の 5 点セットで記述
2. 命名規則: `R<番号>` で連番。意味のある略称は併記可（例 `R7_term_lookup`）
3. **ステートレス原則**: 1 コマンドで完結、外部状態に依存しない
4. **JSON 出力**: Claude がパースしやすい形に。先頭に `print(json.dumps(...))` 一発
5. **Path**: `reference/ENAA/...` を使用（public 昇格時は置換）
6. **エンコーディング**: `PYTHONIOENCODING=utf-8` を必ず付ける

## v0.2 実装済み

- ✅ **メモリキャッシュ**: `cache.py` 経由で Excel 1 度読み + JSON 永続キャッシュ。Excel mtime 自動無効化。R1-R5 全レシピで利用済み
- ✅ **キャッシュ自動無効化**: ENAA Excel の mtime + size を `_meta` に記録、変更検出で自動再構築

## v0.3 以降で検討するもの

- **Excel 書き込みレシピ**: 利用者カスタム列（P 列以降）への書き込み（現在は読み取りのみ）。openpyxl の write モードで実装。書き込み後はキャッシュも自動再構築
- **差分検出**: ENAA 新版が来たときに、旧版キャッシュとの差分（カラム変更・行追加・削除）を検出して報告
- **業務機能関連図のテキスト化**: G25-029-1 解説資料 P7-11 の図表は pypdf では拾えないため、別アプローチ（OCR / 画像抽出 + LLM 解析等）を検討
- **PDF キャッシュ**: 現在 R6 は PDF を毎回再読み込み。pypdf でテキスト抽出した結果を JSON にキャッシュすれば高速化可能（ただし PDF テキスト抽出自体が ~1 秒なので優先度は低い）

## 出典

本レシピは以下の ENAA 資料の構造に依存します：

- 一般財団法人エンジニアリング協会(ENAA)
  「MES/MOM 導入のための標準業務一覧」(G25-029-1〜5, 2025 年 9 月正式版)
- 公式サイト: https://www.enaa.or.jp/research/smart/mes

Excel のシート名・カラム順が将来変更された場合、本レシピの修正が必要となる可能性があります。
