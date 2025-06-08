<template>
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
</template>

<script>
export default {
  name: 'ResultDisplay',
  props: {
    result: {
      type: String,
      default: ''
    }
  }
}
</script>

<style scoped>
.gap-2 {
  gap: 0.5rem;
}
</style> 