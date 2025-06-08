<template>
  <Card 
    ref="card"
    title="股票池管理" 
    :default-collapsed="defaultCollapsed"
    @collapse-changed="onCollapseChanged"
  >
      <!-- 添加股票按钮 -->
      <div class="section-header">
        <h5>股票池</h5>
        <button 
          type="button" 
          class="btn btn-primary btn-sm"
          @click="showAddStockModal = true"
          :disabled="loading"
        >
          <i class="fas fa-plus"></i> 添加股票
        </button>
      </div>
      
      <!-- 股票池表格 -->
      <div class="table-responsive">
        <table class="table table-striped table-hover">
          <thead class="table-dark">
            <tr>
              <th scope="col">#</th>
              <th scope="col">股票代码</th>
              <th scope="col">股票名称</th>
              <th scope="col">当前价格</th>
              <th scope="col">涨跌幅</th>
              <th scope="col">操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="stockPool.length === 0">
              <td colspan="6" class="text-center text-muted">
                暂无股票，请点击上方按钮添加股票
              </td>
            </tr>
            <tr v-for="(stock, index) in stockPool" :key="stock.code">
              <th scope="row">{{ index + 1 }}</th>
              <td>{{ stock.code }}</td>
              <td>{{ stock.name }}</td>
              <td class="text-end">
                <span v-if="stock.price">￥{{ stock.price.toFixed(2) }}</span>
                <span v-else class="text-muted">--</span>
              </td>
              <td class="text-end">
                <span v-if="stock.change !== null" 
                      :class="{'text-success': stock.change > 0, 'text-danger': stock.change < 0}">
                  {{ stock.change > 0 ? '+' : '' }}{{ stock.change?.toFixed(2) }}%
                </span>
                <span v-else class="text-muted">--</span>
              </td>
              <td>
                <button 
                  type="button" 
                  class="btn btn-outline-danger btn-sm"
                  @click="removeStock(index)"
                  :disabled="loading"
                >
                  <i class="fas fa-trash"></i> 删除
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
      
      <!-- 添加股票模态框 -->
      <div v-if="showAddStockModal" class="modal-overlay" @click.self="showAddStockModal = false">
        <div class="modal-dialog">
          <div class="modal-content">
            <div class="modal-header">
              <h5 class="modal-title">添加股票</h5>
              <button type="button" class="btn-close" @click="showAddStockModal = false"></button>
            </div>
            <div class="modal-body">
              <form @submit.prevent="addStock">
                <div class="mb-3">
                  <label for="stockCode" class="form-label">股票搜索 <span class="text-danger">*</span></label>
                  <input 
                    type="text" 
                    class="form-control" 
                    id="stockCode"
                    v-model="searchKeyword"
                    @input="onSearchInput"
                    placeholder="输入股票代码或名称搜索，如：000001、平安银行"
                    autocomplete="off"
                  >
                  <div class="form-text">输入关键词自动搜索股票</div>
                  
                  <!-- 搜索结果下拉列表 -->
                  <div v-if="searchResults.length > 0" class="search-results">
                    <div 
                      v-for="stock in searchResults" 
                      :key="stock.OuterCode"
                      class="search-result-item"
                      @click="selectStock(stock)"
                    >
                      <div class="stock-info">
                        <span class="stock-code">{{ stock.OuterCode }}</span>
                        <span class="stock-name">{{ stock.ShortName }}</span>
                      </div>
                    </div>
                  </div>
                  
                  <!-- 搜索状态提示 -->
                  <div v-if="isSearching" class="search-status">
                    <i class="fas fa-spinner fa-spin"></i> 搜索中...
                  </div>
                  
                  <div v-if="searchError" class="search-status text-danger">
                    <i class="fas fa-exclamation-triangle"></i> {{ searchError }}
                  </div>
                  
                  <!-- 已选择的股票显示 -->
                  <div v-if="selectedStock" class="selected-stock">
                    <div class="selected-stock-info">
                      <strong>已选择：</strong>
                      <span class="badge bg-primary">{{ selectedStock.OuterCode }}</span>
                      <span>{{ selectedStock.ShortName }}</span>
                      <button 
                        type="button" 
                        class="btn btn-sm btn-outline-secondary ms-2"
                        @click="clearSelection"
                      >
                        重新选择
                      </button>
                    </div>
                  </div>
                </div>
              </form>
            </div>
            <div class="modal-footer">
              <button type="button" class="btn btn-secondary" @click="showAddStockModal = false">
                取消
              </button>
              <button type="button" class="btn btn-primary" @click="addStock" :disabled="!canAddStock">
                添加
              </button>
            </div>
          </div>
        </div>
      </div>
  </Card>
</template>

<script>
import Card from '../common/Card.vue'

export default {
  name: 'StockPool',
  components: {
    Card
  },
  props: {
    loading: {
      type: Boolean,
      default: false
    },
    defaultCollapsed: {
      type: Boolean,
      default: false
    }
  },
  data() {
    return {
      stockPool: [],
      showAddStockModal: false,
      searchKeyword: '',
      searchResults: [],
      selectedStock: null,
      isSearching: false,
      searchError: '',
      searchTimeout: null
    }
  },
  computed: {
    canAddStock() {
      return this.selectedStock && 
             !this.stockPool.some(stock => stock.code === this.selectedStock.OuterCode)
    }
  },
  methods: {
    addStock() {
      if (!this.canAddStock) return
      
      const stock = {
        code: this.selectedStock.OuterCode,
        name: this.selectedStock.ShortName,
        price: null,
        change: null
      }
      
      this.stockPool.push(stock)
      this.resetSearch()
      this.showAddStockModal = false
      
      // 触发事件通知父组件股票池已更新
      this.$emit('stock-pool-updated', this.stockPool)
    },
    
    removeStock(index) {
      this.stockPool.splice(index, 1)
      this.$emit('stock-pool-updated', this.stockPool)
    },
    
    onSearchInput() {
      // 清除之前的搜索定时器
      if (this.searchTimeout) {
        clearTimeout(this.searchTimeout)
      }
      
      // 清除之前的选择和搜索结果
      this.selectedStock = null
      this.searchResults = []
      this.searchError = ''
      
      // 如果输入为空，直接返回
      if (!this.searchKeyword.trim()) {
        return
      }
      
      // 设置防抖，500ms后执行搜索
      this.searchTimeout = setTimeout(() => {
        this.searchStocks()
      }, 500)
    },
    
    searchStocks() {
      if (!this.searchKeyword.trim()) return
      
      this.isSearching = true
      this.searchError = ''
      
      // 生成唯一的回调函数名
      const callbackName = 'stockSearchCallback_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9)
      
      // 创建全局回调函数
      window[callbackName] = (data) => {
        this.isSearching = false
        try {
          if (data && data.GubaCodeTable && data.GubaCodeTable.Data) {
            this.searchResults = data.GubaCodeTable.Data.slice(0, 8) // 最多显示8个结果
          } else {
            this.searchResults = []
            this.searchError = '未找到相关股票'
          }
        } catch (error) {
          this.searchError = '搜索出错，请重试'
          console.error('Stock search error:', error)
        }
        
        // 清理全局回调函数和script标签
        delete window[callbackName]
        const script = document.getElementById(callbackName)
        if (script) {
          document.head.removeChild(script)
        }
      }
      
      // 构建请求URL
      const baseUrl = 'https://searchadapter.eastmoney.com/api/suggest/get'
      const params = new URLSearchParams({
        cb: callbackName,
        input: this.searchKeyword.trim(),
        type: '8',
        token: 'D43BF722C8E33BDC906FB84D85E326E8',
        markettype: '',
        mktnum: '',
        jys: '',
        classify: '',
        securitytype: '',
        status: '',
        count: '8',
        _: Date.now().toString()
      })
      
      // 创建script标签进行JSONP请求
      const script = document.createElement('script')
      script.id = callbackName
      script.src = `${baseUrl}?${params.toString()}`
      script.onerror = () => {
        this.isSearching = false
        this.searchError = '网络请求失败，请检查网络连接'
        delete window[callbackName]
      }
      
      document.head.appendChild(script)
    },
    
    selectStock(stock) {
      this.selectedStock = stock
      this.searchResults = []
      this.searchKeyword = `${stock.OuterCode} ${stock.ShortName}`
    },
    
    clearSelection() {
      this.selectedStock = null
      this.searchKeyword = ''
      this.searchResults = []
    },
    
    resetSearch() {
      this.searchKeyword = ''
      this.searchResults = []
      this.selectedStock = null
      this.searchError = ''
      this.isSearching = false
      if (this.searchTimeout) {
        clearTimeout(this.searchTimeout)
        this.searchTimeout = null
      }
    },
    
    // 外部调用方法，用于获取股票池数据
    getStockPool() {
      return this.stockPool
    },
    
    // 外部调用方法，用于设置股票池数据
    setStockPool(stockPool) {
      this.stockPool = stockPool || []
    },
    
    // Card组件collapse状态变化回调
    onCollapseChanged(collapsed) {
      this.$emit('collapse-changed', collapsed)
    },
    
    // 外部调用方法 - 通过ref访问Card组件
    expand() {
      this.$refs.card?.expand()
    },
    
    collapse() {
      this.$refs.card?.collapse()
    },
    
    getCollapseState() {
      return this.$refs.card?.getCollapseState()
    }
  }
}
</script>

<style scoped>
/* 股票池组件样式 */


.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
  padding-bottom: 0.5rem;
  border-bottom: 2px solid #e9ecef;
}

.section-header h5 {
  margin: 0;
  color: #495057;
}

.table {
  margin-bottom: 0;
}

.table th {
  font-weight: 600;
  border-top: none;
}

.table td, .table th {
  vertical-align: middle;
  padding: 0.75rem;
}

/* 模态框样式 */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1050;
}

.modal-dialog {
  background: white;
  border-radius: 0.5rem;
  box-shadow: 0 0.5rem 1rem rgba(0, 0, 0, 0.15);
  width: 90%;
  max-width: 500px;
}

.modal-content {
  border: none;
}

.modal-header {
  padding: 1rem 1.5rem;
  border-bottom: 1px solid #e9ecef;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.modal-title {
  margin: 0;
  font-weight: 600;
}

.btn-close {
  background: none;
  border: none;
  font-size: 1.25rem;
  cursor: pointer;
  padding: 0;
  width: 1em;
  height: 1em;
}

.btn-close:before {
  content: '×';
}

.modal-body {
  padding: 1.5rem;
}

.modal-footer {
  padding: 1rem 1.5rem;
  border-top: 1px solid #e9ecef;
  display: flex;
  gap: 0.5rem;
  justify-content: flex-end;
}

.form-text {
  font-size: 0.875rem;
  color: #6c757d;
}

/* 股票搜索样式 */
.search-results {
  position: absolute;
  top: 100%;
  left: 0;
  right: 0;
  background: white;
  border: 1px solid #dee2e6;
  border-top: none;
  border-radius: 0 0 0.375rem 0.375rem;
  max-height: 200px;
  overflow-y: auto;
  z-index: 1000;
  box-shadow: 0 0.125rem 0.25rem rgba(0, 0, 0, 0.075);
}

.search-result-item {
  padding: 0.75rem;
  cursor: pointer;
  border-bottom: 1px solid #f8f9fa;
  transition: background-color 0.15s ease-in-out;
}

.search-result-item:hover {
  background-color: #f8f9fa;
}

.search-result-item:last-child {
  border-bottom: none;
}

.stock-info {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.stock-code {
  font-weight: 600;
  color: #495057;
  min-width: 80px;
}

.stock-name {
  color: #6c757d;
  flex: 1;
}

.search-status {
  padding: 0.5rem;
  font-size: 0.875rem;
  color: #6c757d;
}

.selected-stock {
  margin-top: 1rem;
  padding: 1rem;
  background-color: #f8f9fa;
  border-radius: 0.375rem;
  border: 1px solid #e9ecef;
}

.selected-stock-info {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  flex-wrap: wrap;
}

.badge {
  font-size: 0.875rem;
}

/* 输入框相对定位，为搜索结果定位做准备 */
.mb-3 {
  position: relative;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .section-header {
    flex-direction: column;
    gap: 1rem;
    align-items: stretch;
  }
  
  .modal-dialog {
    margin: 1rem;
    width: auto;
  }
  
  .selected-stock-info {
    flex-direction: column;
    align-items: flex-start;
  }
}
</style>