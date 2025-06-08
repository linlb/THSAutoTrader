<template>
  <div class="container mt-5">
    <h1 class="text-center">自动化控制面板</h1>
    <div class="row mt-4">
      <div class="col-md-6">
        <WindowControl 
          :loading="loading" 
          :result="result"
          @api-call="callApi"
        />
      </div>
      <div class="col-md-6">
        <TradingService 
          :loading="loading" 
          @execute-trade="executeTrade"
        />
      </div>
      <div class="col-md-6">
        <StockPool 
          :loading="loading" 
          @stock-pool-updated="updateStockPool"
        />
      </div>
    </div>
  </div>
</template>

<script>
import { ref } from 'vue'
import axios from 'axios'
import WindowControl from './components/WindowControl.vue'
import TradingService from './components/TradingService.vue'
import StockPool from './components/StockPool.vue'

export default {
  name: 'App',
  components: {
    WindowControl,
    TradingService,
    StockPool
  },
  setup() {
    const result = ref('')
    const loading = ref(false)

    const callApi = async (url) => {
      loading.value = true
      try {
        const response = await axios.get(url)
        result.value = JSON.stringify(response.data, null, 2)
      } catch (error) {
        console.error('请求失败:', error)
        result.value = '请求失败: ' + error.message
      } finally {
        loading.value = false
      }
    }

    const executeTrade = async () => {
      loading.value = true
      try {
        const response = await axios.post('http://localhost:5000/trade')
        result.value = JSON.stringify(response.data, null, 2)
      } catch (error) {
        console.error('交易操作失败:', error)
        result.value = '交易操作失败: ' + error.message
      } finally {
        loading.value = false
      }
    }

    return {
      result,
      loading,
      callApi,
      executeTrade
    }
  }
}
</script>

<style scoped>
/* 可以在这里添加组件特定的样式 */
</style> 