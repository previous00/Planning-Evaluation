import api from '../utils/request'

export const enrollCourse = (data) => api.post('/learning/enroll', data)
export const checkEnrollment = (courseId) => api.get(`/learning/check-enroll/${courseId}`)
export const getAvailableCoupons = (courseId) => api.get(`/learning/available-coupons/${courseId}`)
export const recordLearning = (data) => api.post('/learning/record', data)
export const getAllProgress = (params) => api.get('/learning/progress', { params })
export const getCourseProgress = (courseId) => api.get(`/learning/progress/${courseId}`)
export const getHistory = (params) => api.get('/learning/history', { params })
export const getRecent = (params) => api.get('/learning/recent', { params })
export const getStats = () => api.get('/learning/stats')
