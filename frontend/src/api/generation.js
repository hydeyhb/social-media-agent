import api from './client'

export const generateSingle = (data) => api.post('/generate/single', data)
export const generateThread = (data) => api.post('/generate/thread', data)
export const generateCaption = (data) => api.post('/generate/caption', data)
export const optimizePost = (postId) => api.post(`/generate/optimize/${postId}`)
export const getOptimalTimes = (platform, narrate = true) =>
  api.post('/generate/optimal-times', null, { params: { platform, narrate } })
export const getContentPatterns = (platform = 'both') =>
  api.post('/generate/patterns', null, { params: { platform } })
