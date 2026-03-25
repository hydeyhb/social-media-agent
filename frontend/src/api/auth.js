import api from './client'

export const getAuthStatus = () => api.get('/auth/status')
export const revokeToken = (platform) => api.delete(`/auth/revoke/${platform}`)
export const getFacebookLoginUrl = () => '/api/auth/facebook/login'
export const getThreadsLoginUrl = () => '/api/auth/threads/login'
