#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Génère tsume.json à partir des fichiers KIF.
Lance depuis le terminal :
  python3 generate_tsume_json.py
"""

import re
import json
from pathlib import Path

# ── Configuration ──────────────────────────────────────────────────────────
KIF_DIR   = Path("/Users/fabienloi/Downloads/tsume/8K Tsume Problems/")
OUTPUT    = Path.home() / "Library/Mobile Documents/iCloud~dk~simonbs~Scriptable/Documents/tsume.json"
OUTPUT_3  = Path.home() / "Library/Mobile Documents/iCloud~dk~simonbs~Scriptable/Documents/tsume_3.json"

# ── Tables de correspondance ───────────────────────────────────────────────
KANJI_NUM = {
    '一': 1, '二': 2, '三': 3, '四': 4, '五': 5,
    '六': 6, '七': 7, '八': 8, '九': 9, '十': 10,
    '十一': 11, '十二': 12, '十三': 13, '十四': 14,
    '十五': 15, '十六': 16, '十七': 17, '十八': 18,
}

COL_NUM = {'１': 1, '２': 2, '３': 3, '４': 4, '５': 5,
           '６': 6, '７': 7, '８': 8, '９': 9}
ROW_IDX = {'一': 0, '二': 1, '三': 2, '四': 3, '五': 4,
           '六': 5, '七': 6, '八': 7, '九': 8}

PIECE_NAMES = {
    '歩': 'fu',   '香': 'kyou', '桂': 'kei',  '銀': 'gin',
    '金': 'kin',  '角': 'kaku', '飛': 'hi',   '玉': 'gyoku', '王': 'gyoku',
    'と': 'to',   '馬': 'uma',  '龍': 'ryuu', '竜': 'ryuu',
    '成香': 'nkyou', '成桂': 'nkei', '成銀': 'ngin',
}

PIECE_TO_SVG = {
    'fu': 'FU', 'kyou': 'KY', 'kei': 'KE', 'gin': 'GI',
    'kin': 'KI', 'kaku': 'KA', 'hi': 'HI', 'gyoku': 'OU',
    'to': 'TO', 'nkyou': 'NY', 'nkei': 'NK', 'ngin': 'NG',
    'uma': 'UM', 'ryuu': 'RY',
}

STOP_WORDS = ('投了', '中断', '詰み', '千日手', '持将棋')

PATTERN_FROM = re.compile(r'\s*(\d+)\s+(.*?)\((\d{2})\)\s*\(')
PATTERN_DROP = re.compile(r'\s*(\d+)\s+(\S+)\s*\(')
PATTERN_HENKO = re.compile(r'\s*変化：(\d+)手')


# ── Parsers ────────────────────────────────────────────────────────────────

def parse_hand(hand_str):
    hand_str = hand_str.strip()
    if hand_str in ('なし', ''):
        return {}
    result = {}
    chars = hand_str.replace('　', ' ')
    tokens = re.findall(r'(成[香桂銀]|[歩香桂銀金角飛玉王とぼ馬龍竜])([一二三四五六七八九十]+)?', chars)
    for piece_k, num_k in tokens:
        if piece_k in PIECE_NAMES:
            count = KANJI_NUM.get(num_k, 1) if num_k else 1
            result[PIECE_NAMES[piece_k]] = count
    return result


def parse_board(lines):
    board = [[None] * 9 for _ in range(9)]
    for row_idx, line in enumerate(lines):
        chars = list(line)
        inner = chars[1:]
        lp = len(inner) - 1
        while lp >= 0 and inner[lp] != '|':
            lp -= 1
        inner = inner[:lp]
        for col_idx in range(9):
            cell = inner[col_idx * 2: col_idx * 2 + 2]
            if len(cell) < 2:
                continue
            gote = (cell[0] == 'v')
            piece_char = cell[1]
            if piece_char and piece_char != '・':
                board[row_idx][col_idx] = {
                    'piece': PIECE_NAMES.get(piece_char, piece_char),
                    'svg': ('1' if gote else '0') + PIECE_TO_SVG.get(PIECE_NAMES.get(piece_char, ''), '??'),
                    'player': 'gote' if gote else 'sente',
                }
    return board


def bounding_box(board, moves=None):
    rows, cols = [], []
    for r in range(9):
        for c in range(9):
            if board[r][c]:
                rows.append(r)
                cols.append(c)
    # Include move origin and destination squares
    for m in (moves or []):
        if m.get('from_row', -1) >= 0:
            rows.append(m['from_row'])
            cols.append(m['from_col'])
        label = m.get('move', '')
        if len(label) >= 2 and label[0] in COL_NUM and label[1] in ROW_IDX:
            rows.append(ROW_IDX[label[1]])
            cols.append(9 - COL_NUM[label[0]])
    if not rows:
        return 0, 8, 0, 8
    return max(0, min(rows)-1), min(8, max(rows)+1), max(0, min(cols)-1), min(8, max(cols)+1)


def parse_section(lines, expected_start=1):
    """Parse une séquence de coups KIF à partir du numéro expected_start."""
    moves = []
    expected = expected_start
    for line in lines:
        if any(w in line for w in STOP_WORDS):
            break
        m = PATTERN_FROM.match(line)
        if m:
            num = int(m.group(1))
            if num != expected:
                break
            from_coord = m.group(3)
            moves.append({
                'num': num,
                'move': m.group(2).strip(),
                'from_col': 9 - int(from_coord[0]),
                'from_row': int(from_coord[1]) - 1,
            })
            expected += 1
        else:
            m2 = PATTERN_DROP.match(line)
            if m2:
                num = int(m2.group(1))
                if num != expected:
                    break
                moves.append({'num': num, 'move': m2.group(2).strip(), 'from_col': -1, 'from_row': -1})
                expected += 1
    return moves


def parse_moves(move_lines):
    """
    Parse la ligne principale et toutes les variantes (変化：N手).
    Retourne (main_moves, variants) où variants est une liste de
    {'from_move': int, 'moves': [...]} .
    """
    # Découper en sections : première = ligne principale, suivantes = variantes
    sections = []
    current_start = 1
    current_lines = []

    for line in move_lines:
        hm = PATTERN_HENKO.match(line)
        if hm:
            sections.append((current_start, current_lines[:]))
            current_start = int(hm.group(1))
            current_lines = []
        else:
            current_lines.append(line)
    sections.append((current_start, current_lines))

    main_moves = parse_section(sections[0][1], expected_start=1) if sections else []

    variants = []
    for start_num, lines in sections[1:]:
        vmoves = parse_section(lines, expected_start=start_num)
        if vmoves:
            variants.append({'from_move': start_num, 'moves': vmoves})

    return main_moves, variants


def is_valid(data):
    """Un tsume valide a un nombre impair de coups ≥ 1."""
    n = len(data['moves'])
    return n > 0 and n % 2 == 1


# ── Parser KIF ─────────────────────────────────────────────────────────────

def parse_kif(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8-sig') as f:
            content = f.read()
    except UnicodeDecodeError:
        with open(filepath, 'r', encoding='shift-jis') as f:
            content = f.read()

    lines = content.replace('\r\n', '\n').replace('\r', '\n').split('\n')

    data = {
        'filename': filepath.name,
        'sente_hand': {}, 'gote_hand': {},
        'board': [], 'moves': [], 'variants': [],
        'author': '', 'source': '', 'bbox': {},
    }

    board_lines, move_lines = [], []
    move_section = False

    for line in lines:
        if line.startswith('後手の持駒：'):
            data['gote_hand'] = parse_hand(line[len('後手の持駒：'):])
        elif line.startswith('先手の持駒：'):
            data['sente_hand'] = parse_hand(line[len('先手の持駒：'):])
        elif line.startswith('*作者：'):
            data['author'] = line[4:].strip()
        elif line.startswith('*発表誌：'):
            data['source'] = line[5:].strip()
        elif line.startswith('|'):
            board_lines.append(line)
        elif line.startswith('手数----'):
            move_section = True
        elif move_section and (re.match(r'\s*\d+', line) or PATTERN_HENKO.match(line)):
            move_lines.append(line)

    main_moves, variants = parse_moves(move_lines)
    data['moves'] = main_moves

    if len(board_lines) == 9:
        board = parse_board(board_lines)
        data['board'] = board
        min_r, max_r, min_c, max_c = bounding_box(board, main_moves)
        data['bbox'] = {'min_row': min_r, 'max_row': max_r, 'min_col': min_c, 'max_col': max_c}
    if variants:
        data['variants'] = variants

    return data


# ── Main ───────────────────────────────────────────────────────────────────

def main():
    kif_files = sorted(KIF_DIR.rglob("*.kif"), key=lambda p: (p.parent.name, p.name))
    total = len(kif_files)

    if total == 0:
        print(f"❌ Aucun fichier .kif trouvé dans {KIF_DIR}")
        return

    print(f"📂 {total} fichiers KIF trouvés")
    print(f"📄 Sortie : {OUTPUT}")
    print()

    tsume_list, skipped, errors = [], 0, []

    for i, kif_path in enumerate(kif_files, 1):
        try:
            data = parse_kif(kif_path)
            if not is_valid(data):
                skipped += 1
                continue
            tsume_list.append(data)
            if i % 100 == 0:
                print(f"  {i}/{total}…")
        except Exception as e:
            errors.append((kif_path.name, str(e)))
            print(f"  ⚠️  {kif_path.name} : {e}")

    # Trier par nombre de coups (ordre stable à l'intérieur de chaque groupe)
    tsume_list.sort(key=lambda t: len(t['moves']))
    for i, t in enumerate(tsume_list, 1):
        t['id'] = i

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT, 'w', encoding='utf-8') as f:
        json.dump(tsume_list, f, ensure_ascii=False, separators=(',', ':'))

    pool_3 = [t for t in tsume_list if len(t['moves']) == 3]
    with open(OUTPUT_3, 'w', encoding='utf-8') as f:
        json.dump(pool_3, f, ensure_ascii=False, separators=(',', ':'))

    total_variants = sum(len(t.get('variants', [])) for t in tsume_list)
    size_mb = OUTPUT.stat().st_size / 1_000_000
    size_3_mb = OUTPUT_3.stat().st_size / 1_000_000
    print()
    print(f"✅ {len(tsume_list)} tsume exportés ({total_variants} variantes)")
    if skipped:
        print(f"🚫 {skipped} problèmes invalides ignorés")
    print(f"📦 tsume.json   : {size_mb:.1f} Mo")
    print(f"📦 tsume_3.json : {size_3_mb:.1f} Mo  ({len(pool_3)} problèmes en 3手)")
    if errors:
        print(f"⚠️  {len(errors)} erreurs :")
        for name, err in errors:
            print(f"   {name} : {err}")


if __name__ == '__main__':
    main()
