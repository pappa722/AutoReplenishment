<template>
  <div class="login-container">
    <div class="login-header">
      <h2>零售单店智能补货系统</h2>
      <p>登录您的账户</p>
    </div>
    
    <el-form
      ref="loginFormRef"
      :model="loginForm"
      :rules="rules"
      label-position="top"
      class="login-form">
      
      <el-form-item label="用户名" prop="username">
        <el-input
          v-model="loginForm.username"
          :prefix-icon="User"
          placeholder="请输入用户名"
        />
      </el-form-item>
      
      <el-form-item label="密码" prop="password">
        <el-input
          v-model="loginForm.password"
          :prefix-icon="Lock"
          type="password"
          placeholder="请输入密码"
          show-password
        />
      </el-form-item>
      
      <div class="form-actions">
        <el-checkbox v-model="rememberMe">记住我</el-checkbox>
        <el-button text>忘记密码?</el-button>
      </div>
      
      <el-form-item>
        <el-button
          type="primary"
          :loading="loading"
          class="submit-btn"
          @click="submitForm">
          登录
        </el-button>
      </el-form-item>
      
      <div class="register-link">
        <span>还没有账户?</span>
        <el-button text @click="$emit('switch-mode')">注册新账户</el-button>
      </div>
    </el-form>
  </div>
</template>

<script setup>
import { ref, reactive, computed } from 'vue'
import { useStore } from 'vuex'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { User, Lock } from '@element-plus/icons-vue'

const emit = defineEmits(['switch-mode'])
const store = useStore()
const router = useRouter()
const loginForm = reactive({
  username: '',
  password: ''
})
const rememberMe = ref(false)
const loading = computed(() => store.getters.isLoading)

const rules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 20, message: '长度在 3 到 20 个字符', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, max: 30, message: '长度在 6 到 30 个字符', trigger: 'blur' }
  ]
}

const loginFormRef = ref(null)

const submitForm = async () => {
  if (!loginFormRef.value) return
  
  try {
    await loginFormRef.value.validate()
    
    await store.dispatch('login', {
      username: loginForm.username,
      password: loginForm.password,
      remember_me: rememberMe.value
    })
    
    ElMessage.success('登录成功')
    router.push('/')
  } catch (error) {
    console.error('Login error:', error)
    ElMessage.error(error.response?.data?.detail || '登录失败，请检查用户名和密码')
  }
}
</script>

<style scoped>
.login-container {
  width: 400px;
  padding: 30px;
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
}

.login-header {
  text-align: center;
  margin-bottom: 30px;
}

.login-header h2 {
  margin-bottom: 10px;
  color: #303133;
}

.login-header p {
  color: #909399;
  margin: 0;
}

.login-form {
  margin-top: 20px;
}

.form-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.submit-btn {
  width: 100%;
}

.register-link {
  margin-top: 15px;
  text-align: center;
}

.register-link span {
  color: #909399;
  margin-right: 5px;
}
</style>