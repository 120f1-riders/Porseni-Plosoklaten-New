'use client'

import { useEffect, useRef, useState } from 'react'
import { toast } from 'sonner'
import { Users, CheckCircle2, Clock, UserPlus, Loader2, Upload, FileText, Trash2, FolderTree } from 'lucide-react'
import { Card } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { StatCard, StatusBadge, PageHeader, Empty } from '@/components/porseni/shared'
import { api, uploadFile, fileUrl } from '@/lib/porseni/api'

const REQ_FILES = [
  { key: 'akte', label: 'Akte Kelahiran' },
  { key: 'surat_ket', label: 'Surat Keterangan Kepala Madrasah' },
  { key: 'pas_photo', label: 'Pas Photo 3x4 (maks 10MB)' },
]

export default function AdminMadrasah({ view, user }) {
  const [lomba, setLomba] = useState([])
  const [peserta, setPeserta] = useState([])
  const [loading, setLoading] = useState(true)

  const load = async () => {
    setLoading(true)
    try {
      const [l, p] = await Promise.all([api('/lomba'), api('/peserta')])
      setLomba(l); setPeserta(p)
    } catch (e) { toast.error(e.message) } finally { setLoading(false) }
  }
  useEffect(() => { load() }, [])

  if (view === 'dashboard') return <Dashboard user={user} peserta={peserta} loading={loading} />
  if (view === 'pendaftaran') return <Pendaftaran user={user} lomba={lomba} onDone={load} />
  return <DaftarPeserta peserta={peserta} loading={loading} onChange={load} />
}

function Dashboard({ user, peserta, loading }) {
  const verified = peserta.filter((p) => p.status === 'verified').length
  const pending = peserta.filter((p) => p.status === 'pending').length
  return (
    <div>
      <PageHeader title={`Selamat datang, ${user.name}`} desc={user.madrasah_name} />
      {loading ? <Loader2 className="h-6 w-6 animate-spin text-primary" /> : (
        <div className="grid gap-4 sm:grid-cols-3">
          <StatCard icon={Users} label="Total Peserta Terdaftar" value={peserta.length} />
          <StatCard icon={CheckCircle2} label="Terverifikasi" value={verified} />
          <StatCard icon={Clock} label="Menunggu Verifikasi" value={pending} />
        </div>
      )}
      <Card className="p-6 mt-6 bg-primary/5 border-primary/20">
        <div className="flex items-start gap-3">
          <UserPlus className="h-5 w-5 text-primary mt-0.5" />
          <div>
            <div className="font-semibold">Daftarkan peserta lomba</div>
            <p className="text-sm text-muted-foreground mt-1">Gunakan menu <b>Pendaftaran Peserta</b> untuk menambahkan siswa beserta berkas persyaratan (Akte, Surat Keterangan, Pas Photo).</p>
          </div>
        </div>
      </Card>
    </div>
  )
}

function FileUploadRow({ item, value, onUploaded }) {
  const [busy, setBusy] = useState(false)
  const ref = useRef(null)
  const handle = async (e) => {
    const file = e.target.files?.[0]
    if (!file) return
    if (file.size > 10 * 1024 * 1024) { toast.error('Ukuran file maksimal 10MB'); return }
    setBusy(true)
    try {
      const res = await uploadFile(file)
      onUploaded(res)
      toast.success(`${item.label} terunggah`)
    } catch (err) { toast.error(err.message) } finally { setBusy(false) }
  }
  return (
    <div className="flex items-center justify-between gap-3 border rounded-lg p-3">
      <div className="flex items-center gap-2 min-w-0">
        <FileText className="h-4 w-4 text-primary shrink-0" />
        <div className="min-w-0">
          <div className="text-sm font-medium truncate">{item.label}</div>
          {value ? <div className="text-xs text-primary truncate">{value.name}</div> : <div className="text-xs text-muted-foreground">Belum diunggah</div>}
        </div>
      </div>
      <input ref={ref} type="file" className="hidden" onChange={handle} accept={item.key === 'pas_photo' ? 'image/*' : 'image/*,application/pdf'} />
      <Button type="button" size="sm" variant={value ? 'outline' : 'secondary'} disabled={busy} onClick={() => ref.current?.click()}>
        {busy ? <Loader2 className="h-4 w-4 animate-spin" /> : <Upload className="h-4 w-4" />}
        <span className="ml-1">{value ? 'Ganti' : 'Unggah'}</span>
      </Button>
    </div>
  )
}

function Pendaftaran({ user, lomba, onDone }) {
  const [form, setForm] = useState({ participant_name: '', ttl: '', nisn: '', lomba_id: '' })
  const [files, setFiles] = useState({})
  const [saving, setSaving] = useState(false)
  const set = (k, v) => setForm((f) => ({ ...f, [k]: v }))

  const submit = async () => {
    if (!form.participant_name || !form.lomba_id) return toast.error('Nama & Cabang Lomba wajib diisi')
    setSaving(true)
    try {
      const filesPayload = {}
      Object.entries(files).forEach(([k, v]) => { filesPayload[k] = { id: v.id, name: v.name } })
      const res = await api('/peserta', { method: 'POST', body: { ...form, madrasah_name: user.madrasah_name, files: filesPayload } })
      toast.success('Peserta berhasil didaftarkan', {
        description: `Nomor Peserta: ${res.nomor_peserta}. Berkas dikirim ke Google Drive: ${res.drive_path}`,
        duration: 7000,
      })
      setForm({ participant_name: '', ttl: '', nisn: '', lomba_id: '' })
      setFiles({})
      onDone()
    } catch (e) { toast.error(e.message) } finally { setSaving(false) }
  }

  return (
    <div>
      <PageHeader title="Pendaftaran Peserta" desc={`Madrasah: ${user.madrasah_name || '-'}`} />
      <div className="grid lg:grid-cols-2 gap-6">
        <Card className="p-6">
          <h3 className="font-semibold mb-4">Data Peserta</h3>
          <div className="space-y-4">
            <div className="space-y-1.5">
              <Label>Nama Lengkap</Label>
              <Input value={form.participant_name} onChange={(e) => set('participant_name', e.target.value)} placeholder="Nama peserta" />
            </div>
            <div className="space-y-1.5">
              <Label>NISN</Label>
              <Input value={form.nisn} onChange={(e) => set('nisn', e.target.value)} placeholder="Nomor Induk Siswa Nasional" />
            </div>
            <div className="space-y-1.5">
              <Label>Tempat, Tanggal Lahir</Label>
              <Input value={form.ttl} onChange={(e) => set('ttl', e.target.value)} placeholder="Kediri, 01 Januari 2015" />
            </div>
            <div className="space-y-1.5">
              <Label>Asal Madrasah</Label>
              <Input value={user.madrasah_name || ''} disabled />
            </div>
            <div className="space-y-1.5">
              <Label>Cabang Lomba</Label>
              <Select value={form.lomba_id} onValueChange={(v) => set('lomba_id', v)}>
                <SelectTrigger><SelectValue placeholder="Pilih cabang lomba" /></SelectTrigger>
                <SelectContent>
                  {lomba.map((l) => <SelectItem key={l.id} value={l.id}>{l.name} ({l.category})</SelectItem>)}
                </SelectContent>
              </Select>
            </div>
          </div>
        </Card>

        <Card className="p-6">
          <h3 className="font-semibold mb-1">Berkas Persyaratan</h3>
          <p className="text-xs text-muted-foreground mb-4 flex items-center gap-1">
            <FolderTree className="h-3.5 w-3.5" /> Disimpan terstruktur: [Lomba]/[Madrasah]/[Peserta]
          </p>
          <div className="space-y-3">
            {REQ_FILES.map((item) => (
              <FileUploadRow key={item.key} item={item} value={files[item.key]} onUploaded={(res) => setFiles((f) => ({ ...f, [item.key]: res }))} />
            ))}
          </div>
          <Button className="w-full mt-6" disabled={saving} onClick={submit}>
            {saving && <Loader2 className="h-4 w-4 mr-2 animate-spin" />} Daftarkan Peserta
          </Button>
        </Card>
      </div>
    </div>
  )
}

function DaftarPeserta({ peserta, loading, onChange }) {
  const del = async (id) => {
    if (!confirm('Hapus peserta ini?')) return
    try { await api(`/peserta/${id}`, { method: 'DELETE' }); toast.success('Peserta dihapus'); onChange() }
    catch (e) { toast.error(e.message) }
  }
  return (
    <div>
      <PageHeader title="Daftar Peserta Saya" desc="Peserta yang telah Anda daftarkan beserta status verifikasi" />
      <Card>
        {loading ? <div className="p-8"><Loader2 className="h-6 w-6 animate-spin text-primary" /></div> : peserta.length === 0 ? <Empty text="Belum ada peserta terdaftar." /> : (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>No. Peserta</TableHead>
                <TableHead>Nama</TableHead>
                <TableHead>Cabang Lomba</TableHead>
                <TableHead>NISN</TableHead>
                <TableHead>Berkas</TableHead>
                <TableHead>Status</TableHead>
                <TableHead></TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {peserta.map((p) => (
                <TableRow key={p.id}>
                  <TableCell className="font-mono">{p.nomor_peserta}</TableCell>
                  <TableCell className="font-medium">{p.participant_name}</TableCell>
                  <TableCell>{p.lomba_name}</TableCell>
                  <TableCell>{p.nisn || '-'}</TableCell>
                  <TableCell>
                    <div className="flex gap-1">
                      {Object.entries(p.files || {}).map(([k, v]) => (
                        <a key={k} href={fileUrl(v.id)} target="_blank" rel="noreferrer" className="text-xs text-primary underline">{k}</a>
                      ))}
                      {(!p.files || Object.keys(p.files).length === 0) && <span className="text-xs text-muted-foreground">-</span>}
                    </div>
                  </TableCell>
                  <TableCell><StatusBadge status={p.status} /></TableCell>
                  <TableCell>
                    <Button size="icon" variant="ghost" className="text-destructive" onClick={() => del(p.id)}><Trash2 className="h-4 w-4" /></Button>
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
