import { google } from 'googleapis'
import { Readable } from 'node:stream'

const SHEETS_SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
export const DRIVE_SCOPE = 'https://www.googleapis.com/auth/drive'

// ============================================================
// SHEETS — Service Account
// ============================================================
let _svcAuth = null
function getServiceAuth() {
  if (_svcAuth) return _svcAuth
  const client_email = process.env.GOOGLE_CLIENT_EMAIL
  const project_id = process.env.GOOGLE_PROJECT_ID
  const private_key = (process.env.GOOGLE_PRIVATE_KEY || '').replace(/\\n/g, '\n')
  if (!client_email || !private_key) return null
  _svcAuth = new google.auth.GoogleAuth({
    credentials: { client_email, private_key, project_id },
    scopes: SHEETS_SCOPES,
  })
  return _svcAuth
}

export function sheetsConfigured() {
  return !!(process.env.GOOGLE_CLIENT_EMAIL && process.env.GOOGLE_PRIVATE_KEY && process.env.GOOGLE_SHEETS_SPREADSHEET_ID)
}

function sheetsClient() { return google.sheets({ version: 'v4', auth: getServiceAuth() }) }

const SPREADSHEET_ID = () => process.env.GOOGLE_SHEETS_SPREADSHEET_ID
const TAB = () => process.env.GOOGLE_SHEETS_TAB || 'Sheet1'
const RANGE = (cells) => `'${TAB().replace(/'/g, "''")}'!${cells}`

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

export async function sheetsStatus() {
  const out = { spreadsheet: null, tabs: [], target_tab: TAB() }
  const sheets = sheetsClient()
  const ss = await sheets.spreadsheets.get({ spreadsheetId: SPREADSHEET_ID(), fields: 'properties(title),sheets(properties(title))' })
  out.spreadsheet = ss.data.properties.title
  out.tabs = (ss.data.sheets || []).map((s) => s.properties.title)
  return out
}

// ============================================================
// DRIVE — OAuth user delegation
// ============================================================
export function oauthConfigured() {
  return !!(process.env.GOOGLE_OAUTH_CLIENT_ID && process.env.GOOGLE_OAUTH_CLIENT_SECRET && redirectUri())
}

function redirectUri() {
  return process.env.GOOGLE_REDIRECT_URI || ((process.env.NEXT_PUBLIC_BASE_URL || '') + '/api/google/callback')
}

export function getOAuthClient(refreshToken) {
  const c = new google.auth.OAuth2(
    process.env.GOOGLE_OAUTH_CLIENT_ID,
    process.env.GOOGLE_OAUTH_CLIENT_SECRET,
    redirectUri()
  )
  if (refreshToken) c.setCredentials({ refresh_token: refreshToken })
  return c
}

export function driveAuthUrl(state) {
  return getOAuthClient().generateAuthUrl({
    access_type: 'offline',
    prompt: 'consent select_account',
    scope: [DRIVE_SCOPE],
    state,
  })
}

export async function exchangeCode(code) {
  const { tokens } = await getOAuthClient().getToken(code)
  return tokens
}

function driveClient(refreshToken) {
  return google.drive({ version: 'v3', auth: getOAuthClient(refreshToken) })
}

const _folderCache = new Map()
async function ensureFolder(drive, name, parentId) {
  const cacheKey = parentId + '/' + name
  if (_folderCache.has(cacheKey)) return _folderCache.get(cacheKey)
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

export async function ensureFolderPath(parts = [], refreshToken) {
  const drive = driveClient(refreshToken)
  let parent = process.env.GOOGLE_DRIVE_FOLDER_ID
  for (const part of parts) {
    if (!part) continue
    parent = await ensureFolder(drive, String(part).slice(0, 120), parent)
  }
  return parent
}

export async function uploadToDrive({ buffer, filename, mimeType, folderId, refreshToken }) {
  const drive = driveClient(refreshToken)
  const parent = folderId || process.env.GOOGLE_DRIVE_FOLDER_ID
  const res = await drive.files.create({
    requestBody: { name: filename, parents: parent ? [parent] : undefined },
    media: { mimeType: mimeType || 'application/octet-stream', body: Readable.from(buffer) },
    fields: 'id,name,mimeType,webViewLink',
    supportsAllDrives: true,
  })
  const f = res.data
  return {
    driveId: f.id, name: f.name, mimeType: f.mimeType,
    url: f.webViewLink || `https://drive.google.com/file/d/${f.id}/view`,
  }
}

export async function downloadFromDrive(driveId, refreshToken) {
  const drive = driveClient(refreshToken)
  const res = await drive.files.get(
    { fileId: driveId, alt: 'media', supportsAllDrives: true },
    { responseType: 'arraybuffer' }
  )
  return Buffer.from(res.data)
}

export async function driveStatus(refreshToken) {
  const drive = driveClient(refreshToken)
  const folder = await drive.files.get({ fileId: process.env.GOOGLE_DRIVE_FOLDER_ID, fields: 'id,name', supportsAllDrives: true })
  return { drive_folder: folder.data.name }
}
