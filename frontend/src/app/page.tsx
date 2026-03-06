'use client'

import Link from 'next/link'

export default function Home() {
  return (
    <main className="min-h-screen bg-gradient-to-br from-orange-50 to-orange-100">
      {/* Header */}
      <header className="bg-white shadow-sm">
        <div className="container mx-auto px-4 py-4 flex justify-between items-center">
          <h1 className="text-2xl font-bold">
            Opportu<span className="text-orange-600">CI</span>
          </h1>
          <nav className="flex gap-4">
            <Link href="/auth/login" className="px-4 py-2 text-gray-600 hover:text-orange-600">
              Connexion
            </Link>
            <Link href="/auth/register" className="px-4 py-2 bg-orange-600 text-white rounded-lg hover:bg-orange-700">
              S&apos;inscrire
            </Link>
          </nav>
        </div>
      </header>

      {/* Hero */}
      <div className="container mx-auto px-4 py-16">
        <div className="text-center">
          <h2 className="text-5xl font-bold text-gray-900 mb-4">
            Opportu<span className="text-orange-600">CI</span>
          </h2>
          <p className="text-xl text-gray-600 mb-8">
            Trouve ta prochaine opportunité avec l&apos;IA
          </p>

          {/* Cards cliquables */}
          <div className="grid md:grid-cols-3 gap-6 mt-12 max-w-4xl mx-auto">
            <Link href="/opportunities?type=scholarship" className="bg-white p-6 rounded-xl shadow-lg hover:shadow-xl hover:scale-105 transition-all cursor-pointer block">
              <div className="text-4xl mb-4">🎓</div>
              <h3 className="text-lg font-semibold mb-2">Bourses</h3>
              <p className="text-gray-600 text-sm">
                Bourses d&apos;études locales et internationales
              </p>
            </Link>

            <Link href="/opportunities?type=job" className="bg-white p-6 rounded-xl shadow-lg hover:shadow-xl hover:scale-105 transition-all cursor-pointer block">
              <div className="text-4xl mb-4">💼</div>
              <h3 className="text-lg font-semibold mb-2">Stages & Emplois</h3>
              <p className="text-gray-600 text-sm">
                Opportunités professionnelles en Côte d&apos;Ivoire
              </p>
            </Link>

            <Link href="/dashboard" className="bg-white p-6 rounded-xl shadow-lg hover:shadow-xl hover:scale-105 transition-all cursor-pointer block">
              <div className="text-4xl mb-4">🤖</div>
              <h3 className="text-lg font-semibold mb-2">Matching IA</h3>
              <p className="text-gray-600 text-sm">
                Recommandations personnalisées par Gemini AI
              </p>
            </Link>
          </div>

          {/* CTA */}
          <div className="mt-12">
            <Link href="/auth/register" className="inline-block px-8 py-4 bg-orange-600 text-white text-lg font-semibold rounded-lg hover:bg-orange-700 transition-colors">
              Commencer gratuitement
            </Link>
          </div>

          {/* Stats */}
          <div className="mt-16 grid grid-cols-3 gap-8 max-w-2xl mx-auto">
            <div>
              <div className="text-3xl font-bold text-orange-600">500+</div>
              <div className="text-gray-600">Opportunités</div>
            </div>
            <div>
              <div className="text-3xl font-bold text-orange-600">1000+</div>
              <div className="text-gray-600">Utilisateurs</div>
            </div>
            <div>
              <div className="text-3xl font-bold text-orange-600">95%</div>
              <div className="text-gray-600">Satisfaction</div>
            </div>
          </div>
        </div>
      </div>
    </main>
  )
}
