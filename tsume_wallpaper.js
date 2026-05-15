// Variables used by Scriptable.
// These must be at the very top of the file. Do not edit.
// icon-color: deep-gray; icon-glyph: chess-board;
// tsume_wallpaper.js — Scriptable
// Génère l'image du tsume et la retourne à Shortcuts
// Shortcuts pose ensuite l'image comme fond d'écran

const FM = FileManager.iCloud()
const BASE = FM.documentsDirectory()

// ── State ────────────────────────────────────────────────────────────────────
const STATE_PATH = FM.joinPath(BASE, "state.json")
function loadState() {
  if (!FM.fileExists(STATE_PATH)) return { index: 0 }
  FM.downloadFileFromiCloud(STATE_PATH)
  return JSON.parse(FM.readString(STATE_PATH))
}
function saveState(s) { FM.writeString(STATE_PATH, JSON.stringify(s)) }

// ── Tsume ────────────────────────────────────────────────────────────────────
const TSUME_PATH = FM.joinPath(BASE, "tsume.json")
await FM.downloadFileFromiCloud(TSUME_PATH)
const ALL_TSUME = JSON.parse(FM.readString(TSUME_PATH))

// Filtre sur les problèmes en 3 coups uniquement
const TSUME_POOL = ALL_TSUME.filter(t => t.moves.length === 3)

let state = loadState()
const idx = state.index % TSUME_POOL.length
const tsume = TSUME_POOL[idx]

// Incrémente pour le prochain appel
state.index = (state.index + 1) % TSUME_POOL.length
saveState(state)

// ── Helpers ──────────────────────────────────────────────────────────────────
const PIECE_KANJI = {
  fu:'歩', kyou:'香', kei:'桂', gin:'銀', kin:'金',
  kaku:'角', hi:'飛', gyoku:'玉', to:'と',
  nkyou:'成香', nkei:'成桂', ngin:'成銀', uma:'馬', ryuu:'龍'
}
const ROW_KANJI = ['一','二','三','四','五','六','七','八','九']

// ── Dimensions iPhone 17 (1206×2622 @3x = 402×874pt) ────────────────────────
const W = 1206
const H = 2622
const SCALE = 3

// ── Couleurs ──────────────────────────────────────────────────────────────────
const C_BG       = new Color("#1e2240")
const C_GRID     = new Color("#ffffff", 0.20)
const C_PIECE    = new Color("#ffffff", 1)
const C_LABEL    = new Color("#ffffff", 0.25)
const C_HEADER   = new Color("#ffffff", 1)
const C_HAND_LBL = new Color("#ffffff", 1)
const C_HAND_PCE = new Color("#ffffff", 1)
const C_HAND_STR = new Color("#ffffff", 0.50)
const C_HAND_CNT = new Color("#ffffff", 0.35)
const C_NASHI    = new Color("#ffffff", 0.20)
const C_SOL_BG   = new Color("#0d1020")
const C_SOL_TEXT = new Color("#ffffff", 0.85)
const C_SOL_TTL  = new Color("#ffffff", 0.35)
const C_SEP      = new Color("#ffffff", 0.12)

// ── Layout ────────────────────────────────────────────────────────────────────
const HEADER_H = 1300  // remonté
const SIDE_W   = 120

const bbox  = tsume.bbox
const board = tsume.board
const N_COLS = bbox.max_col - bbox.min_col + 1
const N_ROWS = bbox.max_row - bbox.min_row + 1

const BOARD_ZONE = H - HEADER_H - 400  // marge basse
const MAX_CELL = 120  // taille max d une case
const CELL = Math.min(
  MAX_CELL,
  Math.floor((W - 2 * SIDE_W) / N_COLS),
  Math.floor(BOARD_ZONE / N_ROWS)
)
const BOARD_W = CELL * N_COLS
const BOARD_H = CELL * N_ROWS
const BOARD_X = Math.round((W - BOARD_W) / 2)
const BOARD_Y = Math.round(HEADER_H + (BOARD_ZONE - BOARD_H) / 2)

const HAND_LEFT_CX  = Math.round(BOARD_X / 2)
const HAND_RIGHT_CX = Math.round(BOARD_X + BOARD_W + (W - BOARD_X - BOARD_W) / 2)

// ── Fond d'écran de base ─────────────────────────────────────────────────────
// Place ton fond d'écran dans iCloud Drive / Scriptable / wallpaper_base.jpg
const BASE_WP_PATH = FM.joinPath(BASE, "wallpaper_base.jpg")
let baseImage = null
if (FM.fileExists(BASE_WP_PATH)) {
  FM.downloadFileFromiCloud(BASE_WP_PATH)
  baseImage = Image.fromFile(BASE_WP_PATH)
}

// ── DrawContext ───────────────────────────────────────────────────────────────
const dc = new DrawContext()
dc.size = new Size(W, H)
dc.respectScreenScale = false
dc.opaque = true

if (baseImage) {
  // Étape 1 : redimensionner l image dans un DrawContext séparé (avec clipping)
  const iW = baseImage.size.width
  const iH = baseImage.size.height
  const scaleX = W / iW
  const scaleY = H / iH
  const scale = Math.max(scaleX, scaleY)
  const scaledW = Math.round(iW * scale)
  const scaledH = Math.round(iH * scale)
  const offsetX = Math.round((W - scaledW) / 2)
  const offsetY = Math.round((H - scaledH) / 2)

  const bgDc = new DrawContext()
  bgDc.size = new Size(W, H)
  bgDc.opaque = true
  bgDc.respectScreenScale = false
  bgDc.drawImageInRect(baseImage, new Rect(offsetX, offsetY, scaledW, scaledH))
  const bgImage = bgDc.getImage()

  // Étape 2 : poser l image redimensionnée comme fond dans le contexte principal
  dc.drawImageInRect(bgImage, new Rect(0, 0, W, H))
} else {
  // Fond de secours si pas de wallpaper_base.jpg
  dc.setFillColor(C_BG)
  dc.fillRect(new Rect(0, 0, W, H))
  dc.setFillColor(new Color("#0f1520", 0.6))
  dc.fillEllipse(new Rect(-100, H * 0.4, W + 200, H * 0.5))
}

// ── Header ────────────────────────────────────────────────────────────────────
dc.setTextColor(C_HEADER)
dc.setFont(Font.systemFont(52))
dc.drawText('詰将棋', new Point(60, 40))

dc.setFont(Font.systemFont(36))
dc.setTextColor(new Color("#ffffff", 0.25))
dc.drawText(`#${tsume.id}`, new Point(60, 104))

if (tsume.author) {
  dc.setFont(Font.systemFont(34))
  dc.drawTextInRect(tsume.author, new Rect(W/2, 64, W/2 - 60, 48))
}

// ── Rectangle semi-transparent sous le goban ─────────────────────────────────
const BLUR_M = 100
const bY = BOARD_Y - BLUR_M
dc.setFillColor(new Color("#000000", 0.40))
dc.fillRect(new Rect(-10, bY, W + 20, H - bY + 10))  // jusqu'en bas de l écran

// ── Grille ────────────────────────────────────────────────────────────────────
dc.setStrokeColor(new Color("#ffffff", 1))
dc.setLineWidth(4)
for (let c = 0; c <= N_COLS; c++) {
  const x = BOARD_X + c * CELL
  const p = new Path()
  p.move(new Point(x, BOARD_Y))
  p.addLine(new Point(x, BOARD_Y + BOARD_H))
  dc.addPath(p)
  dc.strokePath()
}
for (let r = 0; r <= N_ROWS; r++) {
  const y = BOARD_Y + r * CELL
  const p = new Path()
  p.move(new Point(BOARD_X, y))
  p.addLine(new Point(BOARD_X + BOARD_W, y))
  dc.addPath(p)
  dc.strokePath()
}

// ── Labels colonnes ───────────────────────────────────────────────────────────
dc.setTextColor(new Color("#ffffff", 1))
dc.setFont(Font.boldSystemFont(40))
for (let c = 0; c < N_COLS; c++) {
  const colNum = String(9 - (bbox.min_col + c))
  const x = BOARD_X + c * CELL + CELL/2 - 14
  dc.drawText(colNum, new Point(x, BOARD_Y - 56))
}

// Labels lignes
for (let r = 0; r < N_ROWS; r++) {
  const y = BOARD_Y + r * CELL + CELL/2 - 22
  dc.drawText(ROW_KANJI[bbox.min_row + r], new Point(BOARD_X + BOARD_W + 20, y))
}

// ── Pentagone ─────────────────────────────────────────────────────────────────
function drawPentagon(cx, cy, size, flipped, color, lw) {
  const w = size * 0.88, h = size
  let pts = [
    new Point(cx,          cy - h*0.50),
    new Point(cx + w*0.50, cy - h*0.15),
    new Point(cx + w*0.42, cy + h*0.50),
    new Point(cx - w*0.42, cy + h*0.50),
    new Point(cx - w*0.50, cy - h*0.15),
  ]
  if (flipped) pts = pts.map(p => new Point(p.x, 2*cy - p.y))
  const path = new Path()
  path.move(pts[0])
  for (let i = 1; i < pts.length; i++) path.addLine(pts[i])
  path.closeSubpath()
  dc.setStrokeColor(color)
  dc.setLineWidth(lw || 2.5)
  dc.addPath(path)
  dc.strokePath()
}

// ── Pièces sur le goban — PNG depuis pieces_png/ ─────────────────────────────
const PIECE_TO_CODE = {
  fu:'FU', kyou:'KY', kei:'KE', gin:'GI', kin:'KI',
  kaku:'KA', hi:'HI', gyoku:'OU', to:'TO',
  nkyou:'NY', nkei:'NK', ngin:'NG', uma:'UM', ryuu:'RY'
}
const PIECES_PNG_DIR = FM.joinPath(BASE, "pieces_png")
const FONT_SIZE = Math.round(CELL * 0.52)

// Précharge les PNG uniques nécessaires
const pngCache = {}
for (let r = bbox.min_row; r <= bbox.max_row; r++) {
  for (let c = bbox.min_col; c <= bbox.max_col; c++) {
    const cell = board[r][c]
    if (!cell) continue
    const prefix = cell.player === 'gote' ? '1' : '0'
    const code = prefix + (PIECE_TO_CODE[cell.piece] || 'FU')
    if (!pngCache[code]) {
      const path = FM.joinPath(PIECES_PNG_DIR, code + ".png")
      if (FM.fileExists(path)) {
        FM.downloadFileFromiCloud(path)
        const img = Image.fromFile(path)
        if (img) pngCache[code] = img
      }
    }
  }
}

// Dessine les pièces
const sz = CELL - 10
for (let r = bbox.min_row; r <= bbox.max_row; r++) {
  for (let c = bbox.min_col; c <= bbox.max_col; c++) {
    const cell = board[r][c]
    if (!cell) continue
    const drawC = c - bbox.min_col
    const drawR = r - bbox.min_row
    const cx = BOARD_X + drawC * CELL + CELL/2
    const cy = BOARD_Y + drawR * CELL + CELL/2
    const prefix = cell.player === 'gote' ? '1' : '0'
    const code = prefix + (PIECE_TO_CODE[cell.piece] || 'FU')
    if (pngCache[code]) {
      dc.drawImageInRect(pngCache[code], new Rect(cx - sz/2, cy - sz/2, sz, sz))
    } else {
      // Fallback kanji texte
      dc.setTextColor(C_PIECE)
      dc.setFont(Font.boldSystemFont(FONT_SIZE))
      const kanji = PIECE_KANJI[cell.piece] || cell.piece
      dc.drawTextInRect(kanji, new Rect(cx - FONT_SIZE/2, cy - FONT_SIZE/2, FONT_SIZE, FONT_SIZE))
    }
  }
}

// ── Pièces en main — kanji seul, plus grand ──────────────────────────────────
const HP      = Math.round(CELL * 0.55)   // plus grandes
const HS      = Math.round(CELL * 0.62)   // espacement adapté
const HFS     = Math.round(CELL * 0.52)   // taille du kanji
const HFS_CNT = Math.round(CELL * 0.30)   // taille du compteur
const HAND_START_Y = BOARD_Y + 10

function drawHand(entries, cx, flipped, label, align) {
  dc.setTextColor(C_HAND_LBL)
  dc.setFont(Font.boldSystemFont(44))
  const labelText = label[0] + label[1]
  const lw = 120
  const lx = cx - lw/2
  dc.drawTextInRect(labelText, new Rect(lx, BOARD_Y - 60, lw, 52))

  if (!entries || entries.length === 0) {
    dc.setTextColor(C_NASHI)
    dc.setFont(Font.systemFont(38))
    dc.drawTextInRect('な', new Rect(cx - 22, HAND_START_Y,      44, 44))
    dc.drawTextInRect('し', new Rect(cx - 22, HAND_START_Y + 46, 44, 44))
    return
  }

  entries.forEach(([piece, count], i) => {
    const kanji = PIECE_KANJI[piece] || piece
    const py = HAND_START_Y + i * HS
    const cy = py + HFS / 2
    const kx = cx - HFS*0.5
    dc.setTextColor(C_HAND_PCE)
    dc.setFont(Font.boldSystemFont(HFS))
    dc.drawTextInRect(kanji, new Rect(kx, cy - HFS*0.5, HFS, HFS))
    if (count > 1) {
      dc.setTextColor(C_HAND_CNT)
      dc.setFont(Font.systemFont(HFS_CNT))
      dc.drawText(String(count), new Point(kx + HFS*0.76, cy + HFS*0.22))
    }
  })
}

const GOTE_CX  = Math.round(BOARD_X / 2)
const SENTE_CX = Math.round(BOARD_X + BOARD_W + (W - BOARD_X - BOARD_W) / 2)
drawHand(Object.entries(tsume.gote_hand),  GOTE_CX,  true,  '後手', 'center')
drawHand(Object.entries(tsume.sente_hand), SENTE_CX, false, '先手', 'center')

// (solution supprimée — affichée dans le widget écran d'accueil)

// ── Output ────────────────────────────────────────────────────────────────────
const img = dc.getImage()

// Sauvegarde locale
const imgPath = FM.joinPath(BASE, "current_tsume.jpg")
FM.writeImage(imgPath, img)

if (config.runsInApp) {
  await QuickLook.present(img)
  Script.complete()
} else {
  const rawData = Data.fromPNG(img)
  const base64String = rawData.toBase64String()
  Script.setShortcutOutput(base64String)
  Script.complete()
}
