<template>
  <div class="app-container">
    <el-container v-if="isAuthenticated">
      <el-aside width="220px">
        <app-sidebar />
      </el-aside>
      <el-container>
        <el-header height="60px">
          <app-header />
        </el-header>
        <el-main>
          <router-view />
        </el-main>
        <el-footer height="40px">
          <app-footer />
        </el-footer>
      </el-container>
    </el-container>
    
    <div v-else class="auth-container">
      <login-form v-if="!isRegistering" @switch-mode="isRegistering = true" />
      <register-form v-else @switch-mode="isRegistering = false" />
    </div>
  </div>
</template>

<script>
import { computed, ref } from 'vue'
import { useStore } from 'vuex'
import AppSidebar from './components/layout/AppSidebar.vue'
import AppHeader from './components/layout/AppHeader.vue'
import AppFooter from './components/layout/AppFooter.vue'
import LoginForm from './components/auth/LoginForm.vue'
import RegisterForm from './components/auth/RegisterForm.vue'

export default {
  name: 'App',
  components: {
    AppSidebar,
    AppHeader,
    AppFooter,
    LoginForm,
    RegisterForm
  },
  setup() {
    const store = useStore()
    const isRegistering = ref(false)
    const isAuthenticated = computed(() => store.getters.isAuthenticated)
    
    return {
      isRegistering,
      isAuthenticated
    }
  }
}
</script>

<style>
html, body {
  margin: 0;
  padding: 0;
  height: 100%;
  font-family: 'Helvetica Neue', Helvetica, 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', Arial, sans-serif;
}

#app {
  height: 100vh;
}

.app-container {
  height: 100vh;
}

.el-header {
  background-color: #fff;
  color: #333;
  border-bottom: 1px solid #eee;
  display: flex;
  align-items: center;
  padding: 0 20px;
}

.el-aside {
  background-color: #304156;
  color: #fff;
}

.el-main {
  background-color: #f5f7fa;
  padding: 20px;
}

.el-footer {
  background-color: #fff;
  color: #999;
  text-align: center;
  font-size: 12px;
  border-top: 1px solid #eee;
  display: flex;
  align-items: center;
  justify-content: center;
}

.auth-container {
  height: 100vh;
  display: flex;
  justify-content: center;
  align-items: center;
  background-color: #f5f7fa;
}
</style>