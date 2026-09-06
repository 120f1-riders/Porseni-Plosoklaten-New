'use client'

import { useEffect, useState } from 'react'
import { toast } from 'sonner'
import { Loader2, Trophy, GraduationCap } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Card } from '@/components/ui/card'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { api, setToken } from '@/lib/porseni/api'
import { ROLES, APP_TITLE } from '@/lib/porseni/constants'

export default function Auth({ onAuth }) {
  const [mode, setMode] = useState('login')
  const [loading, setLoading] = useState(false)
  const [lombaList, setLombaList] = useState([])

  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [name, setName] = useState('')
  const [role, setRole] = useState('admin_madrasah')
  const [madrasah, setMadrasah] = useState('')
  const [lombaId, setLombaId] = useState('')

  useEffect(() => {
    api('/lomba').then(setLombaList).catch(() => {})
  }, [])

  const handleLogin = async () => {
    if (!email || !password) return toast.error('User & kata sandi wajib diisi')
    setLoading(true)
    try {
      const res = await api('/auth/login', { method: 'POST', body: { email, password } })
      setToken(res.token)
      toast.success('Berhasil masuk. Selamat datang!')
      onAuth(res.user)
    } catch (e) {
      toast.error(e.message)
    } finally {
      setLoading(false)
    }
  }

  const handleRegister = async () => {
    if (!name || !email || !password || !role) return toast.error('Lengkapi semua data')
    if (role === 'admin_madrasah' && !madrasah) return toast.error('Nama Madrasah wajib diisi')
    if (role === 'panitia' && !lombaId) return toast.error('Cabang Lomba wajib dipilih')
    setLoading(true)
    try {
      const res = await api('/auth/register', {
        method: 'POST',
        body: { name, email, password, role, madrasah_name: role === 'admin_madrasah' ? madrasah : null, assigned_lomba_id: role === 'panitia' ? lombaId : null },
      })
      if (res.pending) {
        toast.success(res.message, { duration: 6000 })
        setMode('login')
      } else {
        setToken(res.token)
        toast.success('Registrasi berhasil!')
        onAuth(res.user)
      }
    } catch (e) {
      toast.error(e.message)
    } finally {
      setLoading(false)
    }
  }

  const handleForgot = async () => {
    if (!email) return toast.error('Masukkan user Anda')
    setLoading(true)
    try {
      const res = await api('/auth/forgot', { method: 'POST', body: { email } })
      toast.success(res.message || 'Permintaan reset terkirim ke Super Admin.', { duration: 8000 })
      setMode('login')
    } catch (e) {
      toast.error(e.message)
    } finally {
      setLoading(false)
    }
  }

  const titles = { login: 'Masuk Akun', register: 'Daftar Akun', forgot: 'Lupa Kata Sandi' }
  const descs = {
    login: 'Silakan masuk untuk melanjutkan.',
    register: 'Lengkapi data untuk membuat akun baru.',
    forgot: 'Masukkan user akun Anda. Permintaan reset akan dikirim ke Super Admin untuk ditetapkan sandi baru.',
  }
  const submitFn = mode === 'login' ? handleLogin : mode === 'register' ? handleRegister : handleForgot
  const submitLabel = mode === 'login' ? 'Masuk' : mode === 'register' ? 'Daftar' : 'Kirim Permintaan Reset'

  return (
    <div className="min-h-screen grid lg:grid-cols-2">
      {/* Brand panel */}
      <div className="hidden lg:flex flex-col justify-between p-12 bg-gradient-to-br from-green-800 via-green-700 to-emerald-600 text-white">
        <div className="flex items-center gap-3">
          <div className="h-12 w-12 rounded-xl bg-white/15 flex items-center justify-center backdrop-blur">
            <GraduationCap className="h-7 w-7" />
          </div>
          <div className="font-semibold text-lg leading-tight">SIM Porseni<br /><span className="text-green-200 text-sm font-normal">MI Kecamatan Plosoklaten</span></div>
        </div>
        <div>
          <Trophy className="h-14 w-14 text-green-200 mb-6" />
          <h1 className="text-4xl font-bold leading-tight">Pekan Olahraga<br />dan Seni Madrasah</h1>
          <p className="text-green-100 mt-4 max-w-md">Kelola pendaftaran peserta, penilaian lomba, cetak administrasi, ID card, dan sertifikat juara dalam satu sistem terpadu.</p>
        </div>
        <p className="text-green-200 text-sm">Kementerian Agama - Kecamatan Plosoklaten</p>
      </div>

      {/* Form panel */}
      <div className="flex items-center justify-center p-6 bg-green-50/50">
        <Card className="w-full max-w-md p-8 shadow-lg">
          <div className="lg:hidden flex items-center gap-2 mb-6 text-primary">
            <GraduationCap className="h-6 w-6" />
            <span className="font-bold">SIM Porseni MI Plosoklaten</span>
          </div>
          <h2 className="text-2xl font-bold">{titles[mode]}</h2>
          <p className="text-muted-foreground text-sm mt-1 mb-6">
            {descs[mode]}
          </p>

          <div className="space-y-4">
            {mode === 'register' && (
              <div className="space-y-1.5">
                <Label>Nama Lengkap</Label>
                <Input value={name} onChange={(e) => setName(e.target.value)} placeholder="Nama Anda" />
              </div>
            )}
            <div className="space-y-1.5">
              <Label>User</Label>
              <Input type="text" value={email} onChange={(e) => setEmail(e.target.value)} placeholder="email atau kode akun" />
            </div>
            {mode !== 'forgot' && (
              <div className="space-y-1.5">
                <div className="flex items-center justify-between">
                  <Label>Kata Sandi</Label>
                  {mode === 'login' && (
                    <button type="button" className="text-xs text-primary hover:underline" onClick={() => setMode('forgot')}>Lupa sandi?</button>
                  )}
                </div>
                <Input type="password" value={password} onChange={(e) => setPassword(e.target.value)} placeholder="••••••••" />
              </div>
            )}

            {mode === 'register' && (
              <>
                <div className="space-y-1.5">
                  <Label>Peran / Role</Label>
                  <Select value={role} onValueChange={setRole}>
                    <SelectTrigger><SelectValue /></SelectTrigger>
                    <SelectContent>
                      {ROLES.map((r) => <SelectItem key={r.value} value={r.value}>{r.label}</SelectItem>)}
                    </SelectContent>
                  </Select>
                </div>
                {role === 'admin_madrasah' && (
                  <div className="space-y-1.5">
                    <Label>Nama Madrasah</Label>
                    <Input value={madrasah} onChange={(e) => setMadrasah(e.target.value)} placeholder="MI ..." />
                  </div>
                )}
                {role === 'panitia' && (
                  <div className="space-y-1.5">
                    <Label>Cabang Lomba</Label>
                    <Select value={lombaId} onValueChange={setLombaId}>
                      <SelectTrigger><SelectValue placeholder="Pilih cabang lomba" /></SelectTrigger>
                      <SelectContent>
                        {lombaList.length === 0 && <div className="px-3 py-2 text-sm text-muted-foreground">Belum ada lomba</div>}
                        {lombaList.map((l) => <SelectItem key={l.id} value={l.id}>{l.name} ({l.category})</SelectItem>)}
                      </SelectContent>
                    </Select>
                  </div>
                )}
              </>
            )}

            <Button className="w-full" disabled={loading} onClick={submitFn}>
              {loading && <Loader2 className="h-4 w-4 mr-2 animate-spin" />}
              {submitLabel}
            </Button>
          </div>

          <div className="text-center text-sm text-muted-foreground mt-6">
            {mode === 'forgot' ? (
              <button className="text-primary font-medium hover:underline" onClick={() => setMode('login')}>Kembali ke halaman Masuk</button>
            ) : (
              <>
                {mode === 'login' ? 'Belum punya akun?' : 'Sudah punya akun?'}{' '}
                <button className="text-primary font-medium hover:underline" onClick={() => setMode(mode === 'login' ? 'register' : 'login')}>
                  {mode === 'login' ? 'Daftar di sini' : 'Masuk di sini'}
                </button>
              </>
            )}
          </div>
        </Card>
      </div>
    </div>
  )
}
