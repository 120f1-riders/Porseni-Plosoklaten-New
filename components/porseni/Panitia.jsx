'use client'

import { useEffect, useMemo, useRef, useState } from 'react'
import { toast } from 'sonner'
import { Users, CheckCircle2, Clock, Loader2, Printer, Upload, Award, FileText, Trash2, CheckCircle } from 'lucide-react'
import { Card } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { StatCard, StatusBadge, PageHeader, Empty } from '@/components/porseni/shared'
import { RANKS } from '@/lib/porseni/constants'
import { api, uploadFile, fileUrl } from '@/lib/porseni/api'

export default function Panitia({ view, user }) {
  const [lomba, setLomba] = useState(null)
  const [peserta, setPeserta] = useState([])
  const [juara, setJuara] = useState([])
  const [hasil, setHasil] = useState([])
  const [loading, setLoading] = useState(true)

  const load = async () => {
    setLoading(true)
    try {
      const [ls, p, j, h] = await Promise.all([api('/lomba'), api('/peserta'), api('/juara'), api('/hasil')])
      setLomba(ls.find((l) => l.id === user.assigned_lomba_id) || null)
      setPeserta(p); setJuara(j); setHasil(h)
    } catch (e) { toast.error(e.message) } finally { setLoading(false) }
  }
  useEffect(() => { load() }, [])

  const criteria = useMemo(() => (lomba?.judging_criteria || []).map((c) => (typeof c === 'string' ? c : c.name)), [lomba])

  if (view === 'dashboard') return <Dashboard lomba={lomba} peserta={peserta} loading={loading} />
  if (view === 'cetak') return <Cetak lomba={lomba} peserta={peserta} criteria={criteria} />
  if (view === 'hasil') return <Hasil lomba={lomba} peserta={peserta} juara={juara} hasil={hasil} onChange={load} />
  return <DaftarPeserta lomba={lomba} peserta={peserta} loading={loading} onChange={load} />
}

function Dashboard({ lomba, peserta, loading }) {
  const verified = peserta.filter((p) => p.status === 'verified').length
  return (
    <div>
      <PageHeader title="Dashboard Panitia" desc={lomba ? `Cabang Lomba: ${lomba.name} (${lomba.category})` : 'Belum ada lomba yang ditugaskan'} />
      {loading ? <Loader2 className="h-6 w-6 animate-spin text-primary" /> : (
        <div className="grid gap-4 sm:grid-cols-3">
          <StatCard icon={Users} label="Total Peserta" value={peserta.length} />
          <StatCard icon={CheckCircle2} label="Terverifikasi" value={verified} />
          <StatCard icon={Clock} label="Menunggu" value={peserta.length - verified} />
        </div>
      )}
    </div>
  )
}

function DaftarPeserta({ lomba, peserta, loading, onChange }) {
  const setStatus = async (id, status) => {
    try { await api(`/peserta/${id}/status`, { method: 'PUT', body: { status } }); toast.success('Status diperbarui'); onChange() }
    catch (e) { toast.error(e.message) }
  }
  return (
    <div>
      <PageHeader title="Daftar Peserta" desc={lomba ? lomba.name : ''} />
      <Card>
        {loading ? <div className="p-8"><Loader2 className="h-6 w-6 animate-spin text-primary" /></div> : peserta.length === 0 ? <Empty /> : (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>No. Peserta</TableHead>
                <TableHead>Nama</TableHead>
                <TableHead>Madrasah</TableHead>
                <TableHead>Berkas</TableHead>
                <TableHead>Status</TableHead>
                <TableHead className="text-right">Aksi</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {peserta.map((p) => (
                <TableRow key={p.id}>
                  <TableCell className="font-mono">{p.nomor_peserta}</TableCell>
                  <TableCell className="font-medium">{p.participant_name}</TableCell>
                  <TableCell>{p.madrasah_name}</TableCell>
                  <TableCell>
                    <div className="flex gap-1">
                      {Object.entries(p.files || {}).map(([k, v]) => (
                        <a key={k} href={fileUrl(v.id)} target="_blank" rel="noreferrer" className="text-xs text-primary underline">{k}</a>
                      ))}
                    </div>
                  </TableCell>
                  <TableCell><StatusBadge status={p.status} /></TableCell>
                  <TableCell className="text-right">
                    {p.status !== 'verified'
                      ? <Button size="sm" onClick={() => setStatus(p.id, 'verified')}><CheckCircle className="h-4 w-4 mr-1" />Verifikasi</Button>
                      : <Button size="sm" variant="outline" onClick={() => setStatus(p.id, 'pending')}>Batalkan</Button>}
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

function Cetak({ lomba, peserta, criteria }) {
  const [mode, setMode] = useState('absensi')
  const doPrint = (m) => { setMode(m); setTimeout(() => window.print(), 150) }
  const crit = criteria.length ? criteria : ['Kriteria 1', 'Kriteria 2']

  const Header = (
    <div style={{ textAlign: 'center', borderBottom: '3px double #000', paddingBottom: 12, marginBottom: 20 }}>
      <div style={{ fontSize: 18, fontWeight: 700 }}>PEKAN OLAHRAGA DAN SENI (PORSENI)</div>
      <div style={{ fontSize: 16, fontWeight: 700 }}>MADRASAH IBTIDAIYYAH KECAMATAN PLOSOKLATEN</div>
      <div style={{ fontSize: 14, marginTop: 4 }}>{mode === 'absensi' ? 'DAFTAR HADIR PESERTA' : 'LEMBAR PENILAIAN'} — {lomba?.name || '-'}</div>
    </div>
  )
  const Sign = (label) => (
    <div className="print-sign" style={{ marginTop: 56, display: 'flex', justifyContent: 'flex-end' }}>
      <div style={{ textAlign: 'center', fontSize: 13 }}>
        <div>Plosoklaten, .............................</div>
        <div style={{ marginTop: 4 }}>{label}</div>
        <div style={{ marginTop: 64 }}>( ................................. )</div>
      </div>
    </div>
  )

  const Sheet = (
    <div className="sheet">
      {Header}
      {mode === 'absensi' ? (
        <table className="print-table">
          <thead><tr><th>No</th><th>Nomor Peserta</th><th>Nama</th><th>Madrasah</th><th style={{ width: '25%' }}>Tanda Tangan</th></tr></thead>
          <tbody>
            {peserta.map((p, i) => (
              <tr key={p.id}><td style={{ textAlign: 'center' }}>{i + 1}</td><td style={{ textAlign: 'center' }}>{p.nomor_peserta}</td><td>{p.participant_name}</td><td>{p.madrasah_name}</td><td style={{ height: 34 }}>{(i % 2 === 0) ? '' : ''}</td></tr>
            ))}
            {peserta.length === 0 && <tr><td colSpan={5} style={{ textAlign: 'center' }}>Belum ada peserta</td></tr>}
          </tbody>
        </table>
      ) : (
        <table className="print-table">
          <thead><tr><th>No</th><th>Nomor Peserta</th><th>Nama</th>{crit.map((c, i) => <th key={i}>{c}</th>)}<th>Total</th></tr></thead>
          <tbody>
            {peserta.map((p, i) => (
              <tr key={p.id}><td style={{ textAlign: 'center' }}>{i + 1}</td><td style={{ textAlign: 'center' }}>{p.nomor_peserta}</td><td>{p.participant_name}</td>{crit.map((_, j) => <td key={j} style={{ height: 34 }}></td>)}<td></td></tr>
            ))}
            {peserta.length === 0 && <tr><td colSpan={crit.length + 4} style={{ textAlign: 'center' }}>Belum ada peserta</td></tr>}
          </tbody>
        </table>
      )}
      {Sign(mode === 'absensi' ? 'Panitia / Juri' : 'Juri Lomba')}
    </div>
  )

  return (
    <div>
      <div className="screen-only">
        <PageHeader title="Cetak Administrasi" desc={lomba?.name}>
          <Button variant={mode === 'absensi' ? 'default' : 'outline'} onClick={() => setMode('absensi')}><Printer className="h-4 w-4 mr-1" />Absensi</Button>
          <Button variant={mode === 'penilaian' ? 'default' : 'outline'} onClick={() => setMode('penilaian')}><Printer className="h-4 w-4 mr-1" />Penilaian</Button>
        </PageHeader>
        <div className="flex gap-2 mb-4">
          <Button onClick={() => doPrint('absensi')}><Printer className="h-4 w-4 mr-2" />Cetak Absensi</Button>
          <Button onClick={() => doPrint('penilaian')}><Printer className="h-4 w-4 mr-2" />Cetak Lembar Penilaian</Button>
        </div>
        <Card className="p-2 shadow-inner bg-muted/40">
          <div className="mx-auto max-w-3xl border shadow bg-white">{Sheet}</div>
        </Card>
      </div>
      <div className="print-only">{Sheet}</div>
    </div>
  )
}

function Hasil({ lomba, peserta, juara, hasil, onChange }) {
  const [uploading, setUploading] = useState(false)
  const ref = useRef(null)
  const verified = peserta.filter((p) => p.status === 'verified')

  const upload = async (e) => {
    const file = e.target.files?.[0]
    if (!file) return
    setUploading(true)
    try {
      const res = await uploadFile(file)
      await api('/hasil', { method: 'POST', body: { lomba_id: lomba.id, uploaded_score_sheet_url: res.id, note: res.name } })
      toast.success('Lembar nilai terunggah')
      onChange()
    } catch (err) { toast.error(err.message) } finally { setUploading(false) }
  }

  const assign = async (rank, peserta_id) => {
    try { await api('/juara', { method: 'POST', body: { lomba_id: lomba.id, rank, peserta_id } }); toast.success(`${rank} ditetapkan`); onChange() }
    catch (e) { toast.error(e.message) }
  }
  const removeJuara = async (id) => {
    try { await api(`/juara/${id}`, { method: 'DELETE' }); toast.success('Dihapus'); onChange() } catch (e) { toast.error(e.message) }
  }

  if (!lomba) return <Empty text="Belum ada lomba yang ditugaskan." />

  return (
    <div>
      <PageHeader title="Upload Hasil & Input Juara" desc={lomba.name} />
      <div className="grid lg:grid-cols-2 gap-6">
        <Card className="p-6">
          <h3 className="font-semibold mb-1">Upload Lembar Nilai Fisik</h3>
          <p className="text-sm text-muted-foreground mb-4">Unggah foto / PDF lembar penilaian yang sudah ditandatangani.</p>
          <input ref={ref} type="file" className="hidden" accept="image/*,application/pdf" onChange={upload} />
          <Button variant="secondary" disabled={uploading} onClick={() => ref.current?.click()}>
            {uploading ? <Loader2 className="h-4 w-4 mr-2 animate-spin" /> : <Upload className="h-4 w-4 mr-2" />}Pilih File
          </Button>
          <div className="mt-4 space-y-2">
            {hasil.map((h) => (
              <a key={h.id} href={fileUrl(h.uploaded_score_sheet_url)} target="_blank" rel="noreferrer" className="flex items-center gap-2 text-sm text-primary border rounded-lg p-2 hover:bg-accent">
                <FileText className="h-4 w-4" /> {h.note || 'Lembar nilai'}
              </a>
            ))}
            {hasil.length === 0 && <p className="text-xs text-muted-foreground">Belum ada file diunggah.</p>}
          </div>
        </Card>

        <Card className="p-6">
          <h3 className="font-semibold mb-1 flex items-center gap-2"><Award className="h-4 w-4 text-primary" />Penetapan Juara</h3>
          <p className="text-sm text-muted-foreground mb-4">Pilih peserta untuk setiap peringkat.</p>
          <div className="space-y-3">
            {RANKS.map((rank) => {
              const current = juara.find((j) => j.rank === rank)
              return (
                <div key={rank} className="flex items-center gap-2">
                  <div className="w-24 text-sm font-medium">{rank}</div>
                  <Select value={current?.peserta_id || ''} onValueChange={(v) => assign(rank, v)}>
                    <SelectTrigger className="flex-1"><SelectValue placeholder="Pilih peserta" /></SelectTrigger>
                    <SelectContent>
                      {verified.map((p) => <SelectItem key={p.id} value={p.id}>{p.nomor_peserta} - {p.participant_name}</SelectItem>)}
                      {verified.length === 0 && <div className="px-3 py-2 text-sm text-muted-foreground">Belum ada peserta terverifikasi</div>}
                    </SelectContent>
                  </Select>
                  {current && <Button size="icon" variant="ghost" className="text-destructive" onClick={() => removeJuara(current.id)}><Trash2 className="h-4 w-4" /></Button>}
                </div>
              )
            })}
          </div>
        </Card>
      </div>
    </div>
  )
}
