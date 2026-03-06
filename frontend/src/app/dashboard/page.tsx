'use client'

import { useState, useEffect } from 'react'
import Link from 'next/link'
import { useRouter } from 'next/navigation'

interface UserProfile {
  email: string
  first_name: string
  last_name: string
  profile: {
    skills: string[]
    interests: string[]
    education_level: string
    field_of_study: string
  } | null
}

interface Opportunity {
  id: string
  title: string
  slug: string
  organization: string
  opportunity_type: string
  type_display: string
  location: string
  deadline: string
  time_left: string
  days_until_deadline: number
  featured: boolean
  category_name: string
}

interface Recommendation {
  opportunity: Opportunity
  match_score: number
  match_reasons: string[]
}

export default function DashboardPage() {
  const router = useRouter()
  const [user, setUser] = useState<UserProfile | null>(null)
  const [opportunities, setOpportunities] = useState<Opportunity[]>([])
  const [recommendations, setRecommendations] = useState<Recommendation[]>([])
  const [loading, setLoading] = useState(true)
  const [profileComplete, setProfileComplete] = useState(false)

  useEffect(() => {
    const token = localStorage.getItem('access_token')
    if (!token) {
      router.push('/auth/login')
      return
    }
    loadData(token)
  }, [router])

  const loadData = async (token: string) => {
    try {
      // Charger user + profil
      const userRes = await fetch('http://localhost:8000/api/accounts/users/me/', {
        headers: { Authorization: `Bearer ${token}` },
      })

      if (userRes.status === 401) {
        localStorage.removeItem('access_token')
        localStorage.removeItem('refresh_token')
        router.push('/auth/login')
        return
      }

      if (userRes.ok) {
        const userData = await userRes.json()
        setUser(userData)

        // Vérifier si profil complet
        const profile = userData.profile
        const isComplete = profile &&
          profile.skills?.length > 0 &&
          profile.interests?.length > 0 &&
          profile.education_level
        setProfileComplete(isComplete)
      }

      // Charger les recommandations (si endpoint existe)
      try {
        const recRes = await fetch('http://localhost:8000/api/opportunities/recommendations/', {
          headers: { Authorization: `Bearer ${token}` },
        })
        if (recRes.ok) {
          const recData = await recRes.json()
          setRecommendations(recData.recommendations || recData || [])
        }
      } catch {
        // Endpoint pas encore disponible
      }

      // Charger les opportunités récentes
      const oppRes = await fetch('http://localhost:8000/api/opportunities/')
      if (oppRes.ok) {
        const oppData = await oppRes.json()
        setOpportunities(oppData.results || oppData || [])
      }

    } catch (err) {
      console.error('Erreur chargement:', err)
    } finally {
      setLoading(false)
    }
  }

  const handleLogout = () => {
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    router.push('/')
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

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="w-12 h-12 border-4 border-orange-600 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-gray-500">Chargement de votre espace...</p>
        </div>
      </div>
    )
  }

  return (
    <main className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-4 py-4 flex justify-between items-center">
          <Link href="/" className="text-2xl font-bold">
            Opportu<span className="text-orange-600">CI</span>
          </Link>
          <nav className="flex gap-6 items-center">
            <Link href="/opportunities" className="text-gray-600 hover:text-orange-600">
              Opportunités
            </Link>
            <Link href="/profile" className="text-gray-600 hover:text-orange-600">
              Mon Profil
            </Link>
            <button
              onClick={handleLogout}
              className="text-red-600 hover:text-red-700"
            >
              Déconnexion
            </button>
          </nav>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-4 py-8">
        {/* Welcome Banner */}
        <div className="bg-gradient-to-r from-orange-500 to-orange-600 rounded-2xl p-6 md:p-8 mb-8 text-white">
          <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
            <div>
              <h1 className="text-2xl md:text-3xl font-bold mb-2">
                Bienvenue, {user?.first_name || 'Utilisateur'} !
              </h1>
              <p className="text-orange-100">
                {profileComplete
                  ? 'Découvrez vos opportunités personnalisées'
                  : 'Complétez votre profil pour des recommandations IA personnalisées'
                }
              </p>
            </div>
            {!profileComplete && (
              <Link
                href="/profile"
                className="bg-white text-orange-600 px-6 py-3 rounded-lg font-semibold hover:bg-orange-50 transition-colors"
              >
                Compléter mon profil
              </Link>
            )}
          </div>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
          <div className="bg-white p-5 rounded-xl shadow-sm">
            <div className="text-3xl font-bold text-orange-600">{opportunities.length}</div>
            <div className="text-gray-500 text-sm">Opportunités disponibles</div>
          </div>
          <div className="bg-white p-5 rounded-xl shadow-sm">
            <div className="text-3xl font-bold text-blue-600">
              {opportunities.filter(o => o.opportunity_type === 'scholarship').length}
            </div>
            <div className="text-gray-500 text-sm">Bourses</div>
          </div>
          <div className="bg-white p-5 rounded-xl shadow-sm">
            <div className="text-3xl font-bold text-green-600">
              {opportunities.filter(o => o.opportunity_type === 'job').length}
            </div>
            <div className="text-gray-500 text-sm">Emplois</div>
          </div>
          <div className="bg-white p-5 rounded-xl shadow-sm">
            <div className="text-3xl font-bold text-purple-600">
              {opportunities.filter(o => o.opportunity_type === 'internship').length}
            </div>
            <div className="text-gray-500 text-sm">Stages</div>
          </div>
        </div>

        <div className="grid md:grid-cols-3 gap-8">
          {/* Main Content - Opportunities */}
          <div className="md:col-span-2">
            {/* Featured / Recommandations */}
            {recommendations.length > 0 ? (
              <div className="bg-white rounded-xl shadow-sm p-6 mb-6">
                <h2 className="text-xl font-bold mb-4 flex items-center gap-2">
                  <span className="text-2xl">✨</span>
                  Recommandations IA
                  <span className="text-xs font-normal text-gray-400 bg-gray-100 px-2 py-1 rounded">Gemini</span>
                </h2>
                <div className="space-y-4">
                  {recommendations.slice(0, 5).map((rec) => (
                    <Link
                      key={rec.opportunity.id}
                      href={`/opportunities/${rec.opportunity.slug}`}
                      className="block border rounded-lg p-4 hover:border-orange-300 hover:shadow-md transition-all"
                    >
                      <div className="flex justify-between items-start">
                        <div className="flex-1">
                          <div className="flex items-center gap-2 mb-1">
                            <span className={`text-xs px-2 py-0.5 rounded ${getTypeColor(rec.opportunity.opportunity_type)}`}>
                              {rec.opportunity.type_display}
                            </span>
                            {rec.opportunity.featured && (
                              <span className="text-xs px-2 py-0.5 rounded bg-orange-100 text-orange-800">Featured</span>
                            )}
                          </div>
                          <h3 className="font-semibold text-gray-900">{rec.opportunity.title}</h3>
                          <p className="text-gray-500 text-sm">{rec.opportunity.organization}</p>
                        </div>
                        <div className="text-right ml-4">
                          <div className="text-2xl font-bold text-orange-600">{rec.match_score}%</div>
                          <div className="text-xs text-gray-400">match</div>
                        </div>
                      </div>
                      {rec.match_reasons.length > 0 && (
                        <div className="mt-2 flex flex-wrap gap-1">
                          {rec.match_reasons.slice(0, 2).map((reason, i) => (
                            <span key={i} className="text-xs bg-green-50 text-green-700 px-2 py-0.5 rounded">
                              {reason}
                            </span>
                          ))}
                        </div>
                      )}
                    </Link>
                  ))}
                </div>
              </div>
            ) : null}

            {/* Recent Opportunities */}
            <div className="bg-white rounded-xl shadow-sm p-6">
              <div className="flex justify-between items-center mb-4">
                <h2 className="text-xl font-bold">Opportunités récentes</h2>
                <Link href="/opportunities" className="text-orange-600 hover:text-orange-700 text-sm font-medium">
                  Voir tout &rarr;
                </Link>
              </div>

              <div className="space-y-4">
                {opportunities.slice(0, 6).map((opp) => (
                  <Link
                    key={opp.id}
                    href={`/opportunities/${opp.slug}`}
                    className="block border rounded-lg p-4 hover:border-orange-300 hover:shadow-sm transition-all"
                  >
                    <div className="flex justify-between items-start">
                      <div>
                        <div className="flex items-center gap-2 mb-1">
                          <span className={`text-xs px-2 py-0.5 rounded ${getTypeColor(opp.opportunity_type)}`}>
                            {opp.type_display}
                          </span>
                          {opp.featured && (
                            <span className="text-yellow-500">★</span>
                          )}
                        </div>
                        <h3 className="font-semibold text-gray-900">{opp.title}</h3>
                        <p className="text-gray-500 text-sm">{opp.organization}</p>
                        <p className="text-gray-400 text-xs mt-1">{opp.location}</p>
                      </div>
                      <div className="text-right">
                        <div className={`text-sm font-medium ${opp.days_until_deadline <= 7 ? 'text-red-600' : 'text-gray-600'}`}>
                          {opp.time_left}
                        </div>
                      </div>
                    </div>
                  </Link>
                ))}
              </div>

              {opportunities.length === 0 && (
                <div className="text-center py-8 text-gray-500">
                  Aucune opportunité disponible pour le moment
                </div>
              )}
            </div>
          </div>

          {/* Sidebar */}
          <div className="space-y-6">
            {/* Profile Card */}
            <div className="bg-white rounded-xl shadow-sm p-6">
              <h3 className="font-bold mb-4">Mon Profil</h3>

              {user?.profile ? (
                <div className="space-y-3">
                  <div>
                    <p className="text-sm text-gray-500">Formation</p>
                    <p className="font-medium">
                      {user.profile.education_level
                        ? user.profile.education_level.charAt(0).toUpperCase() + user.profile.education_level.slice(1)
                        : 'Non renseigné'}
                    </p>
                    {user.profile.field_of_study && (
                      <p className="text-sm text-gray-600">{user.profile.field_of_study}</p>
                    )}
                  </div>

                  <div>
                    <p className="text-sm text-gray-500 mb-1">Compétences</p>
                    {user.profile.skills?.length > 0 ? (
                      <div className="flex flex-wrap gap-1">
                        {user.profile.skills.slice(0, 5).map(skill => (
                          <span key={skill} className="text-xs bg-orange-100 text-orange-700 px-2 py-0.5 rounded">
                            {skill}
                          </span>
                        ))}
                        {user.profile.skills.length > 5 && (
                          <span className="text-xs text-gray-400">+{user.profile.skills.length - 5}</span>
                        )}
                      </div>
                    ) : (
                      <p className="text-sm text-gray-400">Aucune compétence</p>
                    )}
                  </div>

                  <div>
                    <p className="text-sm text-gray-500 mb-1">Intérêts</p>
                    {user.profile.interests?.length > 0 ? (
                      <div className="flex flex-wrap gap-1">
                        {user.profile.interests.slice(0, 3).map(interest => (
                          <span key={interest} className="text-xs bg-blue-100 text-blue-700 px-2 py-0.5 rounded">
                            {interest}
                          </span>
                        ))}
                        {user.profile.interests.length > 3 && (
                          <span className="text-xs text-gray-400">+{user.profile.interests.length - 3}</span>
                        )}
                      </div>
                    ) : (
                      <p className="text-sm text-gray-400">Aucun intérêt</p>
                    )}
                  </div>

                  <Link
                    href="/profile"
                    className="block text-center mt-4 py-2 border border-orange-600 text-orange-600 rounded-lg hover:bg-orange-50 text-sm font-medium"
                  >
                    Modifier mon profil
                  </Link>
                </div>
              ) : (
                <div className="text-center py-4">
                  <p className="text-gray-500 text-sm mb-3">Profil non complété</p>
                  <Link
                    href="/profile"
                    className="block py-2 bg-orange-600 text-white rounded-lg hover:bg-orange-700 text-sm font-medium"
                  >
                    Compléter maintenant
                  </Link>
                </div>
              )}
            </div>

            {/* Quick Stats */}
            <div className="bg-white rounded-xl shadow-sm p-6">
              <h3 className="font-bold mb-4">Catégories populaires</h3>
              <div className="space-y-2">
                {[
                  { type: 'scholarship', label: 'Bourses', icon: '🎓' },
                  { type: 'internship', label: 'Stages', icon: '💼' },
                  { type: 'job', label: 'Emplois', icon: '👔' },
                  { type: 'training', label: 'Formations', icon: '📚' },
                  { type: 'competition', label: 'Concours', icon: '🏆' },
                ].map(cat => {
                  const count = opportunities.filter(o => o.opportunity_type === cat.type).length
                  return (
                    <Link
                      key={cat.type}
                      href={`/opportunities?type=${cat.type}`}
                      className="flex items-center justify-between p-2 rounded hover:bg-gray-50"
                    >
                      <span className="flex items-center gap-2">
                        <span>{cat.icon}</span>
                        <span className="text-gray-700">{cat.label}</span>
                      </span>
                      <span className="text-gray-400 text-sm">{count}</span>
                    </Link>
                  )
                })}
              </div>
            </div>

            {/* Urgent Deadlines */}
            <div className="bg-white rounded-xl shadow-sm p-6">
              <h3 className="font-bold mb-4 flex items-center gap-2">
                <span className="text-red-500">⏰</span>
                Deadlines proches
              </h3>
              <div className="space-y-3">
                {opportunities
                  .filter(o => o.days_until_deadline <= 14 && o.days_until_deadline > 0)
                  .sort((a, b) => a.days_until_deadline - b.days_until_deadline)
                  .slice(0, 3)
                  .map(opp => (
                    <Link
                      key={opp.id}
                      href={`/opportunities/${opp.slug}`}
                      className="block p-3 bg-red-50 rounded-lg hover:bg-red-100 transition-colors"
                    >
                      <p className="font-medium text-sm text-gray-900 line-clamp-1">{opp.title}</p>
                      <p className="text-red-600 text-xs font-medium">{opp.time_left}</p>
                    </Link>
                  ))}
                {opportunities.filter(o => o.days_until_deadline <= 14 && o.days_until_deadline > 0).length === 0 && (
                  <p className="text-gray-400 text-sm">Aucune deadline urgente</p>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
    </main>
  )
}
