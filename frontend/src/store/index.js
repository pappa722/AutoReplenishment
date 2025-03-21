import { createStore } from 'vuex'
import axios from 'axios'

// 设置API基础URL
axios.defaults.baseURL = 'http://localhost:8000/api'

export default createStore({
  state: {
    user: null,
    token: localStorage.getItem('token') || null,
    products: [],
    sales: [],
    replenishments: [],
    forecasts: [],
    loading: false,
    error: null
  },
  mutations: {
    SET_USER(state, user) {
      state.user = user
    },
    SET_TOKEN(state, token) {
      state.token = token
      localStorage.setItem('token', token)
      axios.defaults.headers.common['Authorization'] = `Bearer ${token}`
    },
    CLEAR_AUTH(state) {
      state.user = null
      state.token = null
      localStorage.removeItem('token')
      delete axios.defaults.headers.common['Authorization']
    },
    SET_PRODUCTS(state, products) {
      state.products = products
    },
    SET_SALES(state, sales) {
      state.sales = sales
    },
    SET_REPLENISHMENTS(state, replenishments) {
      state.replenishments = replenishments
    },
    SET_FORECASTS(state, forecasts) {
      state.forecasts = forecasts
    },
    SET_LOADING(state, loading) {
      state.loading = loading
    },
    SET_ERROR(state, error) {
      state.error = error
    }
  },
  actions: {
    // 认证相关
    async login({ commit }, credentials) {
      commit('SET_LOADING', true)
      try {
        const response = await axios.post('/auth/login', credentials)
        commit('SET_TOKEN', response.data.access_token)
        commit('SET_USER', response.data.user)
        return response.data
      } catch (error) {
        commit('SET_ERROR', error.response?.data?.detail || 'Login failed')
        throw error
      } finally {
        commit('SET_LOADING', false)
      }
    },
    
    async logout({ commit }) {
      commit('CLEAR_AUTH')
    },
    
    // 产品相关
    async fetchProducts({ commit }) {
      commit('SET_LOADING', true)
      try {
        const response = await axios.get('/products/')
        commit('SET_PRODUCTS', response.data)
        return response.data
      } catch (error) {
        commit('SET_ERROR', error.response?.data?.detail || 'Failed to fetch products')
        throw error
      } finally {
        commit('SET_LOADING', false)
      }
    },
    
    // 销售相关
    async fetchSales({ commit }, params) {
      commit('SET_LOADING', true)
      try {
        const response = await axios.get('/sales/', { params })
        commit('SET_SALES', response.data)
        return response.data
      } catch (error) {
        commit('SET_ERROR', error.response?.data?.detail || 'Failed to fetch sales')
        throw error
      } finally {
        commit('SET_LOADING', false)
      }
    },
    
    // 补货相关
    async fetchReplenishments({ commit }, params) {
      commit('SET_LOADING', true)
      try {
        const response = await axios.get('/replenishments/', { params })
        commit('SET_REPLENISHMENTS', response.data)
        return response.data
      } catch (error) {
        commit('SET_ERROR', error.response?.data?.detail || 'Failed to fetch replenishments')
        throw error
      } finally {
        commit('SET_LOADING', false)
      }
    },
    
    // 预测相关
    async generateForecast({ commit }, params) {
      commit('SET_LOADING', true)
      try {
        const response = await axios.post('/forecasts/generate', params)
        commit('SET_FORECASTS', response.data)
        return response.data
      } catch (error) {
        commit('SET_ERROR', error.response?.data?.detail || 'Failed to generate forecast')
        throw error
      } finally {
        commit('SET_LOADING', false)
      }
    },
    
    // 数据处理相关
    async processData({ commit }, params) {
      commit('SET_LOADING', true)
      try {
        const response = await axios.post('/data-processing/process', params)
        return response.data
      } catch (error) {
        commit('SET_ERROR', error.response?.data?.detail || 'Failed to process data')
        throw error
      } finally {
        commit('SET_LOADING', false)
      }
    }
  },
  getters: {
    isAuthenticated: state => !!state.token,
    currentUser: state => state.user,
    getProducts: state => state.products,
    getSales: state => state.sales,
    getReplenishments: state => state.replenishments,
    getForecasts: state => state.forecasts,
    isLoading: state => state.loading,
    getError: state => state.error
  }
})