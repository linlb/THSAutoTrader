const { createApp } = Vue;

createApp({
  components: {
    WindowControl,
    TradingService,
    ResultDisplay,
  },
  data() {
    return {
      result: '',
      loading: false,
      apis: [
        {
          label: '获取持仓',
          url: 'http://localhost:5000/position',
        },
        {
          label: '获取资金',
          url: 'http://localhost:5000/balance',
        },
      ],
    };
  },
  methods: {
    async callApi(url) {
      this.loading = true;
      try {
        const response = await axios.get(url);
        this.result = JSON.stringify(response.data, null, 2);
      } catch (error) {
        console.error('请求失败:', error);
        this.result = '请求失败: ' + error.message;
      } finally {
        this.loading = false;
      }
    },
    async executeTrade() {
      this.loading = true;
      try {
        // 这里可以调用交易相关的API
        const response = await axios.post('http://localhost:5000/trade');
        this.result = JSON.stringify(response.data, null, 2);
      } catch (error) {
        console.error('交易操作失败:', error);
        this.result = '交易操作失败: ' + error.message;
      } finally {
        this.loading = false;
      }
    },
  },
  template: `
        <div class="container mt-5">
            <h1 class="text-center">自动化控制面板</h1>
            <div class="row mt-4">
                <div class="col-md-6">
                    <WindowControl 
                        :loading="loading" 
                        @api-call="callApi"
                    />
                    <div class="mt-3">
                        <div class="card">
                            <div class="card-body">
                                <ResultDisplay :result="result" />
                            </div>
                        </div>
                    </div>
                </div>
                <div class="col-md-6">
                    <TradingService 
                        :loading="loading" 
                        @execute-trade="executeTrade"
                    />
                </div>
            </div>
        </div>
    `,
}).mount('#app');
