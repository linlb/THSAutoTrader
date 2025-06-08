<template>
  <Card 
    title="交易策略"
    :default-collapsed="defaultCollapsed"
  >
    <!-- 交易策略配置区域 -->
      <div class="strategy-form">
        <div class="row">
          <div class="col-md-6">
            <div class="mb-3">
              <label for="strategyType" class="form-label">策略类型</label>
              <select class="form-select" id="strategyType" v-model="strategyType">
                <option value="">请选择策略类型</option>
                <option value="trend">趋势跟踪</option>
                <option value="reversal">反转策略</option>
                <option value="momentum">动量策略</option>
              </select>
            </div>
          </div>
          <div class="col-md-6">
            <div class="mb-3">
              <label for="riskLevel" class="form-label">风险等级</label>
              <select class="form-select" id="riskLevel" v-model="riskLevel">
                <option value="">请选择风险等级</option>
                <option value="low">低风险</option>
                <option value="medium">中等风险</option>
                <option value="high">高风险</option>
              </select>
            </div>
          </div>
        </div>
        
        <div class="row">
          <div class="col-md-6">
            <div class="mb-3">
              <label for="maxPosition" class="form-label">最大仓位 (%)</label>
              <input 
                type="number" 
                class="form-control" 
                id="maxPosition"
                v-model="maxPosition"
                min="0"
                max="100"
                placeholder="输入最大仓位比例"
              >
            </div>
          </div>
          <div class="col-md-6">
            <div class="mb-3">
              <label for="stopLoss" class="form-label">止损比例 (%)</label>
              <input 
                type="number" 
                class="form-control" 
                id="stopLoss"
                v-model="stopLoss"
                min="0"
                max="50"
                placeholder="输入止损比例"
              >
            </div>
          </div>
        </div>
        
        <div class="d-flex gap-2">
          <button 
            type="button" 
            class="btn btn-primary"
            @click="saveStrategy"
            :disabled="!isStrategyValid"
          >
            保存策略
          </button>
          <button 
            type="button" 
            class="btn btn-outline-secondary"
            @click="resetStrategy"
          >
            重置
          </button>
        </div>
      </div>
    
  </Card>
</template>

<script>
import Card from '../common/Card.vue'

export default {
  name: 'TradingService',
  components: {
    Card
  },
  props: {
    loading: {
      type: Boolean,
      default: false
    }
  },
  data() {
    return {
      strategyType: '',
      riskLevel: '',
      maxPosition: 50,
      stopLoss: 5
    }
  },
  computed: {
    isStrategyValid() {
      return this.strategyType && this.riskLevel && this.maxPosition > 0 && this.stopLoss > 0
    }
  },
  methods: {
    saveStrategy() {
      if (!this.isStrategyValid) return
      
      const strategy = {
        type: this.strategyType,
        riskLevel: this.riskLevel,
        maxPosition: this.maxPosition,
        stopLoss: this.stopLoss,
        timestamp: new Date().toISOString()
      }
      
      // 触发事件通知父组件策略已保存
      this.$emit('strategy-saved', strategy)
      
      // 这里可以添加保存到本地存储或发送到服务器的逻辑
      console.log('策略已保存:', strategy)
      
      // 显示成功提示
      alert('策略保存成功!')
    },
    
    resetStrategy() {
      this.strategyType = ''
      this.riskLevel = ''
      this.maxPosition = 50
      this.stopLoss = 5
    },
    
    // 外部调用方法，用于获取当前策略配置
    getStrategy() {
      return {
        type: this.strategyType,
        riskLevel: this.riskLevel,
        maxPosition: this.maxPosition,
        stopLoss: this.stopLoss
      }
    },
    
    // 外部调用方法，用于设置策略配置
    setStrategy(strategy) {
      if (strategy) {
        this.strategyType = strategy.type || ''
        this.riskLevel = strategy.riskLevel || ''
        this.maxPosition = strategy.maxPosition || 50
        this.stopLoss = strategy.stopLoss || 5
      }
    }
  }
}
</script>

<style scoped>
/* 交易策略组件样式 */
.trading-strategy-section {
  margin-bottom: 2rem;
}

.section-header h5 {
  margin: 0;
  color: #495057;
  font-weight: 600;
}

.strategy-form {
  background-color: #f8f9fa;
  padding: 1.5rem;
  border-radius: 0.5rem;
  border: 1px solid #e9ecef;
}

.form-label {
  font-weight: 600;
  color: #495057;
  margin-bottom: 0.5rem;
}

.form-control, .form-select {
  border: 1px solid #ced4da;
  border-radius: 0.375rem;
  padding: 0.5rem 0.75rem;
  transition: border-color 0.15s ease-in-out, box-shadow 0.15s ease-in-out;
}

.form-control:focus, .form-select:focus {
  border-color: #80bdff;
  box-shadow: 0 0 0 0.2rem rgba(0, 123, 255, 0.25);
}

.btn {
  padding: 0.5rem 1rem;
  border-radius: 0.375rem;
  font-weight: 500;
  transition: all 0.15s ease-in-out;
}

.btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.gap-2 {
  gap: 0.5rem;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .strategy-form {
    padding: 1rem;
  }
  
  .d-flex.gap-2 {
    flex-direction: column;
    gap: 0.75rem;
  }
  
  .btn {
    width: 100%;
  }
}
</style> 