import { defineStore } from 'pinia'
import { login as apiLogin, register as apiRegister, logout as apiLogout, me } from '../api/auth'

export const useUserStore = defineStore('user', {
  state: () => ({
    token: localStorage.getItem('qa_token') || '',
    userInfo: JSON.parse(localStorage.getItem('qa_user') || 'null')
  }),

  getters: {
    isLoggedIn: (state) => !!state.token
  },

  actions: {
    async login(username, password) {
      const data = await apiLogin(username, password)
      this.token = data.access_token
      localStorage.setItem('qa_token', data.access_token)
      await this.fetchUser()
    },

    async register(username, password) {
      return apiRegister(username, password)
    },

    async fetchUser() {
      const info = await me()
      this.userInfo = info
      localStorage.setItem('qa_user', JSON.stringify(info))
    },

    async logout() {
      try {
        await apiLogout()
      } catch (e) {
        // 忽略退出接口异常，本地照常清理
      }
      this.token = ''
      this.userInfo = null
      localStorage.removeItem('qa_token')
      localStorage.removeItem('qa_user')
    }
  }
})
