'use client'

import { useEffect, useState } from 'react'
import { Loader2 } from 'lucide-react'
import Auth from '@/components/porseni/Auth'
import Shell from '@/components/porseni/Shell'
import { api, getToken, clearToken } from '@/lib/porseni/api'

function App() {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    (async () => {
      if (getToken()) {
        try {
          const u = await api('/auth/me')
          setUser(u)
        } catch {
          clearToken()
        }
      }
      setLoading(false)
    })()
  }, [])

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-green-50">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    )
  }

  if (!user) return <Auth onAuth={setUser} />
  return <Shell user={user} onLogout={() => { clearToken(); setUser(null) }} />
}

export default App
