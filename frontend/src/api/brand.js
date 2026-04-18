import api from './client'

export const getActiveBrand = () => api.get('/brand')
export const getAllBrands = () => api.get('/brand/all')
export const createBrand = (data) => api.post('/brand', data)
export const updateBrand = (id, data) => api.put(`/brand/${id}`, data)
export const activateBrand = (id) => api.post(`/brand/${id}/activate`)
export const deleteBrand = (id) => api.delete(`/brand/${id}`)
export const generatePersonaFromBrief = (brief, provider = 'openai') => api.post('/brand/generate', { brief, provider })
