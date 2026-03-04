import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export interface GitHubUser {
  login: string
  name: string
  avatar_url: string
  email?: string
}

export const useAuthStore = defineStore('auth', () => {
  const token = ref<string | null>(null)
  const user = ref<GitHubUser | null>(null)
  const loading = ref(false)

  const isAuthenticated = computed(() => !!token.value && !!user.value)

  // Initialize from localStorage
  function init() {
    const savedToken = localStorage.getItem('github_token')
    const savedUser = localStorage.getItem('github_user')

    if (savedToken && savedUser) {
      token.value = savedToken
      try {
        user.value = JSON.parse(savedUser)
      } catch (e) {
        console.error('Failed to parse saved user:', e)
        logout()
      }
    }
  }

  // Start OAuth flow
  function login() {
    // GitHub OAuth App credentials (需要在 GitHub 创建 OAuth App)
    const clientId = import.meta.env.VITE_GITHUB_CLIENT_ID || 'YOUR_CLIENT_ID'
    const redirectUri = `${window.location.origin}${import.meta.env.BASE_URL}auth/callback`
    const scope = 'gist'

    const authUrl = `https://github.com/login/oauth/authorize?client_id=${clientId}&redirect_uri=${encodeURIComponent(redirectUri)}&scope=${scope}`
    window.location.href = authUrl
  }

  // Handle OAuth callback
  async function handleCallback(code: string) {
    loading.value = true
    try {
      // Note: 实际生产环境需要后端服务来交换 code 获取 token
      // 这里简化处理，假设使用 GitHub OAuth App 的 device flow 或其他方式
      // 由于是静态部署，可以考虑使用 GitHub Personal Access Token 作为替代方案

      // 临时方案：让用户手动输入 Personal Access Token
      const pat = prompt('请输入 GitHub Personal Access Token (需要 gist 权限):')
      if (!pat) {
        throw new Error('未提供 token')
      }

      // 验证 token 并获取用户信息
      const response = await fetch('https://api.github.com/user', {
        headers: {
          'Authorization': `Bearer ${pat}`,
          'Accept': 'application/vnd.github.v3+json'
        }
      })

      if (!response.ok) {
        throw new Error('Token 验证失败')
      }

      const userData = await response.json()

      // 保存认证信息
      token.value = pat
      user.value = {
        login: userData.login,
        name: userData.name || userData.login,
        avatar_url: userData.avatar_url,
        email: userData.email
      }

      // 持久化到 localStorage
      localStorage.setItem('github_token', pat)
      localStorage.setItem('github_user', JSON.stringify(user.value))

    } catch (error) {
      console.error('Authentication failed:', error)
      throw error
    } finally {
      loading.value = false
    }
  }

  // Logout
  function logout() {
    token.value = null
    user.value = null
    localStorage.removeItem('github_token')
    localStorage.removeItem('github_user')
  }

  // 简化版登录：直接使用 Personal Access Token
  async function loginWithToken(pat: string) {
    loading.value = true
    try {
      const response = await fetch('https://api.github.com/user', {
        headers: {
          'Authorization': `Bearer ${pat}`,
          'Accept': 'application/vnd.github.v3+json'
        }
      })

      if (!response.ok) {
        throw new Error('Token 验证失败')
      }

      const userData = await response.json()

      token.value = pat
      user.value = {
        login: userData.login,
        name: userData.name || userData.login,
        avatar_url: userData.avatar_url,
        email: userData.email
      }

      localStorage.setItem('github_token', pat)
      localStorage.setItem('github_user', JSON.stringify(user.value))

      return true
    } catch (error) {
      console.error('Login failed:', error)
      return false
    } finally {
      loading.value = false
    }
  }

  return {
    token,
    user,
    loading,
    isAuthenticated,
    init,
    login,
    loginWithToken,
    handleCallback,
    logout
  }
})
