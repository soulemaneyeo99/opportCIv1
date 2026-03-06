'use client'

import { useState } from 'react'
import Link from 'next/link'
import { useRouter } from 'next/navigation'

export default function RegisterPage() {
  const router = useRouter()
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    confirm_password: '',
    first_name: '',
    last_name: '',
    terms: true,
  })
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFormData({ ...formData, [e.target.name]: e.target.value })
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setError('')

    if (formData.password !== formData.confirm_password) {
      setError('Les mots de passe ne correspondent pas')
      setLoading(false)
      return
    }

    try {
      const res = await fetch('http://localhost:8000/api/accounts/auth/register/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData),
      })

      if (!res.ok) {
        const data = await res.json()
        // Handle the custom error format from backend
        const errors = data.errors || data
        if (errors.email) throw new Error(errors.email[0] || errors.email)
        if (errors.password) throw new Error(errors.password[0] || errors.password)
        if (errors.confirm_password) throw new Error(errors.confirm_password[0] || errors.confirm_password)
        throw new Error(errors.detail || 'Erreur lors de l\'inscription')
      }

      router.push('/auth/login?registered=true')
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Erreur d\'inscription')
    } finally {
      setLoading(false)
    }
  }

  return (
    <main className="min-h-screen bg-gradient-to-br from-orange-50 to-orange-100 flex items-center justify-center py-12">
      <div className="bg-white p-8 rounded-xl shadow-lg w-full max-w-md">
        <h1 className="text-2xl font-bold text-center mb-6">
          Rejoindre <span className="text-orange-600">OpportuCI</span>
        </h1>

        {error && (
          <div className="bg-red-100 text-red-700 p-3 rounded-lg mb-4">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-gray-700 mb-2">Prénom</label>
              <input
                type="text"
                name="first_name"
                value={formData.first_name}
                onChange={handleChange}
                className="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-orange-500"
                required
              />
            </div>
            <div>
              <label className="block text-gray-700 mb-2">Nom</label>
              <input
                type="text"
                name="last_name"
                value={formData.last_name}
                onChange={handleChange}
                className="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-orange-500"
                required
              />
            </div>
          </div>

          <div>
            <label className="block text-gray-700 mb-2">Email</label>
            <input
              type="email"
              name="email"
              value={formData.email}
              onChange={handleChange}
              className="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-orange-500"
              placeholder="votre@email.com"
              required
            />
          </div>

          <div>
            <label className="block text-gray-700 mb-2">Mot de passe</label>
            <input
              type="password"
              name="password"
              value={formData.password}
              onChange={handleChange}
              className="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-orange-500"
              placeholder="••••••••"
              required
              minLength={8}
            />
          </div>

          <div>
            <label className="block text-gray-700 mb-2">Confirmer le mot de passe</label>
            <input
              type="password"
              name="confirm_password"
              value={formData.confirm_password}
              onChange={handleChange}
              className="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-orange-500"
              placeholder="••••••••"
              required
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full py-3 bg-orange-600 text-white rounded-lg hover:bg-orange-700 disabled:opacity-50"
          >
            {loading ? 'Inscription...' : 'S\'inscrire'}
          </button>
        </form>

        <p className="text-center mt-6 text-gray-600">
          Déjà un compte ?{' '}
          <Link href="/auth/login" className="text-orange-600 hover:underline">
            Se connecter
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
