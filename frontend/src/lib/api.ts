/**
 * OpportuCI - API Client
 * =======================
 * Centralized API client with authentication handling
 */

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

interface FetchOptions extends RequestInit {
  auth?: boolean
}

class ApiClient {
  private baseUrl: string

  constructor(baseUrl: string) {
    this.baseUrl = baseUrl
  }

  private getToken(): string | null {
    if (typeof window === 'undefined') return null
    return localStorage.getItem('access_token')
  }

  private setTokens(access: string, refresh: string) {
    localStorage.setItem('access_token', access)
    localStorage.setItem('refresh_token', refresh)
  }

  private clearTokens() {
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
  }

  async fetch<T>(endpoint: string, options: FetchOptions = {}): Promise<T> {
    const { auth = true, headers = {}, ...rest } = options

    const requestHeaders: HeadersInit = {
      'Content-Type': 'application/json',
      ...headers,
    }

    if (auth) {
      const token = this.getToken()
      if (token) {
        (requestHeaders as Record<string, string>)['Authorization'] = `Bearer ${token}`
      }
    }

    const response = await fetch(`${this.baseUrl}${endpoint}`, {
      headers: requestHeaders,
      ...rest,
    })

    // Handle 401 - try to refresh token
    if (response.status === 401 && auth) {
      const refreshed = await this.refreshToken()
      if (refreshed) {
        // Retry request with new token
        const newToken = this.getToken()
        if (newToken) {
          (requestHeaders as Record<string, string>)['Authorization'] = `Bearer ${newToken}`
        }
        const retryResponse = await fetch(`${this.baseUrl}${endpoint}`, {
          headers: requestHeaders,
          ...rest,
        })
        if (!retryResponse.ok) {
          throw new ApiError(retryResponse.status, await retryResponse.text())
        }
        return retryResponse.json()
      } else {
        // Refresh failed, logout
        this.clearTokens()
        if (typeof window !== 'undefined') {
          window.location.href = '/auth/login'
        }
        throw new ApiError(401, 'Session expired')
      }
    }

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}))
      throw new ApiError(response.status, errorData.detail || response.statusText, errorData)
    }

    return response.json()
  }

  private async refreshToken(): Promise<boolean> {
    const refreshToken = localStorage.getItem('refresh_token')
    if (!refreshToken) return false

    try {
      const response = await fetch(`${this.baseUrl}/api/accounts/auth/refresh/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ refresh: refreshToken }),
      })

      if (!response.ok) return false

      const data = await response.json()
      this.setTokens(data.access, refreshToken)
      return true
    } catch {
      return false
    }
  }

  // Auth methods
  async login(email: string, password: string) {
    const data = await this.fetch<{ access: string; refresh: string; user: any }>(
      '/api/accounts/auth/login/',
      { method: 'POST', body: JSON.stringify({ email, password }), auth: false }
    )
    this.setTokens(data.access, data.refresh)
    return data.user
  }

  async register(userData: {
    email: string
    password: string
    confirm_password: string
    first_name: string
    last_name: string
    terms: boolean
  }) {
    return this.fetch('/api/accounts/auth/register/', {
      method: 'POST',
      body: JSON.stringify(userData),
      auth: false,
    })
  }

  logout() {
    this.clearTokens()
    if (typeof window !== 'undefined') {
      window.location.href = '/'
    }
  }

  // User methods
  async getMe() {
    return this.fetch('/api/accounts/users/me/')
  }

  async updateProfile(profileData: any) {
    return this.fetch('/api/accounts/users/update_profile/', {
      method: 'PATCH',
      body: JSON.stringify(profileData),
    })
  }

  // Opportunities methods
  async getOpportunities(params?: { type?: string; search?: string }) {
    const searchParams = new URLSearchParams()
    if (params?.type && params.type !== 'all') {
      searchParams.set('opportunity_type', params.type)
    }
    if (params?.search) {
      searchParams.set('search', params.search)
    }
    const query = searchParams.toString()
    return this.fetch(`/api/opportunities/${query ? `?${query}` : ''}`, { auth: false })
  }

  async getOpportunity(slug: string) {
    return this.fetch(`/api/opportunities/${slug}/`, { auth: false })
  }

  async getRecommendations(limit = 10) {
    return this.fetch(`/api/opportunities/recommendations/?limit=${limit}`)
  }

  // Health check
  async healthCheck() {
    return this.fetch('/api/health/', { auth: false })
  }
}

export class ApiError extends Error {
  status: number
  data: any

  constructor(status: number, message: string, data?: any) {
    super(message)
    this.status = status
    this.data = data
    this.name = 'ApiError'
  }
}

export const api = new ApiClient(API_URL)
export default api
