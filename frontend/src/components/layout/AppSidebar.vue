<template>
  <div class="sidebar">
    <div class="logo-container">
      <img src="@/assets/logo.png" alt="Logo" class="logo" />
      <h2>零售补货系统</h2>
    </div>
    
    <el-menu
      router
      :default-active="activeRoute"
      class="sidebar-menu"
      background-color="#304156"
      text-color="#bfcbd9"
      active-text-color="#409EFF">
      
      <el-menu-item index="/">
        <el-icon><DataLine /></el-icon>
        <span>仪表盘</span>
      </el-menu-item>
      
      <el-menu-item index="/products">
        <el-icon><Goods /></el-icon>
        <span>商品管理</span>
      </el-menu-item>
      
      <el-menu-item index="/sales">
        <el-icon><ShoppingCart /></el-icon>
        <span>销售分析</span>
      </el-menu-item>
      
      <el-menu-item index="/replenishments">
        <el-icon><Box /></el-icon>
        <span>补货管理</span>
      </el-menu-item>
      
      <el-menu-item index="/forecasts">
        <el-icon><TrendCharts /></el-icon>
        <span>销量预测</span>
      </el-menu-item>
      
      <el-menu-item index="/data-processing">
        <el-icon><DataAnalysis /></el-icon>
        <span>数据处理</span>
      </el-menu-item>
    </el-menu>
  </div>
</template>

<script>
import { computed } from 'vue'
import { useRoute } from 'vue-router'

export default {
  name: 'AppSidebar',
  setup() {
    const route = useRoute()
    const activeRoute = computed(() => route.path)
    
    return {
      activeRoute
    }
  }
}
</script>

<style scoped>
.sidebar {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.logo-container {
  height: 60px;
  padding: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
}

.logo {
  width: 30px;
  height: 30px;
  margin-right: 10px;
}

.sidebar-menu {
  border-right: none;
}

.el-menu-item {
  display: flex;
  align-items: center;
}

.el-icon {
  margin-right: 10px;
}
</style>