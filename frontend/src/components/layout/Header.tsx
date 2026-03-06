'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { useState, useEffect } from 'react'

interface HeaderProps {
  transparent?: boolean
}

export default function Header({ transparent = false }: HeaderProps) {
  const pathname = usePathname()
  const [isLoggedIn, setIsLoggedIn] = useState(false)
  const [isMenuOpen, setIsMenuOpen] = useState(false)

  useEffect(() => {
    setIsLoggedIn(!!localStorage.getItem('access_token'))
  }, [])

  const handleLogout = () => {
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    window.location.href = '/'
  }

  const navLinks = [
    { href: '/opportunities', label: 'Opportunités' },
    ...(isLoggedIn ? [
      { href: '/dashboard', label: 'Dashboard' },
      { href: '/profile', label: 'Mon Profil' },
    ] : []),
  ]

  const isActive = (href: string) => pathname === href

  return (
    <header className={`sticky top-0 z-50 ${transparent ? 'bg-transparent' : 'bg-white shadow-sm'}`}>
      <div className="max-w-7xl mx-auto px-4">
        <div className="flex justify-between items-center h-16">
          {/* Logo */}
          <Link href="/" className="text-2xl font-bold">
            Opportu<span className="text-orange-600">CI</span>
          </Link>

          {/* Desktop Navigation */}
          <nav className="hidden md:flex items-center gap-6">
            {navLinks.map(link => (
              <Link
                key={link.href}
                href={link.href}
                className={`text-sm font-medium transition-colors ${
                  isActive(link.href)
                    ? 'text-orange-600'
                    : 'text-gray-600 hover:text-orange-600'
                }`}
              >
                {link.label}
              </Link>
            ))}

            {isLoggedIn ? (
              <button
                onClick={handleLogout}
                className="text-sm font-medium text-red-600 hover:text-red-700"
              >
                Déconnexion
              </button>
            ) : (
              <div className="flex items-center gap-3">
                <Link
                  href="/auth/login"
                  className="text-sm font-medium text-gray-600 hover:text-orange-600"
                >
                  Connexion
                </Link>
                <Link
                  href="/auth/register"
                  className="px-4 py-2 bg-orange-600 text-white text-sm font-medium rounded-lg hover:bg-orange-700 transition-colors"
                >
                  S&apos;inscrire
                </Link>
              </div>
            )}
          </nav>

          {/* Mobile menu button */}
          <button
            onClick={() => setIsMenuOpen(!isMenuOpen)}
            className="md:hidden p-2 text-gray-600"
            aria-label="Toggle menu"
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              {isMenuOpen ? (
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              ) : (
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
              )}
            </svg>
          </button>
        </div>

        {/* Mobile Navigation */}
        {isMenuOpen && (
          <nav className="md:hidden py-4 border-t">
            <div className="flex flex-col gap-3">
              {navLinks.map(link => (
                <Link
                  key={link.href}
                  href={link.href}
                  onClick={() => setIsMenuOpen(false)}
                  className={`py-2 text-sm font-medium ${
                    isActive(link.href) ? 'text-orange-600' : 'text-gray-600'
                  }`}
                >
                  {link.label}
                </Link>
              ))}
              {isLoggedIn ? (
                <button
                  onClick={handleLogout}
                  className="py-2 text-sm font-medium text-red-600 text-left"
                >
                  Déconnexion
                </button>
              ) : (
                <>
                  <Link href="/auth/login" className="py-2 text-sm font-medium text-gray-600">
                    Connexion
                  </Link>
                  <Link
                    href="/auth/register"
                    className="py-2 px-4 bg-orange-600 text-white text-sm font-medium rounded-lg text-center"
                  >
                    S&apos;inscrire
                  </Link>
                </>
              )}
            </div>
          </nav>
        )}
      </div>
    </header>
  )
}
