// tsume_scriptable — ouvre le problème du jour dans l'app web
const FM = FileManager.iCloud()
const BASE = FM.documentsDirectory()

const STATE_PATH = FM.joinPath(BASE, "state.json")
function loadState() {
  if (!FM.fileExists(STATE_PATH)) return { index: 0 }
  FM.downloadFileFromiCloud(STATE_PATH)
  return JSON.parse(FM.readString(STATE_PATH))
}

const TSUME_PATH = FM.joinPath(BASE, "tsume.json")
FM.downloadFileFromiCloud(TSUME_PATH)
const ALL_TSUME = JSON.parse(FM.readString(TSUME_PATH))
const state = loadState()
const idx = ((state.index - 1) + ALL_TSUME.length) % ALL_TSUME.length
const tsume = ALL_TSUME[idx]

const url = "https://fabius32.github.io/Tables/tsume.html?id=" + tsume.id

if (config.runsInApp) {
  await Safari.openInApp(url, true)
} else {
  Script.setShortcutOutput(url)
}
Script.complete()
