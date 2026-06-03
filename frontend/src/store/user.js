import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { login as loginApi, register as registerApi, getProfile } from '../api/auth'

export const useUserStore = defineStore('user', () => {
  const user = ref(JSON.parse(localStorage.getItem('user') || 'null'))
  const token = ref(localStorage.getItem('access_token') || '')

  const isLoggedIn = computed(() => !!token.value)
  const isAdmin = computed(() => user.value?.role === 'admin')

  async function login(data) {
    const res = await loginApi(data)
    token.value = res.access_token
    user.value = res.user
    localStorage.setItem('access_token', res.access_token)
    localStorage.setItem('user', JSON.stringify(res.user))
    return res
  }

  async function register(data) {
    const res = await registerApi(data)
    token.value = res.access_token
    user.value = res.user
    localStorage.setItem('access_token', res.access_token)
    localStorage.setItem('user', JSON.stringify(res.user))
    return res
  }

  async function fetchProfile() {
    const res = await getProfile()
    user.value = res.user
    localStorage.setItem('user', JSON.stringify(res.user))
  }

  function logout() {
    token.value = ''
    user.value = null
    localStorage.removeItem('access_token')
    localStorage.removeItem('user')
  }

  return { user, token, isLoggedIn, isAdmin, login, register, fetchProfile, logout }
})
