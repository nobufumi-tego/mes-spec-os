"""ENAA 実ファイルによる統合テスト

`reference/ENAA/mes_g25-029-2.xlsx` が配置されている場合のみ実行される
（未配置なら全テストが自動スキップ。public clone 直後や CI では走らない）。

目的：
- ENAA Excel の実レイアウトと cache.py の想定（シート名・列マッピング・
  バージョン抽出）が一致しているかの互換性検証
- ENAA が新版でレイアウトを変えたときに、ダミーテストでは検出できない
  破損をここで検出する

実行方法（リポジトリのルートで）:

    PYTHONIOENCODING=utf-8 uv run --with pytest --with openpyxl --no-project \
        python -m pytest tests/ -q

注意：テストは ENAA ファイルを読み取り専用で扱い、変更しない。
キャッシュ書き込み先は一時ディレクトリに差し替えるため、
outputs/.cache/ の実キャッシュにも影響しない。
"""
import os
import re
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'usecases', 'MES仕様書'))
import cache as cache_mod

REAL_XLSX = os.path.join(
    os.path.dirname(__file__), '..', 'reference', 'ENAA', 'mes_g25-029-2.xlsx'
)

pytestmark = pytest.mark.skipif(
    not os.path.exists(REAL_XLSX),
    reason='ENAA 実ファイル（reference/ENAA/mes_g25-029-2.xlsx）が未配置のためスキップ',
)


@pytest.fixture
def real_cache(tmp_path, monkeypatch):
    """実 Excel を読み、キャッシュ書き込みだけ一時ディレクトリへ逃がす"""
    monkeypatch.setattr(cache_mod, 'CACHE_FILE', str(tmp_path / 'enaa_full.json'))
    return cache_mod.get_cache(force_rebuild=True)


def test_excel_layout_is_readable(real_cache):
    """シート名・ヘッダ位置・列マッピングが実ファイルと一致している"""
    rows = real_cache['rows']
    # G25-029-2 (2025年9月版) は約 443 行。新版で大きく変わったら検知する
    assert 300 <= len(rows) <= 700, (
        f'行数が想定範囲外です（{len(rows)} 行）。'
        'ENAA 新版でレイアウトが変わった可能性があります'
    )


def test_version_extracted(real_cache):
    """B2 セルからバージョン日付が抽出できる"""
    version = real_cache['_meta']['version']
    assert version is not None, (
        'バージョンが抽出できません。B2 セルの表記形式が変わった可能性があります'
    )
    assert re.fullmatch(r'\d{4}-\d{2}-\d{2}', version)


def test_divisions_are_12(real_cache):
    """ENAA 12 大分類が揃っている（definition.md の対話フローの前提）"""
    divisions = {r['Division'] for r in real_cache['rows'] if r.get('Division')}
    assert len(divisions) == 12, (
        f'Division 数が 12 でなく {len(divisions)} です: {sorted(divisions)}'
    )
    # definition.md / サンプル出力が参照する中核 Division
    for expected in ('生産管理', '製造'):
        assert expected in divisions


def test_id_format(real_cache):
    """BP_ID が A-10-10-01 形式（R3/R4 レシピと get_by_id の前提）"""
    ids = [r['id'] for r in real_cache['rows'] if r.get('id')]
    assert ids, 'ID 列（col 2）が空です'
    pattern = re.compile(r'^[A-Z]-\d{2}-\d{2}-\d{2}$')
    matched = sum(1 for i in ids if pattern.match(i))
    assert matched / len(ids) >= 0.8, (
        f'ID 形式の一致率が低すぎます（{matched}/{len(ids)}）。列ずれの可能性があります'
    )


def test_mes_target_symbols_recognized(real_cache):
    """MES対象列の記号が 4 値分類（○△×※）で解釈できる"""
    counts = cache_mod.count_mes_targets(real_cache['rows'])
    assert counts['total'] == len(real_cache['rows'])
    recognized = counts['on'] + counts['partial'] + counts['off'] + counts['reference']
    assert recognized > 0, 'MES対象列（col 7）が 1 件も解釈できません。列ずれの可能性があります'
    # 未知記号が半数を超えたら記号体系が変わったとみなす
    assert counts['unknown'] <= counts['total'] / 2, (
        f'未知の MES対象記号が多すぎます: {counts}'
    )


def test_get_by_id_roundtrip(real_cache):
    """先頭行の ID で get_by_id が同じ行を返す"""
    first = next(r for r in real_cache['rows'] if r.get('id'))
    assert cache_mod.get_by_id(real_cache, first['id']) == first
