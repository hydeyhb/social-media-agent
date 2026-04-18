import api from './client'

export const listAssets = () => api.get('/assets')
export const getAsset = (id) => api.get(`/assets/${id}`)
export const deleteAsset = (id) => api.delete(`/assets/${id}`)

export const uploadAsset = (file, platform = 'both', personaId = null, provider = 'openai') => {
  const form = new FormData()
  form.append('file', file)
  if (personaId) form.append('persona_id', personaId)
  return api.post(`/assets/upload?platform=${platform}&provider=${provider}`, form, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
}

export const uploadAssets = (files, platform = 'both', personaId = null, provider = 'openai') => {
  const form = new FormData()
  files.forEach(f => form.append('files', f))
  if (personaId) form.append('persona_id', personaId)
  return api.post(`/assets/upload-multi?platform=${platform}&provider=${provider}`, form, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
}
