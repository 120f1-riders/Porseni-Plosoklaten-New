import { google } from 'googleapis'
import { Readable } from 'node:stream'

const SCOPES = [
  'https://www.googleapis.com/auth/drive',
  'https://www.googleapis.com/auth/spreadsheets',
]

let _auth = null
function getAuth() {
  if (_auth) return _auth
  const client_email = process.env.GOOGLE_CLIENT_EMAIL
  const project_id = process.env.GOOGLE_PROJECT_ID
  const private_key = (process.env.GOOGLE_PRIVATE_KEY || '').replace(/\\n/g, '\n')
  if (!client_email || !private_key) return null
  _auth = new google.auth.GoogleAuth({
    credentials: { client_email, private_key, project_id },
    scopes: SCOPES,
  })
  return _auth
}

export function googleConfigured() {
  return !!(process.env.GOOGLE_CLIENT_EMAIL && process.env.GOOGLE_PRIVATE_KEY && process.env.GOOGLE_DRIVE_FOLDER_ID)
}

function driveClient() { return google.drive({ version: 'v3', auth: getAuth() }) }
function sheetsClient() { return google.sheets({ version: 'v4', auth: getAuth() }) }

const SPREADSHEET_ID = () => process.env.GOOGLE_SHEETS_SPREADSHEET_ID
const TAB = () => process.env.GOOGLE_SHEETS_TAB || 'Sheet1'
// A1 range with quoted tab name (safe for spaces)
const RANGE = (cells) => `'${TAB().replace(/'/g, "''")}'!${cells}`

// ---------- DRIVE ----------
const _folderCache = new Map()
async function ensureFolder(name, parentId) {
  const cacheKey = parentId + '/' + name
  if (_folderCache.has(cacheKey)) return _folderCache.get(cacheKey)
  const drive = driveClient()
  const safe = String(name).replace(/'/g, "\\'")
  const q = `mimeType='application/vnd.google-apps.folder' and name='${safe}' and '${parentId}' in parents and trashed=false`
  const res = await drive.files.list({ q, fields: 'files(id,name)', supportsAllDrives: true, includeItemsFromAllDrives: true })
  let id
  if (res.data.files && res.data.files.length) id = res.data.files[0].id
  else {
    const created = await drive.files.create({
      requestBody: { name: String(name), mimeType: 'application/vnd.google-apps.folder', parents: [parentId] },
      fields: 'id', supportsAllDrives: true,
    })
    id = created.data.id
  }
  _folderCache.set(cacheKey, id)
  return id
}

// Walk/create nested folder path under the root shared folder; returns final folder id
export async function ensureFolderPath(parts = []) {
  let parent = process.env.GOOGLE_DRIVE_FOLDER_ID
  for (const part of parts) {
    if (!part) continue
    parent = await ensureFolder(String(part).slice(0, 120), parent)
  }
  return parent
}

export async function uploadToDrive({ buffer, filename, mimeType, folderId }) {
  const drive = driveClient()
  const parent = folderId || process.env.GOOGLE_DRIVE_FOLDER_ID
  const res = await drive.files.create({
    requestBody: { name: filename, parents: [parent] },
    media: { mimeType: mimeType || 'application/octet-stream', body: Readable.from(buffer) },
    fields: 'id,name,mimeType,webViewLink',
    supportsAllDrives: true,
  })
  const f = res.data
  return {
    driveId: f.id,
    name: f.name,
    mimeType: f.mimeType,
    url: f.webViewLink || `https://drive.google.com/file/d/${f.id}/view`,
  }
}

export async function downloadFromDrive(driveId) {
  const drive = driveClient()
  const res = await drive.files.get(
    { fileId: driveId, alt: 'media', supportsAllDrives: true },
    { responseType: 'arraybuffer' }
  )
  return Buffer.from(res.data)
}

// ---------- SHEETS ----------
export async function ensureTab() {
  const sheets = sheetsClient()
  const ss = await sheets.spreadsheets.get({ spreadsheetId: SPREADSHEET_ID(), fields: 'sheets(properties(title))' })
  const titles = (ss.data.sheets || []).map((s) => s.properties.title)
  if (!titles.includes(TAB())) {
    await sheets.spreadsheets.batchUpdate({
      spreadsheetId: SPREADSHEET_ID(),
      requestBody: { requests: [{ addSheet: { properties: { title: TAB() } } }] },
    })
  }
}

export async function ensureHeader(headerRow) {
  const sheets = sheetsClient()
  const res = await sheets.spreadsheets.values.get({ spreadsheetId: SPREADSHEET_ID(), range: RANGE('A1:Z1') })
  const has = res.data.values && res.data.values.length && res.data.values[0].length
  if (!has) {
    await sheets.spreadsheets.values.update({
      spreadsheetId: SPREADSHEET_ID(), range: RANGE('A1'), valueInputOption: 'RAW',
      requestBody: { values: [headerRow] },
    })
  }
}

export async function appendRows(rows) {
  const sheets = sheetsClient()
  await sheets.spreadsheets.values.append({
    spreadsheetId: SPREADSHEET_ID(), range: RANGE('A:N'),
    valueInputOption: 'RAW', insertDataOption: 'INSERT_ROWS',
    requestBody: { values: rows },
  })
}

export async function overwriteSheet(headerRow, rows) {
  const sheets = sheetsClient()
  await sheets.spreadsheets.values.clear({ spreadsheetId: SPREADSHEET_ID(), range: RANGE('A:Z') })
  await sheets.spreadsheets.values.update({
    spreadsheetId: SPREADSHEET_ID(), range: RANGE('A1'), valueInputOption: 'RAW',
    requestBody: { values: [headerRow, ...rows] },
  })
}

export async function statusCheck() {
  const out = { configured: googleConfigured(), client_email: process.env.GOOGLE_CLIENT_EMAIL }
  const drive = driveClient()
  const folder = await drive.files.get({ fileId: process.env.GOOGLE_DRIVE_FOLDER_ID, fields: 'id,name', supportsAllDrives: true })
  out.drive_folder = folder.data.name
  const sheets = sheetsClient()
  const ss = await sheets.spreadsheets.get({ spreadsheetId: SPREADSHEET_ID(), fields: 'properties(title),sheets(properties(title))' })
  out.spreadsheet = ss.data.properties.title
  out.tabs = (ss.data.sheets || []).map((s) => s.properties.title)
  out.target_tab = TAB()
  return out
}
