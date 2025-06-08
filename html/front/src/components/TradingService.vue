<template>
  <div class="card">
    <div class="card-header">交易服务</div>
    <div class="card-body">
      <button 
        class="btn btn-success"
        @click="handleExecuteTrade"
        :disabled="loading"
      >
        {{ loading ? '执行中...' : '执行交易操作' }}
      </button>
    </div>
  </div>
</template>

<script>
export default {
  name: 'TradingService',
  props: {
    loading: {
      type: Boolean,
      default: false
    }
  },
  emits: ['execute-trade'],
  setup(props, { emit }) {
    const handleExecuteTrade = () => {
      emit('execute-trade')
    }

    return {
      handleExecuteTrade
    }
  }
}
</script>

<style scoped>
/* 交易服务组件特定样式 */
</style> 