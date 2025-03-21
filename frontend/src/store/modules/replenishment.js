import { defineStore } from 'pinia'
import axios from 'axios'

export const useReplenishmentStore = defineStore('replenishment', {
  state: () => ({
    adviceList: [],
    loading: false,
    total: 0,
    currentItem: null,
    categories: [],
  }),

  actions: {
    // 获取补货建议列表
    async fetchAdviceList({ page, pageSize, filters }) {
      this.loading = true
      try {
        const response = await axios.get('/api/replenishments/advice', {
          params: {
            page,
            pageSize,
            ...filters
          }
        })
        this.adviceList = response.data.items
        this.total = response.data.total
      } catch (error) {
        console.error('获取补货建议失败:', error)
        throw error
      } finally {
        this.loading = false
      }
    },

    // 获取商品类别列表
    async fetchCategories() {
      try {
        const response = await axios.get('/api/products/categories')
        this.categories = response.data
      } catch (error) {
        console.error('获取商品类别失败:', error)
        throw error
      }
    },

    // 确认补货
    async confirmReplenishment(replenishmentData) {
      try {
        await axios.post('/api/replenishments/confirm', replenishmentData)
      } catch (error) {
        console.error('确认补货失败:', error)
        throw error
      }
    },

    // 获取补货建议详情
    async fetchAdviceDetails(productId) {
      try {
        const response = await axios.get(`/api/replenishments/advice/${productId}/details`)
        this.currentItem = response.data
        return response.data
      } catch (error) {
        console.error('获取补货建议详情失败:', error)
        throw error
      }
    },

    // 导出补货建议
    async exportAdvice(filters) {
      try {
        const response = await axios.get('/api/replenishments/advice/export', {
          params: filters,
          responseType: 'blob'
        })
        
        // 创建下载链接
        const url = window.URL.createObjectURL(new Blob([response.data]))
        const link = document.createElement('a')
        link.href = url
        link.setAttribute('download', `补货建议_${new Date().toISOString().split('T')[0]}.xlsx`)
        document.body.appendChild(link)
        link.click()
        document.body.removeChild(link)
        window.URL.revokeObjectURL(url)
      } catch (error) {
        console.error('导出补货建议失败:', error)
        throw error
      }
    }
  }
})