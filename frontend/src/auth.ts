import { computed, ref } from 'vue'

export interface AuthUser {
  id: number
  username: string
  role: string
}

function parseStoredUser(): AuthUser | null {
  try {
    return JSON.parse(localStorage.getItem('user') || 'null')
  } catch {
    return null
  }
}

const token = ref<string>(localStorage.getItem('token') || '')
const user = ref<AuthUser | null>(parseStoredUser())

export function useAuth() {
  const isLoggedIn = computed(() => Boolean(token.value))

  const setSession = (newToken: string, newUser: AuthUser) => {
    token.value = newToken
    user.value = newUser
    localStorage.setItem('token', newToken)
    localStorage.setItem('user', JSON.stringify(newUser))
  }

  const clearSession = () => {
    token.value = ''
    user.value = null
    localStorage.removeItem('token')
    localStorage.removeItem('user')
  }

  return { token, user, isLoggedIn, setSession, clearSession }
}
