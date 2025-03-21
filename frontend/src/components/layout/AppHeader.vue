<template>
  <div class="header-container">
    <div class="left-section">
      <el-button
        icon="Menu"
        circle
        plain
        @click="toggleSidebar"
      />
      <el-breadcrumb separator="/">
        <el-breadcrumb-item :to="{ path: '/' }">首页</el-breadcrumb-item>
        <el-breadcrumb-item>{{ currentRouteName }}</el-breadcrumb-item>
      </el-breadcrumb>
    </div>
    
    <div class="right-section">
      <el-dropdown trigger="click" @command="handleCommand">
        <span class="user-dropdown">
          <el-avatar :size="32" :src="userAvatar" />
          <span class="username">{{ username }}</span>
          <el-icon><ArrowDown /></el-icon>
        </span>
        <template #dropdown>
          <el-dropdown-menu>
            <el-dropdown-item command="profile">个人信息</el-dropdown-item>
            <el-dropdown-item command="settings">设置</el-dropdown-item>
            <el-dropdown-item divided command="logout">退出登录</el-dropdown-item>
          </el-dropdown-menu>
        </template>
      </el-dropdown>
    </div>
  </div>
</template>

<script>
import { computed } from 'vue'
import { useStore } from 'vuex'
import { useRoute, useRouter } from 'vue-router'

export default {
  name: 'AppHeader',
  emits: ['toggle-sidebar'],
  setup(props, { emit }) {
    const store = useStore()
    const route = useRoute()
    const router = useRouter()
    
    const currentRouteName = computed(() => {
      const routeMap = {
        '/': '仪表盘',
        '/products': '商品管理',
        '/sales': '销售分析',
        '/replenishments': '补货管理',
        '/forecasts': '销量预测',
        '/data-processing': '数据处理'
      }
      return routeMap[route.path] || route.name
    })
    
    const user = computed(() => store.getters.currentUser || {})
    const username = computed(() => user.value?.username || '用户')
    const userAvatar = computed(() => user.value?.avatar || '')
    
    const toggleSidebar = () => {
      emit('toggle-sidebar')
    }
    
    const handleCommand = (command) => {
      if (command === 'logout') {
        store.dispatch('logout')
        router.push('/login')
      } else if (command === 'profile') {
        router.push('/profile')
      } else if (command === 'settings') {
        router.push('/settings')
      }
    }
    
    return {
      currentRouteName,
      username,
      userAvatar,
      toggleSidebar,
      handleCommand
    }
  }
}
</script>

<style scoped>
.header-container {
  width: 100%;
  height: 100%;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.left-section {
  display: flex;
  align-items: center;
}

.left-section .el-button {
  margin-right: 15px;
}

.right-section {
  display: flex;
  align-items: center;
}

.user-dropdown {
  display: flex;
  align-items: center;
  cursor: pointer;
}

.username {
  margin: 0 5px;
  font-size: 14px;
}
</style>