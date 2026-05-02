# mes-spec-os（v0.2.0 / 構想段階）

製造業の MES / MOM 導入を計画する人向け、[ENAA「MES/MOM 導入のための標準業務一覧」](https://www.enaa.or.jp/research/smart/mes)（2025 年 9 月正式版）を活用した仕様書・RFP 一次稿作成スターター。

> ⚠️ **本リポジトリは構想段階（v0.2.0）です。** 実運用には自社環境での検証が必要であり、出力は **「下書きのたたき台」** として扱ってください。
>
> **再配布リスクを避けるため、ENAA 資料そのものは本リポジトリに含まれません。** 利用者が ENAA 公式サイトから直接ダウンロードして `reference/ENAA/` に配置してください。出力には ENAA 著作権表示が自動で付記されます。
>
> ライセンス: **MIT**（本リポのソース・ドキュメントのみ。ENAA 資料は ENAA 利用条件に従う）。詳細は [LICENSE](LICENSE) を参照。

## ⚠️ 利用前に必ずお読みください

本スターターは Claude Code（クラウド型 AI 対話ツール）を介して動作します。
**製造業の MES 検討では機密性の高い情報（顧客名・取引条件・ライン構成・原価情報等）を扱うため、**
**情シス・法務担当者と一緒に [docs/セキュリティ.md](docs/セキュリティ.md) を確認してから利用してください。**

主な要点（詳細は上記ドキュメント）：

- 利用者が Claude に渡した情報は Anthropic 社（米国）の API に送信されます
- 推奨プラン：Claude Team / Enterprise（データ学習なし、企業管理機能あり）
- 顧客名・型番・原価などは Claude に渡す前に **必ず伏せ字化**
- 本スターターは **ローカル運用前提**（GitHub 等 public への push 禁止）
- 社内ルール・取引先のセキュリティ要件（IATF 16949 等）に抵触しないか事前確認

> **本リポジトリは構想段階の v0.1 骨格です。** 実用には ENAA 資料の取り込み・対話フローの作り込み・検証が必要です。
>
> **再配布リスクを避けるため、ENAA 資料そのものは本リポジトリに含まれません。** 利用者が ENAA 公式サイトから直接ダウンロードして `reference/ENAA/` に配置してください。

## 対象ユーザー

- 製造IT 担当者 / SIer / MES ベンダーのコンサル / 工場 DX 推進責任者
- ENAA G25-029 シリーズを使って MES 仕様書 / RFP 一次稿を組み立てたい人
- ディスクリート系（組立加工系）工場が対象（プロセス系・バッチ系は射程外）

## 必要なもの

- Windows 11 + PowerShell（Claude Code が動く環境）
- Claude Code（インストール手順は別スターター `business-os` の `docs/インストール.md` を参照）
- **ENAA「MES/MOM 導入のための標準業務一覧」5 ファイル**
  - 取得方法・配置先は [reference/ENAA/README.md](reference/ENAA/README.md) を参照

## 使い方（最短）

1. このフォルダに `cd` する
2. `reference/ENAA/README.md` の手順で ENAA 5 資料をダウンロード・配置（5 分程度）
3. PowerShell で `claude` を起動
4. 起動後、「**こんにちは。**」と打って Enter（最後の句点まで打つのがコツ）
5. メニューから `1) MES 仕様書を作る` を選ぶ
6. 案件情報・現状・要件を 1 問 1 答で入力
7. `outputs/MES仕様書/<日付>_<案件名>.yaml` と `.md` が生成される

## 何ができるか

| コマンド | 用途 |
|---|---|
| `/MES仕様書` | ENAA 12 大分類で対話して仕様書 / RFP 一次稿を組み立てる |

（v0.1 では他コマンド未実装）

## ディレクトリ構成

| 場所 | 内容 |
|---|---|
| `core/rules.md` | 振る舞いルール（業務改善OS から継承＋ ENAA 著作権仕様） |
| `usecases/MES仕様書/` | MES 仕様書ユースケースの定義 |
| `.claude/commands/MES仕様書.md` | スラッシュコマンド本体 |
| `reference/ENAA/` | ENAA 標準業務一覧の置き場（**利用者が手動配置**） |
| `inputs/` | 自社の機密データ（ローカル限定、`.gitignore` 済み） |
| `outputs/` | 生成された仕様書 |

## 著作権

ENAA 資料を活用した出力には ENAA 出典が末尾に**自動で付記されます**（CLAUDE.md / core/rules.md で強制）。
これは ENAA の利用条件（著作権表示必須）に基づく仕様で、削除しないでください。

## サポートと自己解決

本プロジェクトは個人運営のオープンソースプロジェクトです。**サポートは「ドキュメント参照 → Claude に質問 → GitHub Issues（best-effort）」の自己解決ベース** で、個別の技術サポート・ZOOM ミーティング・電話対応は行っておりません。

詳細は [SUPPORT.md](SUPPORT.md) を必ずお読みください。

## このあと

- **【利用前必読】セキュリティと情報漏洩対策** → [docs/セキュリティ.md](docs/セキュリティ.md)
- **【利用前必読】サポート方針（個別対応なし）** → [SUPPORT.md](SUPPORT.md)
- ENAA 資料を取得 → [reference/ENAA/README.md](reference/ENAA/README.md)
- 対話の作法 → [core/rules.md](core/rules.md)
- 仕様書ユースケースの中身 → [usecases/MES仕様書/definition.md](usecases/MES仕様書/definition.md)
