import api from '../utils/request'

export const getRecommendations = (params) => api.get('/recommend/', { params })
export const getPopularRecommendations = (params) => api.get('/recommend/popular', { params })
export const getUserProfile = () => api.get('/recommend/profile')
export const refreshProfile = () => api.post('/recommend/profile/refresh')
export const trackClick = (data) => api.post('/recommend/click', data)
export const getRecommendStats = () => api.get('/recommend/stats')
