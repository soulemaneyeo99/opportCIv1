'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'

interface UserData {
  id: number
  email: string
  first_name: string
  last_name: string
  user_type: string
  phone_number: string | null
}

interface ProfileData {
  city: string
  education_level: string
  field_of_study: string
  institution: string
  graduation_year: number | null
  skills: string[]
  interests: string[]
  languages: string[]
  bio: string
  linkedin_url: string
  portfolio_url: string
}

const CITIES = [
  { value: 'abidjan', label: 'Abidjan' },
  { value: 'bouake', label: 'Bouaké' },
  { value: 'daloa', label: 'Daloa' },
  { value: 'yamoussoukro', label: 'Yamoussoukro' },
  { value: 'san_pedro', label: 'San-Pédro' },
  { value: 'korhogo', label: 'Korhogo' },
  { value: 'man', label: 'Man' },
  { value: 'other', label: 'Autre ville' },
]

const EDUCATION_LEVELS = [
  { value: 'secondary', label: 'Secondaire' },
  { value: 'bac', label: 'Baccalauréat' },
  { value: 'bts', label: 'BTS/DUT (Bac+2)' },
  { value: 'license', label: 'Licence (Bac+3)' },
  { value: 'master', label: 'Master (Bac+5)' },
  { value: 'phd', label: 'Doctorat (Bac+8)' },
]

const SUGGESTED_SKILLS = [
  'Python', 'JavaScript', 'React', 'Django', 'Excel', 'Word', 'PowerPoint',
  'Communication', 'Leadership', 'Gestion de projet', 'Marketing Digital',
  'Comptabilité', 'Anglais', 'Analyse de données', 'Design Graphique',
  'SQL', 'Java', 'Vente', 'Négociation', 'Rédaction', 'Photoshop',
]

const SUGGESTED_INTERESTS = [
  'Tech & Innovation', 'Finance & Banque', 'Santé', 'Éducation',
  'Environnement', 'Entrepreneuriat', 'Marketing', 'Ressources Humaines',
  'Droit', 'Agriculture', 'Commerce International', 'Art & Culture',
  'ONG & Développement', 'Télécommunications', 'Énergie',
]

const LANGUAGES = ['Français', 'Anglais', 'Espagnol', 'Arabe', 'Chinois', 'Allemand']

export default function ProfilePage() {
  const router = useRouter()
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')
  const [user, setUser] = useState<UserData | null>(null)
  const [completionScore, setCompletionScore] = useState(0)

  const [profile, setProfile] = useState<ProfileData>({
    city: 'abidjan',
    education_level: '',
    field_of_study: '',
    institution: '',
    graduation_year: null,
    skills: [],
    interests: [],
    languages: ['Français'],
    bio: '',
    linkedin_url: '',
    portfolio_url: '',
  })

  const [newSkill, setNewSkill] = useState('')

  useEffect(() => {
    fetchProfile()
  }, [])

  useEffect(() => {
    calculateCompletion()
  }, [profile])

  const calculateCompletion = () => {
    let score = 0
    if (profile.city) score += 10
    if (profile.education_level) score += 15
    if (profile.field_of_study) score += 10
    if (profile.institution) score += 5
    if (profile.skills.length > 0) score += 20
    if (profile.skills.length >= 3) score += 10
    if (profile.interests.length > 0) score += 15
    if (profile.interests.length >= 3) score += 5
    if (profile.bio && profile.bio.length > 50) score += 10
    setCompletionScore(Math.min(100, score))
  }

  const fetchProfile = async () => {
    const token = localStorage.getItem('access_token')
    if (!token) {
      router.push('/auth/login')
      return
    }

    try {
      const res = await fetch('http://localhost:8000/api/accounts/users/me/', {
        headers: { 'Authorization': `Bearer ${token}` }
      })

      if (res.status === 401) {
        localStorage.removeItem('access_token')
        localStorage.removeItem('refresh_token')
        router.push('/auth/login')
        return
      }

      if (res.ok) {
        const data = await res.json()
        setUser({
          id: data.id,
          email: data.email,
          first_name: data.first_name,
          last_name: data.last_name,
          user_type: data.user_type,
          phone_number: data.phone_number,
        })

        if (data.profile) {
          setProfile({
            city: data.profile.city || 'abidjan',
            education_level: data.profile.education_level || '',
            field_of_study: data.profile.field_of_study || '',
            institution: data.profile.institution || '',
            graduation_year: data.profile.graduation_year,
            skills: data.profile.skills || [],
            interests: data.profile.interests || [],
            languages: data.profile.languages?.length > 0 ? data.profile.languages : ['Français'],
            bio: data.profile.bio || '',
            linkedin_url: data.profile.linkedin_url || '',
            portfolio_url: data.profile.portfolio_url || '',
          })
        }
      }
    } catch (err) {
      setError('Erreur de connexion au serveur')
    } finally {
      setLoading(false)
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setSaving(true)
    setError('')
    setSuccess('')

    const token = localStorage.getItem('access_token')
    if (!token) {
      router.push('/auth/login')
      return
    }

    try {
      const res = await fetch('http://localhost:8000/api/accounts/users/update_profile/', {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(profile)
      })

      if (res.ok) {
        setSuccess('Profil mis à jour avec succès!')
        setTimeout(() => router.push('/dashboard'), 1500)
      } else {
        const data = await res.json()
        const errorMsg = data.errors?.detail || data.detail || 'Erreur lors de la mise à jour'
        setError(typeof errorMsg === 'string' ? errorMsg : JSON.stringify(errorMsg))
      }
    } catch (err) {
      setError('Erreur de connexion au serveur')
    } finally {
      setSaving(false)
    }
  }

  const addSkill = (skill: string) => {
    const trimmed = skill.trim()
    if (trimmed && !profile.skills.includes(trimmed) && profile.skills.length < 15) {
      setProfile({ ...profile, skills: [...profile.skills, trimmed] })
    }
    setNewSkill('')
  }

  const removeSkill = (skill: string) => {
    setProfile({ ...profile, skills: profile.skills.filter(s => s !== skill) })
  }

  const toggleInterest = (interest: string) => {
    if (profile.interests.includes(interest)) {
      setProfile({ ...profile, interests: profile.interests.filter(i => i !== interest) })
    } else if (profile.interests.length < 10) {
      setProfile({ ...profile, interests: [...profile.interests, interest] })
    }
  }

  const toggleLanguage = (lang: string) => {
    if (profile.languages.includes(lang)) {
      if (profile.languages.length > 1) {
        setProfile({ ...profile, languages: profile.languages.filter(l => l !== lang) })
      }
    } else {
      setProfile({ ...profile, languages: [...profile.languages, lang] })
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="w-12 h-12 border-4 border-orange-600 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-gray-500">Chargement du profil...</p>
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
          <nav className="flex items-center gap-6">
            <Link href="/opportunities" className="text-gray-600 hover:text-orange-600">
              Opportunités
            </Link>
            <Link href="/dashboard" className="text-gray-600 hover:text-orange-600">
              Dashboard
            </Link>
          </nav>
        </div>
      </header>

      <main className="max-w-4xl mx-auto px-4 py-8">
        {/* Progress Card */}
        <div className="bg-gradient-to-r from-orange-500 to-orange-600 rounded-xl p-6 mb-6 text-white">
          <div className="flex justify-between items-center mb-3">
            <div>
              <h2 className="text-xl font-semibold">
                {user ? `${user.first_name} ${user.last_name}` : 'Mon Profil'}
              </h2>
              <p className="text-orange-100">Complète ton profil pour de meilleures recommandations</p>
            </div>
            <div className="text-right">
              <div className="text-3xl font-bold">{completionScore}%</div>
              <div className="text-orange-100 text-sm">complété</div>
            </div>
          </div>
          <div className="w-full bg-orange-300 rounded-full h-2">
            <div
              className="bg-white rounded-full h-2 transition-all duration-500"
              style={{ width: `${completionScore}%` }}
            />
          </div>
        </div>

        {/* Form */}
        <div className="bg-white rounded-xl shadow-sm">
          {error && (
            <div className="bg-red-50 border-l-4 border-red-500 text-red-700 p-4 m-6 rounded">
              {error}
            </div>
          )}
          {success && (
            <div className="bg-green-50 border-l-4 border-green-500 text-green-700 p-4 m-6 rounded">
              {success}
            </div>
          )}

          <form onSubmit={handleSubmit}>
            {/* Section: Localisation */}
            <div className="p-6 border-b">
              <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
                <span className="w-8 h-8 bg-orange-100 text-orange-600 rounded-full flex items-center justify-center text-sm">1</span>
                Localisation
              </h2>
              <div className="grid md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-gray-700 mb-2 text-sm font-medium">Ville de résidence *</label>
                  <select
                    value={profile.city}
                    onChange={(e) => setProfile({ ...profile, city: e.target.value })}
                    className="w-full px-4 py-3 border border-gray-200 rounded-lg focus:ring-2 focus:ring-orange-500 focus:border-orange-500 bg-gray-50"
                  >
                    {CITIES.map(city => (
                      <option key={city.value} value={city.value}>{city.label}</option>
                    ))}
                  </select>
                </div>
              </div>
            </div>

            {/* Section: Education */}
            <div className="p-6 border-b">
              <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
                <span className="w-8 h-8 bg-orange-100 text-orange-600 rounded-full flex items-center justify-center text-sm">2</span>
                Formation
              </h2>
              <div className="grid md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-gray-700 mb-2 text-sm font-medium">Niveau d&apos;études *</label>
                  <select
                    value={profile.education_level}
                    onChange={(e) => setProfile({ ...profile, education_level: e.target.value })}
                    className="w-full px-4 py-3 border border-gray-200 rounded-lg focus:ring-2 focus:ring-orange-500 focus:border-orange-500 bg-gray-50"
                  >
                    <option value="">Sélectionner...</option>
                    {EDUCATION_LEVELS.map(level => (
                      <option key={level.value} value={level.value}>{level.label}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-gray-700 mb-2 text-sm font-medium">Domaine d&apos;études *</label>
                  <input
                    type="text"
                    value={profile.field_of_study}
                    onChange={(e) => setProfile({ ...profile, field_of_study: e.target.value })}
                    className="w-full px-4 py-3 border border-gray-200 rounded-lg focus:ring-2 focus:ring-orange-500 focus:border-orange-500 bg-gray-50"
                    placeholder="Ex: Informatique, Gestion, Médecine..."
                  />
                </div>
                <div>
                  <label className="block text-gray-700 mb-2 text-sm font-medium">Établissement</label>
                  <input
                    type="text"
                    value={profile.institution}
                    onChange={(e) => setProfile({ ...profile, institution: e.target.value })}
                    className="w-full px-4 py-3 border border-gray-200 rounded-lg focus:ring-2 focus:ring-orange-500 focus:border-orange-500 bg-gray-50"
                    placeholder="Ex: Université FHB, INP-HB, UVCI..."
                  />
                </div>
                <div>
                  <label className="block text-gray-700 mb-2 text-sm font-medium">Année de graduation (prévue)</label>
                  <input
                    type="number"
                    value={profile.graduation_year || ''}
                    onChange={(e) => setProfile({ ...profile, graduation_year: parseInt(e.target.value) || null })}
                    className="w-full px-4 py-3 border border-gray-200 rounded-lg focus:ring-2 focus:ring-orange-500 focus:border-orange-500 bg-gray-50"
                    placeholder="2026"
                    min="2000"
                    max="2035"
                  />
                </div>
              </div>
            </div>

            {/* Section: Compétences */}
            <div className="p-6 border-b">
              <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
                <span className="w-8 h-8 bg-orange-100 text-orange-600 rounded-full flex items-center justify-center text-sm">3</span>
                Compétences
                <span className="text-sm font-normal text-gray-500">({profile.skills.length}/15)</span>
              </h2>

              {/* Skills sélectionnées */}
              <div className="flex flex-wrap gap-2 mb-4 min-h-[40px]">
                {profile.skills.map(skill => (
                  <span
                    key={skill}
                    className="bg-orange-100 text-orange-800 px-3 py-1.5 rounded-full flex items-center gap-2 text-sm"
                  >
                    {skill}
                    <button
                      type="button"
                      onClick={() => removeSkill(skill)}
                      className="text-orange-600 hover:text-orange-800 font-bold"
                    >
                      &times;
                    </button>
                  </span>
                ))}
                {profile.skills.length === 0 && (
                  <span className="text-gray-400 text-sm italic">Aucune compétence ajoutée</span>
                )}
              </div>

              {/* Ajouter skill */}
              <div className="flex gap-2 mb-4">
                <input
                  type="text"
                  value={newSkill}
                  onChange={(e) => setNewSkill(e.target.value)}
                  onKeyPress={(e) => e.key === 'Enter' && (e.preventDefault(), addSkill(newSkill))}
                  className="flex-1 px-4 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-orange-500 bg-gray-50"
                  placeholder="Ajouter une compétence..."
                  maxLength={50}
                />
                <button
                  type="button"
                  onClick={() => addSkill(newSkill)}
                  disabled={!newSkill.trim()}
                  className="px-4 py-2 bg-orange-600 text-white rounded-lg hover:bg-orange-700 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Ajouter
                </button>
              </div>

              {/* Suggestions */}
              <div>
                <p className="text-sm text-gray-500 mb-2">Suggestions :</p>
                <div className="flex flex-wrap gap-2">
                  {SUGGESTED_SKILLS.filter(s => !profile.skills.includes(s)).slice(0, 12).map(skill => (
                    <button
                      key={skill}
                      type="button"
                      onClick={() => addSkill(skill)}
                      className="text-sm bg-gray-100 text-gray-600 px-3 py-1.5 rounded-full hover:bg-orange-100 hover:text-orange-700 transition-colors"
                    >
                      + {skill}
                    </button>
                  ))}
                </div>
              </div>
            </div>

            {/* Section: Intérêts */}
            <div className="p-6 border-b">
              <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
                <span className="w-8 h-8 bg-orange-100 text-orange-600 rounded-full flex items-center justify-center text-sm">4</span>
                Centres d&apos;intérêt
                <span className="text-sm font-normal text-gray-500">({profile.interests.length}/10)</span>
              </h2>
              <p className="text-sm text-gray-500 mb-4">Sélectionne les domaines qui t&apos;intéressent</p>
              <div className="flex flex-wrap gap-2">
                {SUGGESTED_INTERESTS.map(interest => (
                  <button
                    key={interest}
                    type="button"
                    onClick={() => toggleInterest(interest)}
                    className={`px-4 py-2 rounded-full text-sm font-medium transition-all ${
                      profile.interests.includes(interest)
                        ? 'bg-blue-600 text-white'
                        : 'bg-gray-100 text-gray-600 hover:bg-blue-100 hover:text-blue-700'
                    }`}
                  >
                    {profile.interests.includes(interest) ? '✓ ' : ''}{interest}
                  </button>
                ))}
              </div>
            </div>

            {/* Section: Langues */}
            <div className="p-6 border-b">
              <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
                <span className="w-8 h-8 bg-orange-100 text-orange-600 rounded-full flex items-center justify-center text-sm">5</span>
                Langues parlées
              </h2>
              <div className="flex flex-wrap gap-2">
                {LANGUAGES.map(lang => (
                  <button
                    key={lang}
                    type="button"
                    onClick={() => toggleLanguage(lang)}
                    className={`px-4 py-2 rounded-full text-sm font-medium transition-all ${
                      profile.languages.includes(lang)
                        ? 'bg-green-600 text-white'
                        : 'bg-gray-100 text-gray-600 hover:bg-green-100 hover:text-green-700'
                    }`}
                  >
                    {profile.languages.includes(lang) ? '✓ ' : ''}{lang}
                  </button>
                ))}
              </div>
            </div>

            {/* Section: Bio */}
            <div className="p-6 border-b">
              <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
                <span className="w-8 h-8 bg-orange-100 text-orange-600 rounded-full flex items-center justify-center text-sm">6</span>
                À propos de toi
              </h2>
              <textarea
                value={profile.bio}
                onChange={(e) => setProfile({ ...profile, bio: e.target.value })}
                className="w-full px-4 py-3 border border-gray-200 rounded-lg focus:ring-2 focus:ring-orange-500 bg-gray-50 resize-none"
                rows={4}
                maxLength={500}
                placeholder="Décris tes objectifs professionnels, tes aspirations, ce que tu recherches..."
              />
              <p className="text-sm text-gray-400 mt-1">{profile.bio.length}/500 caractères</p>
            </div>

            {/* Section: Liens */}
            <div className="p-6 border-b">
              <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
                <span className="w-8 h-8 bg-orange-100 text-orange-600 rounded-full flex items-center justify-center text-sm">7</span>
                Liens professionnels
                <span className="text-sm font-normal text-gray-400">(optionnel)</span>
              </h2>
              <div className="grid md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-gray-700 mb-2 text-sm font-medium">LinkedIn</label>
                  <input
                    type="url"
                    value={profile.linkedin_url}
                    onChange={(e) => setProfile({ ...profile, linkedin_url: e.target.value })}
                    className="w-full px-4 py-3 border border-gray-200 rounded-lg focus:ring-2 focus:ring-orange-500 bg-gray-50"
                    placeholder="https://linkedin.com/in/ton-profil"
                  />
                </div>
                <div>
                  <label className="block text-gray-700 mb-2 text-sm font-medium">Portfolio / Site web</label>
                  <input
                    type="url"
                    value={profile.portfolio_url}
                    onChange={(e) => setProfile({ ...profile, portfolio_url: e.target.value })}
                    className="w-full px-4 py-3 border border-gray-200 rounded-lg focus:ring-2 focus:ring-orange-500 bg-gray-50"
                    placeholder="https://ton-portfolio.com"
                  />
                </div>
              </div>
            </div>

            {/* Submit */}
            <div className="p-6 flex gap-4">
              <button
                type="submit"
                disabled={saving}
                className="flex-1 py-3 bg-orange-600 text-white rounded-lg hover:bg-orange-700 disabled:opacity-50 font-semibold transition-colors"
              >
                {saving ? (
                  <span className="flex items-center justify-center gap-2">
                    <span className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin"></span>
                    Enregistrement...
                  </span>
                ) : (
                  'Enregistrer mon profil'
                )}
              </button>
              <Link
                href="/dashboard"
                className="px-8 py-3 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 text-center font-medium"
              >
                Annuler
              </Link>
            </div>
          </form>
        </div>
      </main>
    </div>
  )
}
