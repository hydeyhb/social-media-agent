import api from './client'

export const getOverview = (platform) => api.get('/analytics/overview', { params: { platform } })
export const getPostsAnalytics = (params) => api.get('/analytics/posts', { params })
export const getPostDetail = (id) => api.get(`/analytics/posts/${id}`)
export const getTrends = (days, platform) => api.get('/analytics/trends', { params: { days, platform } })
export const getTopPerformers = (limit, platform) => api.get('/analytics/top-performers', { params: { limit, platform } })
export const getPostingTimes = (platform) => api.get('/analytics/posting-times', { params: { platform } })
export const syncAnalytics = () => api.post('/analytics/sync')
