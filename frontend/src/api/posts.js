import api from './client'

export const listPosts = (params) => api.get('/posts', { params })
export const createPost = (data) => api.post('/posts', data)
export const getPost = (id) => api.get(`/posts/${id}`)
export const updatePost = (id, data) => api.put(`/posts/${id}`, data)
export const deletePost = (id) => api.delete(`/posts/${id}`)
export const publishNow = (id) => api.post(`/posts/${id}/publish-now`)
export const schedulePost = (id, scheduled_at) => api.post(`/posts/${id}/schedule`, { scheduled_at })
export const cancelSchedule = (id) => api.post(`/posts/${id}/cancel-schedule`)
export const getThreadSeries = (groupId) => api.get(`/posts/thread/${groupId}`)
