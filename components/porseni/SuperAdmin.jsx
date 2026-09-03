'use client'

import { useEffect, useMemo, useRef, useState } from 'react'
import { toast } from 'sonner'
import {
  Trophy, Users, GraduationCap, Loader2, Plus, Pencil, Trash2, CheckCircle, ShieldCheck,
  Upload, Award, Download, IdCard, Image as ImageIcon, Printer, UsersRound, User,
} from 'lucide-react'
import { Card } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { Badge } from '@/components/ui/badge'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '@/components/ui/dialog'
import { StatCard, StatusBadge, PageHeader, Empty } from '@/components/porseni/shared'
import OverlayEditor from '@/components/porseni/OverlayEditor'
import { CATEGORIES, LOMBA_TYPES, GENDER_LABEL, ROLE_LABEL, CERT_DEFAULT_FIELDS, IDCARD_PESERTA_FIELDS, IDCARD_PANITIA_FIELDS } from '@/lib/porseni/constants'
import { api, uploadFile, fileUrl } from '@/lib/porseni/api'
import { renderOverlay, downloadDataUrl } from '@/lib/porseni/canvasgen'

export default function SuperAdmin({ view }) {
  if (view === 'lomba') return <ManajemenLomba />
  if (view === 'pengguna') return <ManajemenPengguna />
  if (view === 'pendaftar') return <DataPendaftar />
  if (view === 'sertifikat') return <Sertifikat />
  if (view === 'idcard') return <IdCardManager />
  return <Dashboard />
}

/* ---------------- DASHBOARD ---------------- */
function Dashboard() {
  const [data, setData] = useState({ lomba: [], users: [], peserta: [] })
  const [loading, setLoading] = useState(true)
  useEffect(() => {
    (async () => {
      try {
        const [lomba, users, peserta] = await Promise.all([api('/lomba'), api('/users'), api('/peserta')])
        setData({ lomba, users, peserta })
      } catch (e) { toast.error(e.message) } finally { setLoading(false) }
    })()
  }, [])
  const pendingUsers = data.users.filter((u) => u.status === 'pending').length
  const totalL = data.peserta.filter((p) => p.gender === 'L').length
  const totalP = data.peserta.filter((p) => p.gender === 'P').length
  const perLomba = data.lomba.map((l) => {
    const ps = data.peserta.filter((p) => p.lomba_id === l.id)
    return { ...l, total: ps.length, L: ps.filter((p) => p.gender === 'L').length, P: ps.filter((p) => p.gender === 'P').length }
  }).sort((a, b) => b.total - a.total)
  return (
    <div>
      <PageHeader title="Dashboard Super Admin" desc="Monitoring keseluruhan Porseni MI Plosoklaten" />
      {loading ? <Loader2 className="h-6 w-6 animate-spin text-primary" /> : (
        <>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <StatCard icon={Trophy} label="Cabang Lomba" value={data.lomba.length} />
            <StatCard icon={Users} label="Total Peserta" value={data.peserta.length} />
            <StatCard icon={GraduationCap} label="Pengguna" value={data.users.length} />
            <StatCard icon={ShieldCheck} label="Menunggu Verifikasi" value={pendingUsers} />
          </div>
          <div className="grid gap-4 sm:grid-cols-2 mt-4">
            <StatCard icon={User} label="Peserta Laki-laki" value={totalL} />
            <StatCard icon={UsersRound} label="Peserta Perempuan" value={totalP} />
          </div>
          <Card className="mt-6">
            <div className="p-5 border-b">
              <h3 className="font-semibold">Rekap Pendaftar per Cabang Lomba</h3>
              <p className="text-sm text-muted-foreground">Jumlah peserta terdaftar untuk setiap cabang lomba</p>
            </div>
            {perLomba.length === 0 ? <Empty text="Belum ada cabang lomba." /> : (
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Cabang Lomba</TableHead>
                    <TableHead>Kategori</TableHead>
                    <TableHead>Jenis</TableHead>
                    <TableHead className="text-center">Laki-laki</TableHead>
                    <TableHead className="text-center">Perempuan</TableHead>
                    <TableHead className="text-center">Total</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {perLomba.map((l) => (
                    <TableRow key={l.id}>
                      <TableCell className="font-medium">{l.name}</TableCell>
                      <TableCell><Badge variant={l.category === 'Seni' ? 'secondary' : 'default'}>{l.category}</Badge></TableCell>
                      <TableCell><Badge variant="outline">{l.type === 'kelompok' ? 'Kelompok' : 'Individu'}</Badge></TableCell>
                      <TableCell className="text-center">{l.L}</TableCell>
                      <TableCell className="text-center">{l.P}</TableCell>
                      <TableCell className="text-center font-semibold">{l.total}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            )}
          </Card>
        </>
      )}
    </div>
  )
}

/* ---------------- MANAJEMEN LOMBA ---------------- */
function ManajemenLomba() {
  const [list, setList] = useState([])
  const [loading, setLoading] = useState(true)
  const [open, setOpen] = useState(false)
  const [edit, setEdit] = useState(null)
  const [form, setForm] = useState({ name: '', category: 'Olahraga', type: 'individu', criteria: '' })

  const load = async () => { setLoading(true); try { setList(await api('/lomba')) } catch (e) { toast.error(e.message) } finally { setLoading(false) } }
  useEffect(() => { load() }, [])

  const openNew = () => { setEdit(null); setForm({ name: '', category: 'Olahraga', type: 'individu', criteria: '' }); setOpen(true) }
  const openEdit = (l) => { setEdit(l); setForm({ name: l.name, category: l.category, type: l.type || 'individu', criteria: (l.judging_criteria || []).map((c) => (typeof c === 'string' ? c : c.name)).join(', ') }); setOpen(true) }

  const save = async () => {
    if (!form.name) return toast.error('Nama lomba wajib diisi')
    const body = { name: form.name, category: form.category, type: form.type, judging_criteria: form.criteria.split(',').map((s) => s.trim()).filter(Boolean) }
    try {
      if (edit) await api(`/lomba/${edit.id}`, { method: 'PUT', body })
      else await api('/lomba', { method: 'POST', body })
      toast.success('Lomba disimpan'); setOpen(false); load()
    } catch (e) { toast.error(e.message) }
  }
  const del = async (id) => { if (!confirm('Hapus lomba?')) return; try { await api(`/lomba/${id}`, { method: 'DELETE' }); toast.success('Dihapus'); load() } catch (e) { toast.error(e.message) } }

  return (
    <div>
      <PageHeader title="Manajemen Lomba" desc="Kelola cabang lomba Olahraga & Seni">
        <Button onClick={openNew}><Plus className="h-4 w-4 mr-1" />Tambah Lomba</Button>
      </PageHeader>
      <Card>
        {loading ? <div className="p-8"><Loader2 className="h-6 w-6 animate-spin text-primary" /></div> : list.length === 0 ? <Empty text="Belum ada lomba. Tambahkan cabang lomba pertama." /> : (
          <Table>
            <TableHeader><TableRow><TableHead>Nama Lomba</TableHead><TableHead>Kategori</TableHead><TableHead>Jenis</TableHead><TableHead>Kriteria Penilaian</TableHead><TableHead className="text-right">Aksi</TableHead></TableRow></TableHeader>
            <TableBody>
              {list.map((l) => (
                <TableRow key={l.id}>
                  <TableCell className="font-medium">{l.name}</TableCell>
                  <TableCell><Badge variant={l.category === 'Seni' ? 'secondary' : 'default'}>{l.category}</Badge></TableCell>
                  <TableCell><Badge variant="outline">{l.type === 'kelompok' ? 'Kelompok' : 'Individu'}</Badge></TableCell>
                  <TableCell className="text-sm text-muted-foreground">{(l.judging_criteria || []).map((c) => (typeof c === 'string' ? c : c.name)).join(', ') || '-'}</TableCell>
                  <TableCell className="text-right">
                    <Button size="icon" variant="ghost" onClick={() => openEdit(l)}><Pencil className="h-4 w-4" /></Button>
                    <Button size="icon" variant="ghost" className="text-destructive" onClick={() => del(l.id)}><Trash2 className="h-4 w-4" /></Button>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
      </Card>

      <Dialog open={open} onOpenChange={setOpen}>
        <DialogContent>
          <DialogHeader><DialogTitle>{edit ? 'Edit Lomba' : 'Tambah Lomba'}</DialogTitle></DialogHeader>
          <div className="space-y-4">
            <div className="space-y-1.5"><Label>Nama Lomba</Label><Input value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} placeholder="Kaligrafi / Futsal / ..." /></div>
            <div className="space-y-1.5">
              <Label>Kategori</Label>
              <Select value={form.category} onValueChange={(v) => setForm({ ...form, category: v })}>
                <SelectTrigger><SelectValue /></SelectTrigger>
                <SelectContent>{CATEGORIES.map((c) => <SelectItem key={c} value={c}>{c}</SelectItem>)}</SelectContent>
              </Select>
            </div>
            <div className="space-y-1.5">
              <Label>Jenis Lomba</Label>
              <Select value={form.type} onValueChange={(v) => setForm({ ...form, type: v })}>
                <SelectTrigger><SelectValue /></SelectTrigger>
                <SelectContent>{LOMBA_TYPES.map((t) => <SelectItem key={t.value} value={t.value}>{t.label}</SelectItem>)}</SelectContent>
              </Select>
              <p className="text-xs text-muted-foreground">Kelompok: juara ditetapkan per Madrasah, sertifikat dapat dicetak untuk seluruh anggota regu.</p>
            </div>
            <div className="space-y-1.5"><Label>Kriteria Penilaian (pisahkan dengan koma)</Label><Textarea value={form.criteria} onChange={(e) => setForm({ ...form, criteria: e.target.value })} placeholder="Kerapian, Keindahan, Ketepatan" /></div>
          </div>
          <DialogFooter><Button variant="outline" onClick={() => setOpen(false)}>Batal</Button><Button onClick={save}>Simpan</Button></DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}

/* ---------------- MANAJEMEN PENGGUNA ---------------- */
function ManajemenPengguna() {
  const [users, setUsers] = useState([])
  const [lomba, setLomba] = useState([])
  const [loading, setLoading] = useState(true)
  const load = async () => { setLoading(true); try { const [u, l] = await Promise.all([api('/users'), api('/lomba')]); setUsers(u); setLomba(l) } catch (e) { toast.error(e.message) } finally { setLoading(false) } }
  useEffect(() => { load() }, [])
  const lombaName = (id) => lomba.find((l) => l.id === id)?.name || '-'
  const verify = async (id, status) => { try { await api(`/users/${id}`, { method: 'PUT', body: { status } }); toast.success('Status diperbarui'); load() } catch (e) { toast.error(e.message) } }
  const del = async (id) => { if (!confirm('Hapus pengguna?')) return; try { await api(`/users/${id}`, { method: 'DELETE' }); toast.success('Dihapus'); load() } catch (e) { toast.error(e.message) } }

  return (
    <div>
      <PageHeader title="Manajemen Pengguna" desc="Verifikasi akun Admin Madrasah & Panitia Lomba" />
      <Card>
        {loading ? <div className="p-8"><Loader2 className="h-6 w-6 animate-spin text-primary" /></div> : (
          <Table>
            <TableHeader><TableRow><TableHead>Nama</TableHead><TableHead>Email</TableHead><TableHead>Peran</TableHead><TableHead>Keterangan</TableHead><TableHead>Status</TableHead><TableHead className="text-right">Aksi</TableHead></TableRow></TableHeader>
            <TableBody>
              {users.map((u) => (
                <TableRow key={u.id}>
                  <TableCell className="font-medium">{u.name}</TableCell>
                  <TableCell className="text-sm">{u.email}</TableCell>
                  <TableCell><Badge variant="outline">{ROLE_LABEL[u.role]}</Badge></TableCell>
                  <TableCell className="text-sm text-muted-foreground">{u.role === 'admin_madrasah' ? u.madrasah_name : u.role === 'panitia' ? lombaName(u.assigned_lomba_id) : '-'}</TableCell>
                  <TableCell><StatusBadge status={u.status} /></TableCell>
                  <TableCell className="text-right whitespace-nowrap">
                    {u.status !== 'verified'
                      ? <Button size="sm" onClick={() => verify(u.id, 'verified')}><CheckCircle className="h-4 w-4 mr-1" />Verifikasi</Button>
                      : u.role !== 'super_admin' && <Button size="sm" variant="outline" onClick={() => verify(u.id, 'pending')}>Nonaktifkan</Button>}
                    {u.role !== 'super_admin' && <Button size="icon" variant="ghost" className="text-destructive ml-1" onClick={() => del(u.id)}><Trash2 className="h-4 w-4" /></Button>}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
      </Card>
    </div>
  )
}

/* ---------------- DATA PENDAFTAR (cetak keseluruhan) ---------------- */
function DataPendaftar() {
  const [peserta, setPeserta] = useState([])
  const [lomba, setLomba] = useState([])
  const [loading, setLoading] = useState(true)
  const [lombaFilter, setLombaFilter] = useState('all')
  const [genderFilter, setGenderFilter] = useState('all')

  useEffect(() => {
    (async () => {
      try {
        const [p, l] = await Promise.all([api('/peserta'), api('/lomba')])
        setPeserta(p || []); setLomba(l || [])
      } catch (e) { toast.error(e.message) } finally { setLoading(false) }
    })()
  }, [])

  const rows = peserta
    .filter((p) => lombaFilter === 'all' ? true : p.lomba_id === lombaFilter)
    .filter((p) => genderFilter === 'all' ? true : p.gender === genderFilter)

  const doPrint = () => setTimeout(() => window.print(), 150)

  const Sheet = (
    <div className="sheet">
      <div style={{ textAlign: 'center', borderBottom: '3px double #000', paddingBottom: 12, marginBottom: 20 }}>
        <div style={{ fontSize: 18, fontWeight: 700 }}>PEKAN OLAHRAGA DAN SENI (PORSENI)</div>
        <div style={{ fontSize: 16, fontWeight: 700 }}>MADRASAH IBTIDAIYYAH KECAMATAN PLOSOKLATEN</div>
        <div style={{ fontSize: 14, marginTop: 4 }}>DAFTAR SELURUH PESERTA{lombaFilter !== 'all' ? ' — ' + (lomba.find((l) => l.id === lombaFilter)?.name || '') : ''}</div>
      </div>
      <table className="print-table">
        <thead><tr><th>No</th><th>No. Peserta</th><th>Nama</th><th>L/P</th><th>Asal Madrasah</th><th>Cabang Lomba</th><th>Status</th></tr></thead>
        <tbody>
          {rows.map((p, i) => (
            <tr key={p.id}>
              <td style={{ textAlign: 'center' }}>{i + 1}</td>
              <td style={{ textAlign: 'center' }}>{p.nomor_peserta}</td>
              <td>{p.participant_name}</td>
              <td style={{ textAlign: 'center' }}>{p.gender || '-'}</td>
              <td>{p.madrasah_name}</td>
              <td>{p.lomba_name}</td>
              <td style={{ textAlign: 'center' }}>{p.status === 'verified' ? 'Terverifikasi' : 'Menunggu'}</td>
            </tr>
          ))}
          {rows.length === 0 && <tr><td colSpan={7} style={{ textAlign: 'center' }}>Belum ada peserta</td></tr>}
        </tbody>
      </table>
      <div style={{ marginTop: 16, fontSize: 13 }}>Total: {rows.length} peserta</div>
    </div>
  )

  return (
    <div>
      <div className="screen-only">
        <PageHeader title="Data Pendaftar" desc="Seluruh peserta lintas madrasah & cabang lomba">
          <Button onClick={doPrint}><Printer className="h-4 w-4 mr-2" />Cetak Semua</Button>
        </PageHeader>
        <Card className="p-4 mb-4 flex flex-wrap items-center gap-3">
          <div className="flex items-center gap-2">
            <span className="text-sm text-muted-foreground">Cabang Lomba:</span>
            <Select value={lombaFilter} onValueChange={setLombaFilter}>
              <SelectTrigger className="w-56"><SelectValue /></SelectTrigger>
              <SelectContent>
                <SelectItem value="all">Semua Lomba</SelectItem>
                {lomba.map((l) => <SelectItem key={l.id} value={l.id}>{l.name}</SelectItem>)}
              </SelectContent>
            </Select>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-sm text-muted-foreground">Jenis Kelamin:</span>
            <Select value={genderFilter} onValueChange={setGenderFilter}>
              <SelectTrigger className="w-40"><SelectValue /></SelectTrigger>
              <SelectContent>
                <SelectItem value="all">Semua</SelectItem>
                <SelectItem value="L">Laki-laki</SelectItem>
                <SelectItem value="P">Perempuan</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <span className="text-xs text-muted-foreground">{rows.length} peserta</span>
        </Card>
        <Card>
          {loading ? <div className="p-8"><Loader2 className="h-6 w-6 animate-spin text-primary" /></div> : rows.length === 0 ? <Empty text="Belum ada peserta." /> : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>No. Peserta</TableHead>
                  <TableHead>Nama</TableHead>
                  <TableHead>L/P</TableHead>
                  <TableHead>Asal Madrasah</TableHead>
                  <TableHead>Cabang Lomba</TableHead>
                  <TableHead>Kelengkapan</TableHead>
                  <TableHead>Status</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {rows.map((p) => (
                  <TableRow key={p.id}>
                    <TableCell className="font-mono">{p.nomor_peserta}</TableCell>
                    <TableCell className="font-medium">{p.participant_name}</TableCell>
                    <TableCell>{GENDER_LABEL[p.gender] ? p.gender : '-'}</TableCell>
                    <TableCell>{p.madrasah_name}</TableCell>
                    <TableCell>{p.lomba_name}</TableCell>
                    <TableCell>{p.complete ? <Badge className="bg-emerald-600 text-white">Lengkap</Badge> : <Badge variant="outline" className="text-amber-700 border-amber-300">Belum</Badge>}</TableCell>
                    <TableCell><StatusBadge status={p.status} /></TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </Card>
      </div>
      <div className="print-only">{Sheet}</div>
    </div>
  )
}

/* ---------------- TEMPLATE STUDIO (reusable) ---------------- */
function TemplateStudio({ type, defaultFields, targets, loadingTargets, sample }) {
  const [imageUrl, setImageUrl] = useState(null)
  const [fields, setFields] = useState(defaultFields)
  const [loaded, setLoaded] = useState(false)
  const [uploading, setUploading] = useState(false)
  const [saving, setSaving] = useState(false)
  const [generating, setGenerating] = useState(false)
  const ref = useRef(null)

  useEffect(() => {
    (async () => {
      try {
        const list = await api(`/templates?type=${type}`)
        if (list[0]) { setImageUrl(list[0].image_url); if (list[0].fields?.length) setFields(list[0].fields) }
      } catch (e) { /* ignore */ } finally { setLoaded(true) }
    })()
  }, [type])

  const upload = async (e) => {
    const file = e.target.files?.[0]; if (!file) return
    setUploading(true)
    try { const res = await uploadFile(file); setImageUrl(fileUrl(res.id)); toast.success('Template diunggah') }
    catch (err) { toast.error(err.message) } finally { setUploading(false) }
  }
  const save = async () => {
    if (!imageUrl) return toast.error('Unggah template terlebih dahulu')
    setSaving(true)
    try { await api('/templates', { method: 'POST', body: { type, image_url: imageUrl, fields } }); toast.success('Template tersimpan') }
    catch (e) { toast.error(e.message) } finally { setSaving(false) }
  }
  const generateAll = async () => {
    if (!imageUrl) return toast.error('Unggah template terlebih dahulu')
    if (!targets.length) return toast.error('Belum ada data untuk digenerate')
    setGenerating(true)
    try {
      for (const t of targets) {
        const dataUrl = await renderOverlay({ templateSrc: imageUrl, fields, values: t.values })
        downloadDataUrl(dataUrl, t.filename)
        await new Promise((r) => setTimeout(r, 250))
      }
      toast.success(`${targets.length} file berhasil digenerate`)
    } catch (e) { toast.error('Gagal generate: ' + e.message) } finally { setGenerating(false) }
  }
  const generateOne = async (t) => {
    try { const dataUrl = await renderOverlay({ templateSrc: imageUrl, fields, values: t.values }); downloadDataUrl(dataUrl, t.filename) }
    catch (e) { toast.error(e.message) }
  }

  if (!loaded) return <Loader2 className="h-6 w-6 animate-spin text-primary" />

  return (
    <div className="space-y-6">
      <Card className="p-6">
        <div className="flex flex-wrap items-center gap-3 mb-4">
          <input ref={ref} type="file" accept="image/*" className="hidden" onChange={upload} />
          <Button variant="secondary" disabled={uploading} onClick={() => ref.current?.click()}>
            {uploading ? <Loader2 className="h-4 w-4 mr-2 animate-spin" /> : <Upload className="h-4 w-4 mr-2" />}
            {imageUrl ? 'Ganti Template' : 'Unggah Template (Gambar)'}
          </Button>
          {imageUrl && <Button onClick={save} disabled={saving}>{saving ? <Loader2 className="h-4 w-4 mr-2 animate-spin" /> : null}Simpan Tata Letak</Button>}
        </div>
        {imageUrl ? (
          <OverlayEditor templateSrc={imageUrl} fields={fields} onChange={setFields} sampleValues={sample} />
        ) : (
          <div className="border-2 border-dashed rounded-lg py-16 text-center text-muted-foreground">
            <ImageIcon className="h-10 w-10 mx-auto mb-3 opacity-50" />
            Unggah gambar template (JPG/PNG) untuk mulai menata teks.
          </div>
        )}
      </Card>

      <Card className="p-6">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h3 className="font-semibold">Generate ({targets.length})</h3>
            <p className="text-sm text-muted-foreground">Hasil diunduh sebagai gambar PNG siap cetak.</p>
          </div>
          <Button onClick={generateAll} disabled={generating || !imageUrl || !targets.length}>
            {generating ? <Loader2 className="h-4 w-4 mr-2 animate-spin" /> : <Download className="h-4 w-4 mr-2" />}Unduh Semua
          </Button>
        </div>
        {loadingTargets ? <Loader2 className="h-5 w-5 animate-spin text-primary" /> : targets.length === 0 ? <Empty text="Belum ada data." /> : (
          <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-2">
            {targets.map((t, i) => (
              <div key={i} className="flex items-center justify-between border rounded-lg px-3 py-2 text-sm">
                <span className="truncate">{t.label}</span>
                <Button size="icon" variant="ghost" disabled={!imageUrl} onClick={() => generateOne(t)}><Download className="h-4 w-4" /></Button>
              </div>
            ))}
          </div>
        )}
      </Card>
    </div>
  )
}

/* ---------------- SERTIFIKAT ---------------- */
function Sertifikat() {
  const [raw, setRaw] = useState({ loading: true, juara: [], peserta: [], lomba: [] })
  const [groupMode, setGroupMode] = useState('peserta') // 'peserta' | 'regu'

  useEffect(() => {
    (async () => {
      try {
        const [juara, peserta, lomba] = await Promise.all([api('/juara'), api('/peserta'), api('/lomba')])
        setRaw({ loading: false, juara: juara || [], peserta: peserta || [], lomba: lomba || [] })
      } catch (e) { toast.error(e.message); setRaw({ loading: false, juara: [], peserta: [], lomba: [] }) }
    })()
  }, [])

  const lm = Object.fromEntries((raw.lomba || []).map((l) => [l.id, l.name]))
  const targets = []
  for (const j of raw.juara || []) {
    const lombaName = lm[j.lomba_id] || ''
    if (j.is_group) {
      if (groupMode === 'regu') {
        targets.push({
          label: `${j.rank} - ${j.madrasah_name} (Regu)`,
          filename: `Sertifikat_${j.rank}_${(j.madrasah_name || 'regu').replace(/\s+/g, '_')}.png`,
          values: { participant_name: j.madrasah_name, madrasah_name: j.madrasah_name, lomba_name: lombaName, rank: j.rank },
        })
      } else {
        const members = (raw.peserta || []).filter((p) => p.lomba_id === j.lomba_id && p.madrasah_name === j.madrasah_name)
        if (members.length === 0) {
          targets.push({
            label: `${j.rank} - ${j.madrasah_name} (tidak ada anggota)`,
            filename: `Sertifikat_${(j.madrasah_name || 'regu').replace(/\s+/g, '_')}.png`,
            values: { participant_name: j.madrasah_name, madrasah_name: j.madrasah_name, lomba_name: lombaName, rank: j.rank },
          })
        }
        members.forEach((p) => targets.push({
          label: `${j.rank} - ${p.participant_name} (${j.madrasah_name})`,
          filename: `Sertifikat_${(p.participant_name || 'peserta').replace(/\s+/g, '_')}.png`,
          values: { participant_name: p.participant_name, madrasah_name: p.madrasah_name, lomba_name: lombaName, rank: j.rank },
        }))
      }
    } else {
      targets.push({
        label: `${j.rank} - ${j.participant_name}`,
        filename: `Sertifikat_${(j.participant_name || 'peserta').replace(/\s+/g, '_')}.png`,
        values: { participant_name: j.participant_name, madrasah_name: j.madrasah_name, lomba_name: lombaName, rank: j.rank },
      })
    }
  }

  const hasGroup = (raw.juara || []).some((j) => j.is_group)

  return (
    <div>
      <PageHeader title="Manajemen Sertifikat" desc="Unggah template, atur posisi teks, lalu generate sertifikat untuk seluruh juara" />
      {hasGroup && (
        <Card className="p-4 mb-6 flex flex-wrap items-center gap-3">
          <span className="text-sm font-medium">Mode Sertifikat Kelompok:</span>
          <Button size="sm" variant={groupMode === 'peserta' ? 'default' : 'outline'} onClick={() => setGroupMode('peserta')}>Per Peserta (semua anggota regu)</Button>
          <Button size="sm" variant={groupMode === 'regu' ? 'default' : 'outline'} onClick={() => setGroupMode('regu')}>Per Regu / Madrasah</Button>
        </Card>
      )}
      <TemplateStudio
        type="certificate"
        defaultFields={CERT_DEFAULT_FIELDS}
        targets={targets}
        loadingTargets={raw.loading}
        sample={{ participant_name: 'Ahmad Fauzi', madrasah_name: 'MI Al-Hidayah', lomba_name: 'Kaligrafi', rank: 'Juara 1' }}
      />
    </div>
  )
}

/* ---------------- ID CARD ---------------- */
function IdCardManager() {
  const [tab, setTab] = useState('peserta')
  return (
    <div>
      <PageHeader title="Manajemen ID Card" desc="Unggah template kartu identitas & cetak untuk Peserta dan Panitia" />
      <div className="flex gap-2 mb-6">
        <Button variant={tab === 'peserta' ? 'default' : 'outline'} onClick={() => setTab('peserta')}><IdCard className="h-4 w-4 mr-1" />ID Card Peserta</Button>
        <Button variant={tab === 'panitia' ? 'default' : 'outline'} onClick={() => setTab('panitia')}><IdCard className="h-4 w-4 mr-1" />ID Card Panitia</Button>
      </div>
      {tab === 'peserta' ? <IdCardPeserta /> : <IdCardPanitia />}
    </div>
  )
}

function IdCardPeserta() {
  const [state, setState] = useState({ loading: true, targets: [] })
  useEffect(() => {
    (async () => {
      try {
        const peserta = await api('/peserta')
        const targets = peserta.map((p) => ({
          label: `${p.nomor_peserta} - ${p.participant_name}`,
          filename: `IDCard_${(p.participant_name || 'peserta').replace(/\s+/g, '_')}.png`,
          values: { participant_name: p.participant_name, madrasah_name: p.madrasah_name, lomba_name: p.lomba_name, nomor_peserta: 'No. ' + p.nomor_peserta, photo: p.files?.pas_photo ? fileUrl(p.files.pas_photo.id) : null },
        }))
        setState({ loading: false, targets })
      } catch (e) { toast.error(e.message); setState({ loading: false, targets: [] }) }
    })()
  }, [])
  return (
    <TemplateStudio type="idcard_peserta" defaultFields={IDCARD_PESERTA_FIELDS} targets={state.targets} loadingTargets={state.loading}
      sample={{ participant_name: 'Ahmad Fauzi', madrasah_name: 'MI Al-Hidayah', lomba_name: 'Kaligrafi', nomor_peserta: 'No. 001' }} />
  )
}

function IdCardPanitia() {
  const [state, setState] = useState({ loading: true, targets: [] })
  useEffect(() => {
    (async () => {
      try {
        const [users, lomba] = await Promise.all([api('/users'), api('/lomba')])
        const lm = Object.fromEntries(lomba.map((l) => [l.id, l.name]))
        const targets = users.filter((u) => u.role === 'panitia').map((u) => ({
          label: u.name,
          filename: `IDCard_Panitia_${u.name.replace(/\s+/g, '_')}.png`,
          values: { name: u.name, role_label: 'Panitia / Juri', lomba_name: lm[u.assigned_lomba_id] || '-', photo: null },
        }))
        setState({ loading: false, targets })
      } catch (e) { toast.error(e.message); setState({ loading: false, targets: [] }) }
    })()
  }, [])
  return (
    <TemplateStudio type="idcard_panitia" defaultFields={IDCARD_PANITIA_FIELDS} targets={state.targets} loadingTargets={state.loading}
      sample={{ name: 'Budi Santoso', role_label: 'Panitia / Juri', lomba_name: 'Futsal' }} />
  )
}
