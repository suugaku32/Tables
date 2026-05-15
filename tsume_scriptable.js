const FM = FileManager.iCloud()
const BASE = FM.documentsDirectory()

const STATE_PATH = FM.joinPath(BASE, "state.json")
let state = { index: 0 }
if (FM.fileExists(STATE_PATH)) {
  await FM.downloadFileFromiCloud(STATE_PATH)
  state = JSON.parse(FM.readString(STATE_PATH))
}

const TSUME_PATH = FM.joinPath(BASE, "tsume.json")
await FM.downloadFileFromiCloud(TSUME_PATH)
const ALL_TSUME = JSON.parse(FM.readString(TSUME_PATH))

const idx = ((state.index - 1) + ALL_TSUME.length) % ALL_TSUME.length
const tsume = ALL_TSUME[idx]

const url = "https://fabius32.github.io/Tables/tsume.html?id=" + tsume.id

Safari.open(url)
Script.complete()
