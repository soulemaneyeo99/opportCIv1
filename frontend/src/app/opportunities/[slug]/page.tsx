'use client'

import { useState, useEffect } from 'react'
import Link from 'next/link'
import { useParams, useRouter } from 'next/navigation'

interface OpportunitySource {
  id: number
  name: string
  source_type: string
  url: string | null
}

interface OpportunityDetail {
  id: string
  title: string
  slug: string
  description: string
  organization: string
  organization_logo: string | null
  opportunity_type: string
  type_display: string
  category_name: string
  location: string
  is_remote: boolean
  deadline: string
  days_until_deadline: number
  is_expired: boolean
  time_left: string
  featured: boolean
  application_link: string
  requirements: string
  education_level: string
  skills_required: string[]
  experience_years: number
  compensation: string
  publication_date: string
  view_count: number
  source: OpportunitySource | null
  external_id: string | null
}

export default function OpportunityDetailPage() {
  const params = useParams()
  const router = useRouter()
  const slug = params.slug as string

  const [opportunity, setOpportunity] = useState<OpportunityDetail | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [isLoggedIn, setIsLoggedIn] = useState(false)
  const [saved, setSaved] = useState(false)

  useEffect(() => {
    setIsLoggedIn(!!localStorage.getItem('access_token'))
    fetchOpportunity()
  }, [slug])

  const fetchOpportunity = async () => {
    try {
      const res = await fetch(`http://localhost:8000/api/opportunities/${slug}/`)
      if (!res.ok) {
        if (res.status === 404) {
          setError('Opportunité non trouvée')
        } else {
          setError('Erreur lors du chargement')
        }
        return
      }
      const data = await res.json()
      setOpportunity(data)
    } catch (err) {
      setError('Erreur de connexion')
    } finally {
      setLoading(false)
    }
  }

  const getTypeColor = (type: string) => {
    const colors: Record<string, string> = {
      scholarship: 'bg-purple-100 text-purple-800',
      internship: 'bg-blue-100 text-blue-800',
      job: 'bg-green-100 text-green-800',
      training: 'bg-yellow-100 text-yellow-800',
      competition: 'bg-red-100 text-red-800',
    }
    return colors[type] || 'bg-gray-100 text-gray-800'
  }

  const getEducationLabel = (level: string) => {
    const labels: Record<string, string> = {
      secondary: 'Secondaire',
      bac: 'Baccalauréat',
      bts: 'BTS/DUT (Bac+2)',
      license: 'Licence (Bac+3)',
      master: 'Master (Bac+5)',
      phd: 'Doctorat (Bac+8)',
      any: 'Tous niveaux',
    }
    return labels[level] || level
  }

  const handleSave = async () => {
    if (!isLoggedIn) {
      router.push('/auth/login')
      return
    }
    setSaved(!saved)
    // TODO: API call to save opportunity
  }

  const handleApply = () => {
    if (opportunity?.application_link) {
      window.open(opportunity.application_link, '_blank')
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="w-12 h-12 border-4 border-orange-600 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-gray-500">Chargement...</p>
        </div>
      </div>
    )
  }

  if (error || !opportunity) {
    return (
      <div className="min-h-screen bg-gray-50">
        <header className="bg-white shadow-sm">
          <div className="max-w-4xl mx-auto px-4 py-4">
            <Link href="/" className="text-2xl font-bold">
              Opportu<span className="text-orange-600">CI</span>
            </Link>
          </div>
        </header>
        <div className="max-w-4xl mx-auto px-4 py-16 text-center">
          <div className="text-6xl mb-4">😕</div>
          <h1 className="text-2xl font-bold mb-2">{error || 'Opportunité non trouvée'}</h1>
          <p className="text-gray-600 mb-6">Cette opportunité n&apos;existe pas ou a été supprimée</p>
          <Link
            href="/opportunities"
            className="inline-block px-6 py-3 bg-orange-600 text-white rounded-lg hover:bg-orange-700"
          >
            Voir toutes les opportunités
          </Link>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm sticky top-0 z-10">
        <div className="max-w-4xl mx-auto px-4 py-4 flex justify-between items-center">
          <Link href="/" className="text-2xl font-bold">
            Opportu<span className="text-orange-600">CI</span>
          </Link>
          <nav className="flex gap-4 items-center">
            <Link href="/opportunities" className="text-gray-600 hover:text-orange-600">
              ← Retour
            </Link>
            {isLoggedIn ? (
              <Link href="/dashboard" className="text-gray-600 hover:text-orange-600">
                Dashboard
              </Link>
            ) : (
              <Link href="/auth/login" className="text-orange-600 hover:text-orange-700">
                Connexion
              </Link>
            )}
          </nav>
        </div>
      </header>

      <main className="max-w-4xl mx-auto px-4 py-8">
        {/* Demo Data Banner - Only shows if no external_id (seed data) */}
        {!opportunity.external_id && (
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
            <div className="flex items-start gap-3">
              <span className="text-blue-500 text-xl flex-shrink-0">ℹ️</span>
              <div>
                <p className="text-blue-800 font-medium">Mode Démonstration</p>
                <p className="text-blue-700 text-sm mt-1">
                  Cette opportunité est un <strong>exemple de test</strong>. En production, les opportunités seront
                  récupérées automatiquement depuis des sources comme GreatYop, Afri-Carrières, etc.,
                  avec des liens directs vers les vraies offres.
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Breadcrumb */}
        <nav className="text-sm text-gray-500 mb-6">
          <Link href="/opportunities" className="hover:text-orange-600">Opportunités</Link>
          <span className="mx-2">/</span>
          <span className="text-gray-700">{opportunity.type_display}</span>
        </nav>

        <div className="grid md:grid-cols-3 gap-8">
          {/* Main Content */}
          <div className="md:col-span-2">
            <div className="bg-white rounded-xl shadow-sm p-6 md:p-8">
              {/* Header */}
              <div className="mb-6">
                <div className="flex items-center gap-3 mb-4">
                  <span className={`px-3 py-1 rounded-full text-sm ${getTypeColor(opportunity.opportunity_type)}`}>
                    {opportunity.type_display}
                  </span>
                  {opportunity.featured && (
                    <span className="bg-orange-100 text-orange-800 px-3 py-1 rounded-full text-sm">
                      ★ Mise en avant
                    </span>
                  )}
                  {opportunity.is_remote && (
                    <span className="bg-green-100 text-green-800 px-3 py-1 rounded-full text-sm">
                      Remote
                    </span>
                  )}
                </div>

                <h1 className="text-2xl md:text-3xl font-bold text-gray-900 mb-3">
                  {opportunity.title}
                </h1>

                <div className="flex flex-wrap items-center gap-4 text-gray-600">
                  <span className="flex items-center gap-1">
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
                    </svg>
                    {opportunity.organization}
                  </span>
                  <span className="flex items-center gap-1">
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                    </svg>
                    {opportunity.location || 'Non spécifié'}
                  </span>
                </div>
              </div>

              {/* Description */}
              <div className="prose prose-gray max-w-none mb-8">
                <h2 className="text-xl font-semibold mb-4">Description</h2>
                <div className="whitespace-pre-wrap text-gray-700 leading-relaxed">
                  {opportunity.description}
                </div>
              </div>

              {/* Requirements */}
              {opportunity.requirements && (
                <div className="mb-8">
                  <h2 className="text-xl font-semibold mb-4">Conditions requises</h2>
                  <div className="whitespace-pre-wrap text-gray-700">
                    {opportunity.requirements}
                  </div>
                </div>
              )}

              {/* Skills */}
              {opportunity.skills_required?.length > 0 && (
                <div className="mb-8">
                  <h2 className="text-xl font-semibold mb-4">Compétences recherchées</h2>
                  <div className="flex flex-wrap gap-2">
                    {opportunity.skills_required.map((skill, idx) => (
                      <span
                        key={idx}
                        className="bg-gray-100 text-gray-700 px-3 py-1.5 rounded-full text-sm"
                      >
                        {skill}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Sidebar */}
          <div className="space-y-6">
            {/* Apply Card */}
            <div className="bg-white rounded-xl shadow-sm p-6 sticky top-24">
              {/* Deadline */}
              <div className={`text-center p-4 rounded-lg mb-6 ${
                opportunity.is_expired
                  ? 'bg-red-50'
                  : opportunity.days_until_deadline <= 7
                    ? 'bg-orange-50'
                    : 'bg-green-50'
              }`}>
                <div className={`text-2xl font-bold ${
                  opportunity.is_expired
                    ? 'text-red-600'
                    : opportunity.days_until_deadline <= 7
                      ? 'text-orange-600'
                      : 'text-green-600'
                }`}>
                  {opportunity.is_expired ? 'Expiré' : opportunity.time_left}
                </div>
                <div className="text-sm text-gray-600">
                  {opportunity.is_expired
                    ? 'Cette opportunité est terminée'
                    : 'pour postuler'}
                </div>
              </div>

              {/* Compensation */}
              {opportunity.compensation && (
                <div className="mb-6">
                  <p className="text-sm text-gray-500 mb-1">Rémunération</p>
                  <p className="font-semibold text-gray-900">{opportunity.compensation}</p>
                </div>
              )}

              {/* Education Level */}
              {opportunity.education_level && opportunity.education_level !== 'any' && (
                <div className="mb-6">
                  <p className="text-sm text-gray-500 mb-1">Niveau requis</p>
                  <p className="font-semibold text-gray-900">{getEducationLabel(opportunity.education_level)}</p>
                </div>
              )}

              {/* Experience */}
              {opportunity.experience_years > 0 && (
                <div className="mb-6">
                  <p className="text-sm text-gray-500 mb-1">Expérience</p>
                  <p className="font-semibold text-gray-900">{opportunity.experience_years} an(s) minimum</p>
                </div>
              )}

              {/* Actions */}
              {!opportunity.is_expired && (
                <div className="space-y-3">
                  {/* Demo data - no real link */}
                  {!opportunity.external_id ? (
                    <div className="text-center">
                      <button
                        disabled
                        className="w-full py-3 bg-gray-200 text-gray-500 rounded-lg font-semibold cursor-not-allowed mb-2"
                      >
                        Postuler (Démo)
                      </button>
                      <p className="text-xs text-gray-400">
                        Opportunité de démonstration - pas de lien réel
                      </p>
                    </div>
                  ) : opportunity.application_link ? (
                    <a
                      href={opportunity.application_link}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="w-full py-3 bg-orange-600 text-white rounded-lg hover:bg-orange-700 font-semibold transition-colors flex items-center justify-center gap-2"
                    >
                      Postuler sur le site officiel
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                      </svg>
                    </a>
                  ) : (
                    <button
                      disabled
                      className="w-full py-3 bg-gray-300 text-gray-500 rounded-lg font-semibold cursor-not-allowed"
                    >
                      Lien non disponible
                    </button>
                  )}
                  <button
                    onClick={handleSave}
                    className={`w-full py-3 border rounded-lg font-medium transition-colors ${
                      saved
                        ? 'border-orange-600 text-orange-600 bg-orange-50'
                        : 'border-gray-300 text-gray-700 hover:border-orange-600 hover:text-orange-600'
                    }`}
                  >
                    {saved ? '✓ Sauvegardé' : 'Sauvegarder'}
                  </button>
                </div>
              )}

              {/* Share */}
              <div className="mt-6 pt-6 border-t">
                <p className="text-sm text-gray-500 mb-3">Partager</p>
                <div className="flex gap-2">
                  <button
                    onClick={() => {
                      navigator.clipboard.writeText(window.location.href)
                      alert('Lien copié!')
                    }}
                    className="flex-1 py-2 border border-gray-200 rounded-lg text-sm hover:bg-gray-50"
                  >
                    📋 Copier le lien
                  </button>
                </div>
              </div>
            </div>

            {/* Info Card */}
            <div className="bg-white rounded-xl shadow-sm p-6">
              <h3 className="font-semibold mb-4">Informations</h3>
              <div className="space-y-3 text-sm">
                <div className="flex justify-between">
                  <span className="text-gray-500">Publié</span>
                  <span className="text-gray-900">
                    {new Date(opportunity.publication_date).toLocaleDateString('fr-FR')}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-500">Catégorie</span>
                  <span className="text-gray-900">{opportunity.category_name}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-500">Vues</span>
                  <span className="text-gray-900">{opportunity.view_count}</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* CTA */}
        {!isLoggedIn && (
          <div className="mt-12 bg-gradient-to-r from-orange-500 to-orange-600 rounded-2xl p-8 text-white text-center">
            <h2 className="text-2xl font-bold mb-2">Tu recherches d&apos;autres opportunités ?</h2>
            <p className="text-orange-100 mb-6">
              Crée ton profil et reçois des recommandations personnalisées par notre IA
            </p>
            <Link
              href="/auth/register"
              className="inline-block bg-white text-orange-600 px-8 py-3 rounded-lg font-semibold hover:bg-orange-50"
            >
              Créer mon compte gratuit
            </Link>
          </div>
        )}
      </main>
    </div>
  )
}
