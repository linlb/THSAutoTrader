const WindowControl = {
  props: ['loading'],
  emits: ['api-call'],
  data() {
    return {
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
    handleApiCall(url) {
      this.$emit('api-call', url);
    },
  },
  template: `
        <div class="card">
            <div class="card-header">Window 控制</div>
            <div class="card-body d-flex flex-column gap-2">
                <div v-for="api in apis" :key="api.url" class="d-flex align-items-center gap-2 flex-nowrap">
                    <label class="me-2 flex-shrink-0">{{ api.label }}</label>
                    <input
                        type="text"
                        class="form-control flex-shrink-1"
                        :value="api.url"
                        disabled
                    />
                    <button
                        class="btn btn-primary flex-shrink-0"
                        @click="handleApiCall(api.url)"
                        :disabled="loading"
                    >
                        {{ loading ? '请求中...' : '点击' }}
                    </button>
                </div>
            </div>
        </div>
    `,
};
