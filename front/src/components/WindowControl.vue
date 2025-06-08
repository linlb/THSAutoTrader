<template>
  <Card 
    ref="card"
    title="Window 控制调试" 
    :header-clickable="true"
    @collapse-changed="onCollapseChanged"
  >
    <div class="d-flex flex-column gap-2">
      <div 
        v-for="api in apis" 
        :key="api.url" 
        class="d-flex align-items-center gap-2 flex-nowrap"
      >
        <label class="me-2 flex-shrink-0">{{ api.label }}</label>
        <input
          type="text"
          class="form-control flex-shrink-1"
          :value="api.url"
        />
        <button
          class="btn btn-primary flex-shrink-0"
          @click="handleApiCall(api.url)"
          :disabled="loadingStates[api.url]"
        >
          {{ loadingStates[api.url] ? '请求中...' : '执行' }}
        </button>
      </div>
      
      <!-- 集成结果显示区域 -->
      <div class="mt-3">
        <div class="d-flex align-items-center gap-2 flex-nowrap">
          <label class="me-2 flex-shrink-0">返回结果</label>
          <textarea
            :value="result"
            class="form-control flex-shrink-1"
            rows="6"
            disabled
            placeholder="API调用结果将显示在这里..."
          ></textarea>
        </div>
      </div>
    </div>
  </Card>
</template>

<script>
import { ref, reactive } from 'vue'
import Card from '../common/Card.vue'

export default {
  name: 'WindowControl',
  components: {
    Card
  },
  props: {
    result: {
      type: String,
      default: ''
    }
  },
  emits: ['api-call', 'collapse-changed'],
  setup(props, { emit }) {
    const apis = ref([
      {
        label: '获取持仓',
        url: 'http://localhost:5000/position'
      },
      {
        label: '获取资金',
        url: 'http://localhost:5000/balance'
      },
      {
        label: '下单接口',
        url: 'http://localhost:5000/xiadan?code=600000&status=1'
      },
      {
        label: '撤单接口',
        url: 'http://localhost:5000/cancel_all_orders'
      }
    ])

    // 为每个API创建独立的loading状态
    const loadingStates = reactive({})
    
    // 初始化所有API的loading状态
    apis.value.forEach(api => {
      loadingStates[api.url] = false
    })

    const handleApiCall = async (url) => {
      loadingStates[url] = true
      try {
        await emit('api-call', url)
      } finally {
        loadingStates[url] = false
      }
    }

    const onCollapseChanged = (collapsed) => {
      emit('collapse-changed', collapsed)
    }

    return {
      apis,
      loadingStates,
      handleApiCall,
      onCollapseChanged
    }
  }
}
</script>

<style scoped>
.gap-2 {
  gap: 0.5rem;
}
</style> 