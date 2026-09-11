import request from './request'

export const login = (username, password) =>
  request.post('/auth/login', { username, password })

export const register = (username, password) =>
  request.post('/auth/register', { username, password })

export const logout = () =>
  request.post('/auth/logout')

export const me = () =>
  request.get('/auth/me')

export const changePassword = (old_password, new_password) =>
  request.post('/auth/change-password', { old_password, new_password })
