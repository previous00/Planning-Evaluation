import api from '../utils/request'

export const getMallItems = (params) => api.get('/mall/items', { params })
export const getMallItem = (itemId) => api.get(`/mall/items/${itemId}`)
export const redeemItem = (data) => api.post('/mall/redeem', data)
export const getMyOrders = (params) => api.get('/mall/orders', { params })
export const getMyPoints = () => api.get('/growth/points')
export const getPointsTransactions = (params) => api.get('/growth/points/transactions', { params })
export const getPointsRules = () => api.get('/growth/points/rules')
