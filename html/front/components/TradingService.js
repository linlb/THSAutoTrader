const TradingService = {
  props: ['loading'],
  emits: ['execute-trade'],
  methods: {
    handleExecuteTrade() {
      this.$emit('execute-trade');
    },
  },
  template: `
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
    `,
};
