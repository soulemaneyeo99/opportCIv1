'use client'

import { useState, useEffect, useCallback } from 'react'
import { useRouter } from 'next/navigation'
import api from '@/lib/api'

interface User {
  id: number
  email: string
  first_name: string
  last_name: string
  user_type: string
  profile: {
    city: string
    education_level: string
    field_of_study: string
    skills: string[]
    interests: string[]
    languages: string[]
  } | null
}

interface AuthState {
  user: User | null
  isLoading: boolean
  isAuthenticated: boolean
  error: string | null
}

export function useAuth() {
  const router = useRouter()
  const [state, setState] = useState<AuthState>({
    user: null,
    isLoading: true,
    isAuthenticated: false,
    error: null,
  })

  const checkAuth = useCallback(async () => {
    const token = localStorage.getItem('access_token')

    if (!token) {
      setState({
        user: null,
        isLoading: false,
        isAuthenticated: false,
        error: null,
      })
      return
    }

    try {
      const user = await api.getMe() as User
      setState({
        user,
        isLoading: false,
        isAuthenticated: true,
        error: null,
      })
    } catch (error) {
      setState({
        user: null,
        isLoading: false,
        isAuthenticated: false,
        error: 'Session expired',
      })
    }
  }, [])

  useEffect(() => {
    checkAuth()
  }, [checkAuth])

  const login = async (email: string, password: string) => {
    setState(prev => ({ ...prev, isLoading: true, error: null }))

    try {
      const user = await api.login(email, password)
      setState({
        user,
        isLoading: false,
        isAuthenticated: true,
        error: null,
      })
      return { success: true }
    } catch (error: any) {
      const message = error.message || 'Erreur de connexion'
      setState(prev => ({ ...prev, isLoading: false, error: message }))
      return { success: false, error: message }
    }
  }

  const register = async (userData: {
    email: string
    password: string
    confirm_password: string
    first_name: string
    last_name: string
  }) => {
    setState(prev => ({ ...prev, isLoading: true, error: null }))

    try {
      await api.register({ ...userData, terms: true })
      setState(prev => ({ ...prev, isLoading: false }))
      return { success: true }
    } catch (error: any) {
      const message = error.data?.errors?.email?.[0] ||
                     error.data?.errors?.password?.[0] ||
                     error.message ||
                     'Erreur lors de l\'inscription'
      setState(prev => ({ ...prev, isLoading: false, error: message }))
      return { success: false, error: message }
    }
  }

  const logout = () => {
    api.logout()
    setState({
      user: null,
      isLoading: false,
      isAuthenticated: false,
      error: null,
    })
  }

  const updateProfile = async (profileData: any) => {
    try {
      const updated = await api.updateProfile(profileData)
      setState(prev => ({
        ...prev,
        user: prev.user ? { ...prev.user, profile: updated as any } : null,
      }))
      return { success: true }
    } catch (error: any) {
      return { success: false, error: error.message }
    }
  }

  const requireAuth = useCallback((redirectTo = '/auth/login') => {
    if (!state.isLoading && !state.isAuthenticated) {
      router.push(redirectTo)
    }
  }, [state.isLoading, state.isAuthenticated, router])

  const isProfileComplete = useCallback(() => {
    const profile = state.user?.profile
    return !!(
      profile &&
      profile.skills?.length > 0 &&
      profile.interests?.length > 0 &&
      profile.education_level
    )
  }, [state.user])

  return {
    ...state,
    login,
    register,
    logout,
    updateProfile,
    requireAuth,
    isProfileComplete,
    refetch: checkAuth,
  }
}

export default useAuth
