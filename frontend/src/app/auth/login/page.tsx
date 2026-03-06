'use client'

import { useState } from 'react'
import Link from 'next/link'
import { useRouter } from 'next/navigation'

export default function LoginPage() {
  const router = useRouter()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setError('')

    try {
      const res = await fetch('http://localhost:8000/api/accounts/auth/login/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password }),
      })

      if (!res.ok) {
        throw new Error('Email ou mot de passe incorrect')
      }

      const data = await res.json()
      localStorage.setItem('access_token', data.access)
      localStorage.setItem('refresh_token', data.refresh)
      router.push('/dashboard')
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Erreur de connexion')
    } finally {
      setLoading(false)
    }
  }

  return (
    <main className="min-h-screen bg-gradient-to-br from-orange-50 to-orange-100 flex items-center justify-center">
      <div className="bg-white p-8 rounded-xl shadow-lg w-full max-w-md">
        <h1 className="text-2xl font-bold text-center mb-6">
          Connexion à <span className="text-orange-600">OpportuCI</span>
        </h1>

        {error && (
          <div className="bg-red-100 text-red-700 p-3 rounded-lg mb-4">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-gray-700 mb-2">Email</label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-orange-500 focus:border-transparent"
              placeholder="votre@email.com"
              required
            />
          </div>

          <div>
            <label className="block text-gray-700 mb-2">Mot de passe</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-orange-500 focus:border-transparent"
              placeholder="••••••••"
              required
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full py-3 bg-orange-600 text-white rounded-lg hover:bg-orange-700 disabled:opacity-50"
          >
            {loading ? 'Connexion...' : 'Se connecter'}
          </button>
        </form>

        <p className="text-center mt-6 text-gray-600">
          Pas encore de compte ?{' '}
          <Link href="/auth/register" className="text-orange-600 hover:underline">
            S&apos;inscrire
          </Link>
        </p>

        <p className="text-center mt-4">
          <Link href="/" className="text-gray-500 hover:text-orange-600">
            ← Retour à l&apos;accueil
          </Link>
        </p>
      </div>
    </main>
  )
}
