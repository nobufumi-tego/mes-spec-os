# CHANGELOG

本リポジトリの変更履歴。バージョンは README.md タイトルの表記と一致させる。

## v0.2.2 (2026-07-26)

### セキュリティ強化

- `.claude/settings.json` を追加：`git push` / `git remote add` / `inputs/`・`reference/ENAA/` の `git add` を permissions で機械的に拒否（従来は CLAUDE.md の指示文のみで強制力がなかった）
- clone 後に `git remote remove origin` を実行する手順を README / docs/インストール.md に追加（outputs/ の仕様書が誤 push で公開される事故の防止）

### 機能追加

- `/保存` コマンドを追加（機密混入チェック付きのローカル Git 保存。CLAUDE.md から案内していたが実体が未実装だった）
- `doctor.ps1` を追加（必要ツール・ENAA 5 資料の配置・リモート設定を一括診断）
- 中断案件の再開フローを Stage 0 に定義（`outputs/MES仕様書/` の既存 YAML を検出して続きから再開）
- ENAA Excel（G25-029-2）の中身識別を追加（シート名による判定。従来はファイル数による推定のみ）

### 品質

- `tests/test_cache.py` を追加（cache.py の単体テスト 9 件。ENAA 実ファイル不要のダミー Excel フィクスチャ方式）
- CHANGELOG.md 新設

### ドキュメント整理

- README の v0.1 時代の残骸（重複した注意書き・「他コマンド未実装」）を除去
- インストール導線を自リポジトリの docs/インストール.md に統一（business-os 参照を解消）
- definition.md の残課題を実装状況と同期（メモリキャッシュ・サンプル outputs は完了済みへ移動、重複項目を統合）
- CLAUDE.md の ENAA 状態確認フローの記述を core/rules.md への参照に一本化

## v0.2.1 (2026-05-03)

- ENAA 概念（フェーズ区分 / MES 対象 4 値 / 代替可能システム 13 種 / 3 効果軸 / カーナビメタファ等）を雛形対話に統合
- ENAA 問合せ先を公式ページへの参照に簡素化

## v0.2.0 (2026-05-02)

- 初回公開（private 開発版から ENAA 再配布に当たる部分を除去して public 化）
- `/MES仕様書` コマンド（Stage 0〜4 の対話フロー）
- cache.py による ENAA Excel の JSON キャッシュ機構
- 初心者向け 3 文書（5分で試す / インストール / 困ったとき）
- ENAA ダウンロード URL を `?fname=` 形式に修正（直リンク 403 対策）
