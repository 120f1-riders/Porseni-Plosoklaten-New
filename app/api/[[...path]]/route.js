import { MongoClient } from 'mongodb'
import { v4 as uuidv4 } from 'uuid'
import { NextResponse } from 'next/server'
import crypto from 'node:crypto'
import fs from 'node:fs/promises'
import path from 'node:path'
import {
  googleConfigured,
  uploadToDrive,
  downloadFromDrive,
  ensureFolderPath,
  ensureTab,
  ensureHeader,
  appendRows,
  overwriteSheet,
  statusCheck,
} from '@/lib/porseni/google'

const SHEET_HEADER = [
  'No Peserta', 'Nama Peserta', 'L/P', 'Cabang Lomba', 'Jenis', 'Madrasah',
  'NISN', 'TTL', 'Tim', 'Kelengkapan', 'Link Akte', 'Link Surat Ket', 'Link Pas Photo', 'Tanggal Daftar',
]

async function fileLinkFor(db, f) {
  if (!f || !f.id) return ''
  const rec = await db.collection('files').findOne({ id: f.id })
  if (rec && rec.drive_url) return rec.drive_url
  return (process.env.NEXT_PUBLIC_BASE_URL || '') + '/api/files/' + f.id
}

async function buildSheetRow(db, doc, lomba) {
  const files = doc.files || {}
  return [
    doc.nomor_peserta || '', doc.participant_name || '', doc.gender || '',
    doc.lomba_name || (lomba ? lomba.name : ''), (lomba ? lomba.type : '') || '',
    doc.madrasah_name || '', doc.nisn || '', doc.ttl || '', doc.team_name || '',
    doc.complete ? 'Lengkap' : 'Belum',
    await fileLinkFor(db, files.akte), await fileLinkFor(db, files.surat_ket), await fileLinkFor(db, files.pas_photo),
    doc.created_at ? new Date(doc.created_at).toLocaleString('id-ID') : '',
  ]
}

// Append one or more peserta docs to Google Sheet (non-blocking / best-effort)
async function syncSheetAppend(db, docs) {
  try {
    if (!googleConfigured() || !process.env.GOOGLE_SHEETS_SPREADSHEET_ID) return
    await ensureTab()
    await ensureHeader(SHEET_HEADER)
    const rows = []
    for (const d of docs) {
      const lomba = await db.collection('lomba').findOne({ id: d.lomba_id })
      rows.push(await buildSheetRow(db, d, lomba))
    }
    if (rows.length) await appendRows(rows)
  } catch (e) {
    console.error('[sheet-sync] append failed:', e.message)
  }
}

let client
let db

const UP_DIR = path.join(process.cwd(), '.uploads')
const SALT = 'porseni_mi_plosoklaten_2025'

async function connectToMongo() {
  if (!client) {
    client = new MongoClient(process.env.MONGO_URL)
    await client.connect()
    db = client.db(process.env.DB_NAME)
  }
  return db
}

function handleCORS(response) {
  response.headers.set('Access-Control-Allow-Origin', process.env.CORS_ORIGINS || '*')
  response.headers.set('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
  response.headers.set('Access-Control-Allow-Headers', 'Content-Type, Authorization')
  response.headers.set('Access-Control-Allow-Credentials', 'true')
  return response
}

function json(data, status = 200) {
  return handleCORS(NextResponse.json(data, { status }))
}

function hashPw(pw) {
  return crypto.createHash('sha256').update(String(pw) + SALT).digest('hex')
}

function clean(doc) {
  if (!doc) return doc
  const { _id, password, password_plain, token, ...rest } = doc
  return rest
}

// For super_admin user listing: keep password_plain visible, strip hash/token/_id
function cleanUserAdmin(doc) {
  if (!doc) return doc
  const { _id, password, token, ...rest } = doc
  return rest
}

const REQUIRED_FILE_KEYS = ['akte', 'surat_ket', 'pas_photo']

function computeComplete(doc) {
  const files = doc.files || {}
  const hasAllFiles = REQUIRED_FILE_KEYS.every((k) => files[k] && files[k].id)
  const hasData = !!(doc.participant_name && doc.gender && doc.lomba_id)
  return hasData && hasAllFiles
}

async function getUser(request) {
  const auth = request.headers.get('authorization') || ''
  const token = auth.startsWith('Bearer ') ? auth.slice(7) : null
  if (!token) return null
  const u = await db.collection('users').findOne({ token })
  return u || null
}

export async function OPTIONS() {
  return handleCORS(new NextResponse(null, { status: 200 }))
}

async function handleRoute(request, { params }) {
  const { path: pathArr = [] } = await params
  const p = pathArr
  const route = `/${p.join('/')}`
  const method = request.method

  try {
    const db = await connectToMongo()

    // ---------- HEALTH ----------
    if ((route === '/' || route === '/root') && method === 'GET') {
      return json({ message: 'Porseni MI Plosoklaten API' })
    }

    // ---------- INTEGRATIONS (Google Drive + Sheets) ----------
    if (route === '/integrations/status' && method === 'GET') {
      const u = await getUser(request)
      if (!u || u.role !== 'super_admin') return json({ error: 'Akses ditolak' }, 403)
      if (!googleConfigured()) return json({ configured: false, message: 'Kredensial Google belum diset' })
      try {
        const st = await statusCheck()
        st.tab_exists = Array.isArray(st.tabs) && st.tabs.includes(st.target_tab)
        return json(st)
      } catch (e) {
        return json({ configured: true, ok: false, error: e.message }, 200)
      }
    }
    if (route === '/integrations/sync' && method === 'POST') {
      const u = await getUser(request)
      if (!u || u.role !== 'super_admin') return json({ error: 'Akses ditolak' }, 403)
      if (!googleConfigured()) return json({ error: 'Kredensial Google belum diset' }, 400)
      try {
        await ensureTab()
        const all = await db.collection('peserta').find({}).sort({ lomba_name: 1, nomor_peserta: 1 }).toArray()
        const rows = []
        for (const d of all) {
          const lomba = await db.collection('lomba').findOne({ id: d.lomba_id })
          rows.push(await buildSheetRow(db, d, lomba))
        }
        await overwriteSheet(SHEET_HEADER, rows)
        return json({ ok: true, synced: rows.length })
      } catch (e) {
        return json({ error: e.message }, 500)
      }
    }

    // ---------- FILE SERVE ---------- GET /files/:id
    if (p[0] === 'files' && p[1] && method === 'GET') {
      const f = await db.collection('files').findOne({ id: p[1] })
      if (!f) return json({ error: 'File tidak ditemukan' }, 404)
      let buf
      if (f.driveId) {
        buf = await downloadFromDrive(f.driveId)
      } else {
        buf = await fs.readFile(path.join(UP_DIR, f.storedName))
      }
      return new NextResponse(buf, {
        status: 200,
        headers: {
          'Content-Type': f.mime || 'application/octet-stream',
          'Content-Disposition': `inline; filename="${f.name}"`,
          'Cache-Control': 'public, max-age=31536000',
        },
      })
    }

    // ---------- UPLOAD ---------- POST /upload (multipart)
    if (route === '/upload' && method === 'POST') {
      const form = await request.formData()
      const file = form.get('file')
      if (!file || typeof file === 'string') return json({ error: 'File wajib diunggah' }, 400)
      const bytes = Buffer.from(await file.arrayBuffer())
      const id = uuidv4()
      const origName = file.name || id
      const mime = file.type || 'application/octet-stream'
      // Optional Drive folder path context from client (Lomba/Madrasah)
      const folderCtx = form.get('folder_path')
      let doc = null
      if (googleConfigured()) {
        try {
          let folderId
          if (folderCtx && typeof folderCtx === 'string') {
            folderId = await ensureFolderPath(folderCtx.split('/').filter(Boolean))
          }
          const up = await uploadToDrive({ buffer: bytes, filename: `${Date.now()}_${origName}`, mimeType: mime, folderId })
          doc = { id, name: origName, driveId: up.driveId, drive_url: up.url, mime, size: bytes.length, created_at: new Date() }
        } catch (e) {
          console.error('[drive-upload] failed, fallback to disk:', e.message)
        }
      }
      if (!doc) {
        await fs.mkdir(UP_DIR, { recursive: true })
        const ext = (origName && origName.includes('.')) ? '.' + origName.split('.').pop() : ''
        const storedName = id + ext
        await fs.writeFile(path.join(UP_DIR, storedName), bytes)
        doc = { id, name: origName, storedName, mime, size: bytes.length, created_at: new Date() }
      }
      await db.collection('files').insertOne(doc)
      return json({ id, name: doc.name, url: `/api/files/${id}`, size: doc.size, drive_url: doc.drive_url || null })
    }

    // ---------- AUTH ----------
    if (route === '/auth/register' && method === 'POST') {
      const b = await request.json()
      if (!b.name || !b.email || !b.password || !b.role) return json({ error: 'Data tidak lengkap' }, 400)
      const exists = await db.collection('users').findOne({ email: String(b.email).toLowerCase() })
      if (exists) return json({ error: 'Email sudah terdaftar' }, 400)
      const isSuper = b.role === 'super_admin'
      const user = {
        id: uuidv4(),
        name: b.name,
        email: String(b.email).toLowerCase(),
        password: hashPw(b.password),
        password_plain: String(b.password),
        role: b.role,
        madrasah_name: b.madrasah_name || null,
        assigned_lomba_id: b.assigned_lomba_id || null,
        status: isSuper ? 'verified' : 'pending',
        token: uuidv4(),
        created_at: new Date(),
      }
      await db.collection('users').insertOne(user)
      if (user.status === 'pending') {
        return json({ pending: true, message: 'Registrasi berhasil. Menunggu verifikasi Super Admin.' })
      }
      return json({ token: user.token, user: clean(user) })
    }

    if (route === '/auth/login' && method === 'POST') {
      const b = await request.json()
      const u = await db.collection('users').findOne({ email: String(b.email || '').toLowerCase() })
      if (!u || u.password !== hashPw(b.password)) return json({ error: 'Email atau kata sandi salah' }, 401)
      if (u.status !== 'verified') return json({ error: 'Akun Anda masih menunggu verifikasi Super Admin.' }, 403)
      const token = uuidv4()
      await db.collection('users').updateOne({ id: u.id }, { $set: { token } })
      return json({ token, user: clean({ ...u, token }) })
    }

    if (route === '/auth/me' && method === 'GET') {
      const u = await getUser(request)
      if (!u) return json({ error: 'Tidak terautentikasi' }, 401)
      return json(clean(u))
    }

    // ---------- PROFILE (self service) ----------
    if (route === '/auth/profile' && method === 'GET') {
      const u = await getUser(request)
      if (!u) return json({ error: 'Tidak terautentikasi' }, 401)
      const { _id, password, token, ...rest } = u
      return json(rest) // includes password_plain, photo_url, assigned_lomba_id
    }
    if (route === '/auth/profile' && method === 'PUT') {
      const u = await getUser(request)
      if (!u) return json({ error: 'Tidak terautentikasi' }, 401)
      const b = await request.json()
      const set = {}
      if (b.name !== undefined) set.name = b.name
      if (b.photo_url !== undefined) set.photo_url = b.photo_url
      if (b.password) { set.password = hashPw(String(b.password)); set.password_plain = String(b.password) }
      await db.collection('users').updateOne({ id: u.id }, { $set: set })
      const doc = await db.collection('users').findOne({ id: u.id })
      const { _id, password, token, ...rest } = doc
      return json(rest)
    }

    // ---------- FORGOT PASSWORD (public) -> notify super admin ----------
    if (route === '/auth/forgot' && method === 'POST') {
      const b = await request.json()
      const email = String(b.email || '').toLowerCase()
      const target = await db.collection('users').findOne({ email })
      if (target) {
        await db.collection('users').updateOne({ id: target.id }, { $set: { reset_requested: true, reset_requested_at: new Date() } })
      }
      // generic response (avoid leaking which emails exist)
      return json({ ok: true, message: 'Permintaan reset sandi terkirim ke Super Admin. Silakan hubungi Super Admin untuk sandi baru Anda.' })
    }

    // ---------- LOMBA ----------
    if (route === '/lomba' && method === 'GET') {
      const list = await db.collection('lomba').find({}).sort({ created_at: 1 }).toArray()
      return json(list.map(clean))
    }
    if (route === '/lomba' && method === 'POST') {
      const u = await getUser(request)
      if (!u || u.role !== 'super_admin') return json({ error: 'Akses ditolak' }, 403)
      const b = await request.json()
      const doc = { id: uuidv4(), name: b.name, category: b.category || 'Olahraga', type: b.type || 'individu', team_size: b.team_size ? Number(b.team_size) : null, judging_criteria: b.judging_criteria || [], created_at: new Date() }
      await db.collection('lomba').insertOne(doc)
      return json(clean(doc))
    }
    if (p[0] === 'lomba' && p[1] && method === 'PUT') {
      const u = await getUser(request)
      if (!u || u.role !== 'super_admin') return json({ error: 'Akses ditolak' }, 403)
      const b = await request.json()
      const set = {}
      ;['name', 'category', 'type', 'team_size', 'judging_criteria'].forEach(k => { if (b[k] !== undefined) set[k] = b[k] })
      await db.collection('lomba').updateOne({ id: p[1] }, { $set: set })
      const doc = await db.collection('lomba').findOne({ id: p[1] })
      return json(clean(doc))
    }
    if (p[0] === 'lomba' && p[1] && method === 'DELETE') {
      const u = await getUser(request)
      if (!u || u.role !== 'super_admin') return json({ error: 'Akses ditolak' }, 403)
      await db.collection('lomba').deleteOne({ id: p[1] })
      return json({ ok: true })
    }

    // ---------- USERS (super admin) ----------
    if (route === '/users' && method === 'GET') {
      const u = await getUser(request)
      if (!u || u.role !== 'super_admin') return json({ error: 'Akses ditolak' }, 403)
      const list = await db.collection('users').find({}).sort({ created_at: -1 }).toArray()
      return json(list.map(cleanUserAdmin))
    }
    if (p[0] === 'users' && p[1] && method === 'PUT') {
      const u = await getUser(request)
      if (!u || u.role !== 'super_admin') return json({ error: 'Akses ditolak' }, 403)
      const b = await request.json()
      const set = {}
      ;['status', 'name', 'madrasah_name', 'assigned_lomba_id'].forEach(k => { if (b[k] !== undefined) set[k] = b[k] })
      if (b.password) {
        set.password = hashPw(String(b.password))
        set.password_plain = String(b.password)
        set.reset_requested = false
      }
      await db.collection('users').updateOne({ id: p[1] }, { $set: set })
      const doc = await db.collection('users').findOne({ id: p[1] })
      return json(cleanUserAdmin(doc))
    }
    if (p[0] === 'users' && p[1] && method === 'DELETE') {
      const u = await getUser(request)
      if (!u || u.role !== 'super_admin') return json({ error: 'Akses ditolak' }, 403)
      await db.collection('users').deleteOne({ id: p[1] })
      return json({ ok: true })
    }

    // ---------- PESERTA ----------
    if (route === '/peserta' && method === 'GET') {
      const u = await getUser(request)
      if (!u) return json({ error: 'Tidak terautentikasi' }, 401)
      let q = {}
      if (u.role === 'admin_madrasah') q = { created_by: u.id }
      else if (u.role === 'panitia') q = { lomba_id: u.assigned_lomba_id, complete: true }
      const list = await db.collection('peserta').find(q).sort({ created_at: -1 }).toArray()
      return json(list.map(clean))
    }
    if (route === '/peserta' && method === 'POST') {
      const u = await getUser(request)
      if (!u) return json({ error: 'Tidak terautentikasi' }, 401)
      const b = await request.json()
      const lomba = await db.collection('lomba').findOne({ id: b.lomba_id })
      const count = await db.collection('peserta').countDocuments({ lomba_id: b.lomba_id })
      const nomor = String(count + 1).padStart(3, '0')
      const madrasah = b.madrasah_name || u.madrasah_name || '-'
      const drivePath = `${lomba ? lomba.name : 'Lomba'}/${madrasah}/${b.participant_name}`
      const doc = {
        id: uuidv4(),
        participant_name: b.participant_name,
        gender: b.gender === 'P' ? 'P' : (b.gender === 'L' ? 'L' : ''),
        nisn: b.nisn || '',
        ttl: b.ttl || '',
        madrasah_name: madrasah,
        lomba_id: b.lomba_id,
        lomba_name: lomba ? lomba.name : '',
        nomor_peserta: nomor,
        status: 'pending',
        files: b.files || {},
        drive_path: drivePath,
        created_by: u.id,
        created_at: new Date(),
      }
      doc.complete = computeComplete(doc)
      await db.collection('peserta').insertOne(doc)
      await syncSheetAppend(db, [doc])
      return json(clean(doc))
    }
    // ---------- PESERTA TEAM (kelompok) ----------
    if (route === '/peserta/team' && method === 'POST') {
      const u = await getUser(request)
      if (!u) return json({ error: 'Tidak terautentikasi' }, 401)
      const b = await request.json()
      const lomba = await db.collection('lomba').findOne({ id: b.lomba_id })
      const madrasah = b.madrasah_name || u.madrasah_name || '-'
      const members = Array.isArray(b.members) ? b.members.filter((m) => m && m.participant_name) : []
      if (members.length === 0) return json({ error: 'Minimal satu anggota tim wajib diisi' }, 400)
      const team_id = uuidv4()
      const team_name = b.team_name || `${lomba ? lomba.name : 'Tim'} - ${madrasah}`
      let count = await db.collection('peserta').countDocuments({ lomba_id: b.lomba_id })
      const created = []
      for (const m of members) {
        count += 1
        const nomor = String(count).padStart(3, '0')
        const doc = {
          id: uuidv4(),
          participant_name: m.participant_name,
          gender: m.gender === 'P' ? 'P' : (m.gender === 'L' ? 'L' : ''),
          nisn: m.nisn || '',
          ttl: m.ttl || '',
          madrasah_name: madrasah,
          lomba_id: b.lomba_id,
          lomba_name: lomba ? lomba.name : '',
          nomor_peserta: nomor,
          status: 'pending',
          files: m.files || {},
          is_group: true,
          team_id,
          team_name,
          drive_path: `${lomba ? lomba.name : 'Lomba'}/${madrasah}/${team_name}/${m.participant_name}`,
          created_by: u.id,
          created_at: new Date(),
        }
        doc.complete = computeComplete(doc)
        await db.collection('peserta').insertOne(doc)
        created.push(clean(doc))
      }
      await syncSheetAppend(db, created)
      return json({ team_id, team_name, count: created.length, members: created })
    }
    if (p[0] === 'peserta' && p[1] && p[2] === 'status' && method === 'PUT') {
      const u = await getUser(request)
      if (!u) return json({ error: 'Akses ditolak' }, 403)
      const b = await request.json()
      await db.collection('peserta').updateOne({ id: p[1] }, { $set: { status: b.status } })
      const doc = await db.collection('peserta').findOne({ id: p[1] })
      return json(clean(doc))
    }
    if (p[0] === 'peserta' && p[1] && method === 'PUT') {
      const u = await getUser(request)
      if (!u) return json({ error: 'Tidak terautentikasi' }, 401)
      const b = await request.json()
      const set = {}
      ;['participant_name', 'gender', 'nisn', 'ttl', 'madrasah_name', 'lomba_id', 'files', 'status', 'nomor_peserta'].forEach(k => { if (b[k] !== undefined) set[k] = b[k] })
      if (b.lomba_id !== undefined) {
        const lomba = await db.collection('lomba').findOne({ id: b.lomba_id })
        set.lomba_name = lomba ? lomba.name : ''
      }
      const existing = await db.collection('peserta').findOne({ id: p[1] })
      const merged = { ...existing, ...set }
      set.complete = computeComplete(merged)
      await db.collection('peserta').updateOne({ id: p[1] }, { $set: set })
      const doc = await db.collection('peserta').findOne({ id: p[1] })
      return json(clean(doc))
    }
    if (p[0] === 'peserta' && p[1] && method === 'DELETE') {
      const u = await getUser(request)
      if (!u) return json({ error: 'Tidak terautentikasi' }, 401)
      await db.collection('peserta').deleteOne({ id: p[1] })
      return json({ ok: true })
    }

    // ---------- HASIL ----------
    if (route === '/hasil' && method === 'GET') {
      const u = await getUser(request)
      if (!u) return json({ error: 'Tidak terautentikasi' }, 401)
      const url = new URL(request.url)
      const lomba_id = url.searchParams.get('lomba_id') || (u.role === 'panitia' ? u.assigned_lomba_id : null)
      const q = lomba_id ? { lomba_id } : {}
      const list = await db.collection('hasil').find(q).sort({ created_at: -1 }).toArray()
      return json(list.map(clean))
    }
    if (route === '/hasil' && method === 'POST') {
      const u = await getUser(request)
      if (!u) return json({ error: 'Tidak terautentikasi' }, 401)
      const b = await request.json()
      const doc = { id: uuidv4(), lomba_id: b.lomba_id, uploaded_score_sheet_url: b.uploaded_score_sheet_url, note: b.note || '', created_by: u.id, created_at: new Date() }
      await db.collection('hasil').insertOne(doc)
      return json(clean(doc))
    }

    // ---------- JUARA ----------
    if (route === '/juara' && method === 'GET') {
      const u = await getUser(request)
      if (!u) return json({ error: 'Tidak terautentikasi' }, 401)
      const url = new URL(request.url)
      const lomba_id = url.searchParams.get('lomba_id')
      let q = {}
      if (lomba_id) q = { lomba_id }
      else if (u.role === 'panitia') q = { lomba_id: u.assigned_lomba_id }
      const list = await db.collection('juara').find(q).toArray()
      return json(list.map(clean))
    }
    if (route === '/juara' && method === 'POST') {
      const u = await getUser(request)
      if (!u) return json({ error: 'Tidak terautentikasi' }, 401)
      const b = await request.json()
      // one winner per rank per lomba -> upsert
      await db.collection('juara').deleteMany({ lomba_id: b.lomba_id, rank: b.rank })
      const lomba = await db.collection('lomba').findOne({ id: b.lomba_id })
      const isGroup = (b.is_group !== undefined) ? !!b.is_group : (lomba && lomba.type === 'kelompok')
      let doc
      if (isGroup) {
        // group winner keyed by madrasah
        doc = {
          id: uuidv4(), lomba_id: b.lomba_id, peserta_id: null, rank: b.rank,
          is_group: true,
          participant_name: b.madrasah_name || '', madrasah_name: b.madrasah_name || '',
          certificate_url: null, created_at: new Date(),
        }
      } else {
        const peserta = await db.collection('peserta').findOne({ id: b.peserta_id })
        doc = {
          id: uuidv4(), lomba_id: b.lomba_id, peserta_id: b.peserta_id, rank: b.rank,
          is_group: false,
          participant_name: peserta ? peserta.participant_name : '', madrasah_name: peserta ? peserta.madrasah_name : '',
          certificate_url: null, created_at: new Date(),
        }
      }
      await db.collection('juara').insertOne(doc)
      return json(clean(doc))
    }
    if (p[0] === 'juara' && p[1] && method === 'DELETE') {
      const u = await getUser(request)
      if (!u) return json({ error: 'Tidak terautentikasi' }, 401)
      await db.collection('juara').deleteOne({ id: p[1] })
      return json({ ok: true })
    }

    // ---------- TEMPLATES (certificate / idcard) ----------
    if (route === '/templates' && method === 'GET') {
      const url = new URL(request.url)
      const type = url.searchParams.get('type')
      const q = type ? { type } : {}
      const list = await db.collection('templates').find(q).toArray()
      return json(list.map(clean))
    }
    if (route === '/templates' && method === 'POST') {
      const u = await getUser(request)
      if (!u || u.role !== 'super_admin') return json({ error: 'Akses ditolak' }, 403)
      const b = await request.json()
      const existing = await db.collection('templates').findOne({ type: b.type })
      if (existing) {
        await db.collection('templates').updateOne({ type: b.type }, { $set: { image_url: b.image_url, fields: b.fields || [] } })
      } else {
        await db.collection('templates').insertOne({ id: uuidv4(), type: b.type, image_url: b.image_url, fields: b.fields || [], created_at: new Date() })
      }
      const doc = await db.collection('templates').findOne({ type: b.type })
      return json(clean(doc))
    }

    return json({ error: `Route ${route} not found` }, 404)
  } catch (error) {
    console.error('API Error:', error)
    return json({ error: 'Internal server error', detail: String(error && error.message || error) }, 500)
  }
}

export const GET = handleRoute
export const POST = handleRoute
export const PUT = handleRoute
export const DELETE = handleRoute
export const PATCH = handleRoute
