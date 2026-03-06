import Link from 'next/link'

export default function Footer() {
  return (
    <footer className="bg-gray-900 text-gray-300">
      <div className="max-w-7xl mx-auto px-4 py-12">
        <div className="grid md:grid-cols-4 gap-8">
          {/* Brand */}
          <div>
            <Link href="/" className="text-2xl font-bold text-white">
              Opportu<span className="text-orange-500">CI</span>
            </Link>
            <p className="mt-3 text-sm text-gray-400">
              La plateforme IA qui connecte les jeunes ivoiriens aux meilleures opportunités.
            </p>
          </div>

          {/* Links */}
          <div>
            <h3 className="font-semibold text-white mb-3">Opportunités</h3>
            <ul className="space-y-2 text-sm">
              <li><Link href="/opportunities?type=scholarship" className="hover:text-orange-500">Bourses</Link></li>
              <li><Link href="/opportunities?type=internship" className="hover:text-orange-500">Stages</Link></li>
              <li><Link href="/opportunities?type=job" className="hover:text-orange-500">Emplois</Link></li>
              <li><Link href="/opportunities?type=training" className="hover:text-orange-500">Formations</Link></li>
            </ul>
          </div>

          <div>
            <h3 className="font-semibold text-white mb-3">Plateforme</h3>
            <ul className="space-y-2 text-sm">
              <li><Link href="/auth/register" className="hover:text-orange-500">Créer un compte</Link></li>
              <li><Link href="/auth/login" className="hover:text-orange-500">Connexion</Link></li>
              <li><Link href="/dashboard" className="hover:text-orange-500">Dashboard</Link></li>
            </ul>
          </div>

          <div>
            <h3 className="font-semibold text-white mb-3">Contact</h3>
            <ul className="space-y-2 text-sm">
              <li>Abidjan, Côte d&apos;Ivoire</li>
              <li>contact@opportuci.ci</li>
            </ul>
          </div>
        </div>

        <div className="border-t border-gray-800 mt-8 pt-8 text-center text-sm text-gray-500">
          <p>&copy; {new Date().getFullYear()} OpportuCI. Tous droits réservés.</p>
        </div>
      </div>
    </footer>
  )
}
