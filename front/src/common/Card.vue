<template>
  <div class="card">
    <div 
      class="card-header d-flex justify-content-between align-items-center"
      :class="{ 'clickable': showToggle }"
      @click="handleHeaderClick"
    >
      <span class="card-title">{{ title }}</span>
      <button 
        v-if="showToggle"
        type="button" 
        class="btn btn-outline-secondary btn-sm toggle-btn"
        @click.stop="toggleCollapse"
      >
        {{ isCollapsed ? '展开' : '收起' }}
      </button>
    </div>
    <div class="card-body collapse-content" :class="{ 'collapsed': isCollapsed }">
      <slot></slot>
    </div>
  </div>
</template>

<script>
export default {
  name: 'Card',
  props: {
    title: {
      type: String,
      required: true
    },
    showToggle: {
      type: Boolean,
      default: true
    },
    defaultCollapsed: {
      type: Boolean,
      default: false
    },
    headerClickable: {
      type: Boolean,
      default: false
    }
  },
  emits: ['collapse-changed'],
  data() {
    return {
      isCollapsed: this.defaultCollapsed
    }
  },
  methods: {
    toggleCollapse() {
      this.isCollapsed = !this.isCollapsed
      this.$emit('collapse-changed', this.isCollapsed)
    },
    
    handleHeaderClick() {
      if (this.headerClickable && this.showToggle) {
        this.toggleCollapse()
      }
    },
    
    // 外部调用方法
    expand() {
      if (this.isCollapsed) {
        this.isCollapsed = false
        this.$emit('collapse-changed', this.isCollapsed)
      }
    },
    
    collapse() {
      if (!this.isCollapsed) {
        this.isCollapsed = true
        this.$emit('collapse-changed', this.isCollapsed)
      }
    },
    
    getCollapseState() {
      return this.isCollapsed
    },
    
    setCollapseState(collapsed) {
      if (this.isCollapsed !== collapsed) {
        this.isCollapsed = collapsed
        this.$emit('collapse-changed', this.isCollapsed)
      }
    }
  },
  
  watch: {
    defaultCollapsed(newVal) {
      this.isCollapsed = newVal
    }
  }
}
</script>

<style scoped>
.card {
  border: 1px solid #dee2e6;
  border-radius: 0.375rem;
  margin-bottom: 1rem;
  box-shadow: 0 0.125rem 0.25rem rgba(0, 0, 0, 0.075);
}

.card-header {
  background-color: #f8f9fa;
  border-bottom: 1px solid #dee2e6;
  font-weight: 600;
  padding: 0.75rem 1.25rem;
  transition: background-color 0.15s ease-in-out;
}

.card-header.clickable {
  cursor: pointer;
}

.card-header.clickable:hover {
  background-color: #e9ecef;
}

.card-title {
  color: #495057;
  font-size: 1.1rem;
  margin: 0;
}

.toggle-btn {
  border: none;
  padding: 0.25rem 0.75rem;
  transition: all 0.3s ease;
  border-radius: 0.375rem;
  font-size: 0.875rem;
  min-width: 60px;
}

.toggle-btn:hover {
  background-color: #e9ecef;
  color: #495057;
}

.toggle-btn:focus {
  box-shadow: 0 0 0 0.2rem rgba(0, 123, 255, 0.25);
}

.card-body {
  padding: 1.25rem;
}

.collapse-content {
  transition: all 0.3s ease-in-out;
  max-height: 2000px;
  overflow: visible;
  opacity: 1;
}

.collapse-content.collapsed {
  max-height: 0;
  overflow: hidden;
  padding: 0 1.25rem !important;
  opacity: 0;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .card-header {
    padding: 0.5rem 1rem;
  }
  
  .card-body {
    padding: 1rem;
  }
  
  .card-title {
    font-size: 1rem;
  }
}
</style> 