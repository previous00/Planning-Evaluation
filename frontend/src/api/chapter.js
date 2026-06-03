import api from '../utils/request'

export const getChapters = (courseId) => api.get(`/chapters/course/${courseId}`)
export const getChapter = (chapterId) => api.get(`/chapters/${chapterId}`)
export const createChapter = (data) => api.post('/chapters/', data)
export const updateChapter = (chapterId, data) => api.put(`/chapters/${chapterId}`, data)
export const deleteChapter = (chapterId) => api.delete(`/chapters/${chapterId}`)
