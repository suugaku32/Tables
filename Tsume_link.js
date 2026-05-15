// Variables used by Scriptable.
// These must be at the very top of the file. Do not edit.
// icon-color: purple; icon-glyph: magic; share-sheet-inputs: url;
const FM = FileManager.iCloud()
const BASE = FM.documentsDirectory()

const STATE_PATH = FM.joinPath(BASE, "state.json")
let lastId = null
if (FM.fileExists(STATE_PATH)) {
  await FM.downloadFileFromiCloud(STATE_PATH)
  const s = JSON.parse(FM.readString(STATE_PATH))
  lastId = s.lastId || null
}

const base = "https://fabius32.github.io/Tables/tsume.html"
const url = lastId ? base + "#id=" + lastId : base

if (config.runsInApp) {
  Safari.open(url)
} else {
  Script.setShortcutOutput(url)
}
Script.complete()
