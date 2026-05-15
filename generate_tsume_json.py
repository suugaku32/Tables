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
KIF_DIR    = Path("/Users/fabienloi/Downloads/tsume/8K Tsume Problems/")
OUTPUT     = Path.home() / "Library/Mobile Documents/iCloud~dk~simonbs~Scriptable/Documents/tsume.json"

# ── Tables de correspondance ───────────────────────────────────────────────
KANJI_NUM = {
    '一': 1, '二': 2, '三': 3, '四': 4, '五': 5,
    '六': 6, '七': 7, '八': 8, '九': 9, '十': 10,
    '十一': 11, '十二': 12, '十三': 13, '十四': 14,
    '十五': 15, '十六': 16, '十七': 17, '十八': 18,
}

PIECE_NAMES = {
    '歩': 'fu',   '香': 'kyou', '桂': 'kei',  '銀': 'gin',
    '金': 'kin',  '角': 'kaku', '飛': 'hi',   '玉': 'gyoku', '王': 'gyoku',
    'と': 'to',   '馬': 'uma',  '龍': 'ryuu', '竜': 'ryuu',
    '成香': 'nkyou', '成桂': 'nkei', '成銀': 'ngin',
}

# Correspondance piece_id → code fichier SVG
PIECE_TO_SVG = {
    'fu':    'FU', 'kyou': 'KY', 'kei':   'KE', 'gin':  'GI',
    'kin':   'KI', 'kaku': 'KA', 'hi':    'HI', 'gyoku':'OU',
    'to':    'TO', 'nkyou':'NY', 'nkei':  'NK', 'ngin': 'NG',
    'uma':   'UM', 'ryuu': 'RY',
}

# Marqueurs de fin de partie invalides
STOP_WORDS = ('投了', '中断', '詰み', '千日手', '持将棋')


def parse_hand(hand_str):
    hand_str = hand_str.strip()
    if hand_str in ('なし', ''):
        return {}
    result = {}
    chars = hand_str.replace('　', ' ').replace('　', ' ')
    tokens = re.findall(r'(成[香桂銀]|[歩香桂銀金角飛玉王とぼ馬龍竜])([一二三四五六七八九十]+)?', chars)
    for piece_k, num_k in tokens:
        if piece_k in PIECE_NAMES:
            count = KANJI_NUM.get(num_k, 1) if num_k else 1
            result[PIECE_NAMES[piece_k]] = count
    return result


def parse_board(lines):
    """
    board[row][col] = {'piece': str, 'player': 'sente'|'gote'} | None
    row 0 = 一 (haut), col 0 = colonne 9 (gauche KIF), col 8 = colonne 1 (droite KIF)
    """
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
                    'svg':   ('1' if gote else '0') + PIECE_TO_SVG.get(PIECE_NAMES.get(piece_char, ''), '??'),
                    'player': 'gote' if gote else 'sente',
                }
    return board


def bounding_box(board):
    rows, cols = [], []
    for r in range(9):
        for c in range(9):
            if board[r][c]:
                rows.append(r)
                cols.append(c)
    if not rows:
        return 0, 8, 0, 8
    min_r = max(0, min(rows) - 1)
    max_r = min(8, max(rows) + 1)
    min_c = max(0, min(cols) - 1)
    max_c = min(8, max(cols) + 1)
    return min_r, max_r, min_c, max_c


def parse_moves(move_lines):
    moves = []
    pattern_from = re.compile(r'\s*(\d+)\s+(.*?)\((\d{2})\)\s*\(')
    pattern_drop = re.compile(r'\s*(\d+)\s+(\S+)\s*\(')
    for line in move_lines:
        # Arrêt sur tout marqueur de fin invalide
        if any(w in line for w in STOP_WORDS):
            break
        m = pattern_from.match(line)
        if m:
            num = int(m.group(1))
            move = m.group(2).strip()
            from_coord = m.group(3)
            from_col = 9 - int(from_coord[0])
            from_row = int(from_coord[1]) - 1
            moves.append({'num': num, 'move': move, 'from_col': from_col, 'from_row': from_row})
        else:
            m2 = pattern_drop.match(line)
            if m2:
                num = int(m2.group(1))
                move = m2.group(2).strip()
                moves.append({'num': num, 'move': move, 'from_col': -1, 'from_row': -1})
    return moves


def is_valid(data):
    """Un tsume valide a un nombre impair de coups ≥ 1."""
    n = len(data['moves'])
    return n > 0 and n % 2 == 1


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
        'sente_hand': {},
        'gote_hand': {},
        'board': [],
        'moves': [],
        'author': '',
        'source': '',
        'bbox': {},
    }

    board_lines = []
    move_section = False
    move_lines = []

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
        elif move_section and re.match(r'\s*\d+', line):
            move_lines.append(line)

    if len(board_lines) == 9:
        board = parse_board(board_lines)
        data['board'] = board
        min_r, max_r, min_c, max_c = bounding_box(board)
        data['bbox'] = {
            'min_row': min_r, 'max_row': max_r,
            'min_col': min_c, 'max_col': max_c,
        }

    data['moves'] = parse_moves(move_lines)
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

    tsume_list = []
    skipped = 0
    errors = []

    for i, kif_path in enumerate(kif_files, 1):
        try:
            data = parse_kif(kif_path)
            if not is_valid(data):
                skipped += 1
                continue
            data['id'] = len(tsume_list) + 1
            tsume_list.append(data)
            if i % 100 == 0:
                print(f"  {i}/{total}...")
        except Exception as e:
            errors.append((kif_path.name, str(e)))
            print(f"  ⚠️  {kif_path.name} : {e}")

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)

    with open(OUTPUT, 'w', encoding='utf-8') as f:
        json.dump(tsume_list, f, ensure_ascii=False, indent=None, separators=(',', ':'))

    size_mb = OUTPUT.stat().st_size / 1_000_000
    print()
    print(f"✅ {len(tsume_list)} tsume exportés")
    if skipped:
        print(f"🚫 {skipped} problèmes invalides ignorés (中断, nombre pair de coups…)")
    print(f"📦 Taille du fichier : {size_mb:.1f} Mo")
    if errors:
        print(f"⚠️  {len(errors)} erreurs :")
        for name, err in errors:
            print(f"   {name} : {err}")


if __name__ == '__main__':
    main()
