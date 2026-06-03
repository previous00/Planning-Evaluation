import api from '../utils/request'

export const getDashboard = () => api.get('/admin/dashboard')
export const getUsers = (params) => api.get('/admin/users', { params })
export const updateUser = (id, data) => api.put(`/admin/users/${id}`, data)
export const deleteUser = (id) => api.delete(`/admin/users/${id}`)
export const createCategory = (data) => api.post('/admin/categories', data)
export const updateCategory = (id, data) => api.put(`/admin/categories/${id}`, data)
export const deleteCategory = (id) => api.delete(`/admin/categories/${id}`)
export const getLearningStats = () => api.get('/admin/learning-stats')
