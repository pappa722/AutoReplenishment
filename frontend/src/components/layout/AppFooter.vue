<template>
  <div class="footer-container">
    <span>零售单店智能补货系统 &copy; {{ currentYear }}</span>
  </div>
</template>

<script>
import { ref } from 'vue'

export default {
  name: 'AppFooter',
  setup() {
    const currentYear = ref(new Date().getFullYear())
    
    return {
      currentYear
    }
  }
}
</script>

<style scoped>
.footer-container {
  width: 100%;
  text-align: center;
  color: #909399;
  font-size: 12px;
}
</style>