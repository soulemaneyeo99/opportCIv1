'use client'

import { useState, useEffect, Suspense } from 'react'
import Link from 'next/link'
import { useSearchParams, useRouter } from 'next/navigation'

interface Opportunity {
  id: string
  title: string
  slug: string
  organization: string
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
  description?: string
  compensation?: string
}

const FILTERS = [
  { value: 'all', label: 'Toutes', icon: '📋' },
  { value: 'scholarship', label: 'Bourses', icon: '🎓' },
  { value: 'internship', label: 'Stages', icon: '💼' },
  { value: 'job', label: 'Emplois', icon: '👔' },
  { value: 'training', label: 'Formations', icon: '📚' },
  { value: 'competition', label: 'Concours', icon: '🏆' },
]

function OpportunitiesContent() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const typeFilter = searchParams.get('type')

  const [opportunities, setOpportunities] = useState<Opportunity[]>([])
  const [loading, setLoading] = useState(true)
  const [filter, setFilter] = useState(typeFilter || 'all')
  const [search, setSearch] = useState('')
  const [isLoggedIn, setIsLoggedIn] = useState(false)

  useEffect(() => {
    setIsLoggedIn(!!localStorage.getItem('access_token'))
  }, [])

  useEffect(() => {
    fetchOpportunities()
  }, [filter])

  const fetchOpportunities = async () => {
    setLoading(true)
    try {
      let url = 'http://localhost:8000/api/opportunities/'
      if (filter && filter !== 'all') {
        url += `?opportunity_type=${filter}`
      }
      const res = await fetch(url)
      const data = await res.json()
      setOpportunities(data.results || data || [])
    } catch (err) {
      console.error('Erreur:', err)
    } finally {
      setLoading(false)
    }
  }

  const filteredOpportunities = opportunities.filter(opp => {
    if (!search) return true
    const searchLower = search.toLowerCase()
    return (
      opp.title.toLowerCase().includes(searchLower) ||
      opp.organization.toLowerCase().includes(searchLower) ||
      opp.location?.toLowerCase().includes(searchLower)
    )
  })

  const getTypeColor = (type: string) => {
    const colors: Record<string, string> = {
      scholarship: 'bg-purple-100 text-purple-800 border-purple-200',
      internship: 'bg-blue-100 text-blue-800 border-blue-200',
      job: 'bg-green-100 text-green-800 border-green-200',
      training: 'bg-yellow-100 text-yellow-800 border-yellow-200',
      competition: 'bg-red-100 text-red-800 border-red-200',
    }
    return colors[type] || 'bg-gray-100 text-gray-800 border-gray-200'
  }

  const handleFilterChange = (value: string) => {
    setFilter(value)
    const newUrl = value === 'all' ? '/opportunities' : `/opportunities?type=${value}`
    router.push(newUrl, { scroll: false })
  }

  return (
    <main className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-4 py-4 flex justify-between items-center">
          <Link href="/" className="text-2xl font-bold">
            Opportu<span className="text-orange-600">CI</span>
          </Link>
          <nav className="flex gap-4 items-center">
            {isLoggedIn ? (
              <>
                <Link href="/dashboard" className="text-gray-600 hover:text-orange-600">
                  Dashboard
                </Link>
                <Link href="/profile" className="text-gray-600 hover:text-orange-600">
                  Mon Profil
                </Link>
              </>
            ) : (
              <>
                <Link href="/auth/login" className="text-gray-600 hover:text-orange-600">
                  Connexion
                </Link>
                <Link href="/auth/register" className="px-4 py-2 bg-orange-600 text-white rounded-lg hover:bg-orange-700">
                  S&apos;inscrire
                </Link>
              </>
            )}
          </nav>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-4 py-8">
        {/* Hero Section */}
        <div className="text-center mb-8">
          <h1 className="text-3xl md:text-4xl font-bold mb-4">
            Découvre les opportunités pour <span className="text-orange-600">réussir</span>
          </h1>
          <p className="text-gray-600 max-w-2xl mx-auto">
            Bourses, stages, emplois et formations sélectionnés pour les jeunes ivoiriens
          </p>
        </div>

        {/* Search Bar */}
        <div className="max-w-2xl mx-auto mb-8">
          <div className="relative">
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Rechercher une opportunité, organisation..."
              className="w-full px-5 py-4 pl-12 border border-gray-200 rounded-xl shadow-sm focus:ring-2 focus:ring-orange-500 focus:border-orange-500 text-lg"
            />
            <svg
              className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
            {search && (
              <button
                onClick={() => setSearch('')}
                className="absolute right-4 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
              >
                &times;
              </button>
            )}
          </div>
        </div>

        {/* Filter Pills */}
        <div className="flex gap-2 mb-8 flex-wrap justify-center">
          {FILTERS.map((option) => (
            <button
              key={option.value}
              onClick={() => handleFilterChange(option.value)}
              className={`px-4 py-2 rounded-full transition-all flex items-center gap-2 ${
                filter === option.value
                  ? 'bg-orange-600 text-white shadow-md'
                  : 'bg-white text-gray-700 hover:bg-orange-50 border border-gray-200'
              }`}
            >
              <span>{option.icon}</span>
              <span>{option.label}</span>
              {filter !== option.value && (
                <span className="text-xs text-gray-400">
                  ({option.value === 'all'
                    ? opportunities.length
                    : opportunities.filter(o => o.opportunity_type === option.value).length})
                </span>
              )}
            </button>
          ))}
        </div>

        {/* Results Count */}
        <div className="mb-6 text-gray-600">
          <span className="font-semibold text-gray-900">{filteredOpportunities.length}</span> opportunité(s) trouvée(s)
          {search && <span> pour &quot;{search}&quot;</span>}
        </div>

        {/* Opportunities Grid */}
        {loading ? (
          <div className="text-center py-12">
            <div className="w-12 h-12 border-4 border-orange-600 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
            <p className="text-gray-600">Chargement des opportunités...</p>
          </div>
        ) : filteredOpportunities.length === 0 ? (
          <div className="text-center py-12 bg-white rounded-xl shadow-sm">
            <div className="text-4xl mb-4">🔍</div>
            <p className="text-gray-600 text-lg">Aucune opportunité trouvée</p>
            <p className="text-sm text-gray-400 mt-2">Essayez de modifier vos filtres ou votre recherche</p>
            {search && (
              <button
                onClick={() => setSearch('')}
                className="mt-4 text-orange-600 hover:text-orange-700"
              >
                Effacer la recherche
              </button>
            )}
          </div>
        ) : (
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
            {filteredOpportunities.map((opp) => (
              <Link
                key={opp.id}
                href={`/opportunities/${opp.slug}`}
                className={`bg-white rounded-xl shadow-sm hover:shadow-lg transition-all p-6 border-2 ${
                  opp.featured ? 'border-orange-400' : 'border-transparent'
                } hover:border-orange-300`}
              >
                {/* Header */}
                <div className="flex items-start justify-between mb-3">
                  <span className={`text-xs px-2.5 py-1 rounded-full border ${getTypeColor(opp.opportunity_type)}`}>
                    {opp.type_display}
                  </span>
                  {opp.featured && (
                    <span className="text-orange-500" title="Mise en avant">★</span>
                  )}
                </div>

                {/* Title */}
                <h3 className="text-lg font-semibold mb-2 line-clamp-2 text-gray-900 group-hover:text-orange-600">
                  {opp.title}
                </h3>

                {/* Organization */}
                <p className="text-gray-600 text-sm mb-3">{opp.organization}</p>

                {/* Location */}
                <div className="flex items-center gap-2 text-sm text-gray-500 mb-4">
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
                  </svg>
                  <span>{opp.location || 'Non spécifié'}</span>
                  {opp.is_remote && (
                    <span className="bg-green-100 text-green-700 text-xs px-2 py-0.5 rounded">Remote</span>
                  )}
                </div>

                {/* Deadline */}
                <div className="flex justify-between items-center pt-4 border-t border-gray-100">
                  <span className={`text-sm font-medium ${
                    opp.is_expired
                      ? 'text-red-600'
                      : opp.days_until_deadline <= 7
                        ? 'text-orange-600'
                        : 'text-gray-600'
                  }`}>
                    {opp.is_expired ? '❌ Expiré' : `⏰ ${opp.time_left}`}
                  </span>
                  <span className="text-orange-600 text-sm font-medium group-hover:underline">
                    Voir détails →
                  </span>
                </div>
              </Link>
            ))}
          </div>
        )}

        {/* CTA for non-logged users */}
        {!isLoggedIn && filteredOpportunities.length > 0 && (
          <div className="mt-12 text-center bg-gradient-to-r from-orange-500 to-orange-600 rounded-2xl p-8 text-white">
            <h2 className="text-2xl font-bold mb-2">Reçois des recommandations personnalisées</h2>
            <p className="text-orange-100 mb-6">
              Inscris-toi gratuitement et notre IA te proposera les meilleures opportunités selon ton profil
            </p>
            <Link
              href="/auth/register"
              className="inline-block bg-white text-orange-600 px-8 py-3 rounded-lg font-semibold hover:bg-orange-50 transition-colors"
            >
              Créer mon compte gratuit
            </Link>
          </div>
        )}
      </div>
    </main>
  )
}

export default function OpportunitiesPage() {
  return (
    <Suspense fallback={
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="w-12 h-12 border-4 border-orange-600 border-t-transparent rounded-full animate-spin"></div>
      </div>
    }>
      <OpportunitiesContent />
    </Suspense>
  )
}
