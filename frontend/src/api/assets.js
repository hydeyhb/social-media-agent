import api from './client'
import axios from 'axios'

export const listAssets = () => api.get('/assets')
export const getAsset = (id) => api.get(`/assets/${id}`)
export const deleteAsset = (id) => api.delete(`/assets/${id}`)

export const uploadAsset = (file, platform = 'both', personaId = null) => {
  const form = new FormData()
  form.append('file', file)
  if (personaId) form.append('persona_id', personaId)
  return axios.post(`/api/assets/upload?platform=${platform}`, form, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
}
