<template>
  <div class="register-container">
    <div class="register-header">
      <h2>零售单店智能补货系统</h2>
      <p>创建新账户</p>
    </div>
    
    <el-form
      ref="registerForm"
      :model="registerForm"
      :rules="rules"
      label-position="top"
      class="register-form">
      
      <el-form-item label="用户名" prop="username">
        <el-input
          v-model="registerForm.username"
          prefix-icon="User"
          placeholder="请输入用户名"
        />
      </el-form-item>
      
      <el-form-item label="邮箱" prop="email">
        <el-input
          v-model="registerForm.email"
          prefix-icon="Message"
          placeholder="请输入邮箱"
        />
      </el-form-item>
      
      <el-form-item label="密码" prop="password">
        <el-input
          v-model="registerForm.password"
          prefix-icon="Lock"
          type="password"
          placeholder="请输入密码"
          show-password
        />
      </el-form-item>
      
      <el-form-item label="确认密码" prop="confirmPassword">
        <el-input
          v-model="registerForm.confirmPassword"
          prefix-icon="Lock"
          type="password"
          placeholder="请再次输入密码"
          show-password
        />
      </el-form-item>
      
      <el-form-item>
        <el-button
          type="primary"
          :loading="loading"
          class="submit-btn"
          @click="submitForm">
          注册
        </el-button>
      </el-form-item>
      
      <div class="login-link">
        <span>已有账户?</span>
        <el-button type="text" @click="$emit('switch-mode')">返回登录</el-button>
      </div>
    </el-form>
  </div>
</template>

<script>
import { ref, reactive, computed } from 'vue'
import { useStore } from 'vuex'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'

export default {
  name: 'RegisterForm',
  emits: ['switch-mode'],
  setup() {
    const store = useStore()
    const router = useRouter()
    const registerForm = reactive({
      username: '',
      email: '',
      password: '',
      confirmPassword: ''
    })
    
    const loading = computed(() => store.getters.isLoading)
    
    const validatePass2 = (rule, value, callback) => {
      if (value === '') {
        callback(new Error('请再次输入密码'))
      } else if (value !== registerForm.password) {
        callback(new Error('两次输入密码不一致!'))
      } else {
        callback()
      }
    }
    
    const rules = {
      username: [
        { required: true, message: '请输入用户名', trigger: 'blur' },
        { min: 3, max: 20, message: '长度在 3 到 20 个字符', trigger: 'blur' }
      ],
      email: [
        { required: true, message: '请输入邮箱地址', trigger: 'blur' },
        { type: 'email', message: '请输入正确的邮箱地址', trigger: 'blur' }
      ],
      password: [
        { required: true, message: '请输入密码', trigger: 'blur' },
        { min: 6, max: 30, message: '长度在 6 到 30 个字符', trigger: 'blur' }
      ],
      confirmPassword: [
        { required: true, message: '请再次输入密码', trigger: 'blur' },
        { validator: validatePass2, trigger: 'blur' }
      ]
    }
    
    const registerForm_ref = ref(null)
    
    const submitForm = async () => {
      if (!registerForm_ref.value) return
      
      try {
        await registerForm_ref.value.validate()
        
        await store.dispatch('register', {
          username: registerForm.username,
          email: registerForm.email,
          password: registerForm.password
        })
        
        ElMessage.success('注册成功')
        router.push('/')
      } catch (error) {
        console.error('Registration error:', error)
        ElMessage.error(error.response?.data?.detail || '注册失败，请稍后重试')
      }
    }
    
    return {
      registerForm,
      loading,
      rules,
      registerForm_ref,
      submitForm
    }
  }
}
</script>

<style scoped>
.register-container {
  width: 400px;
  padding: 30px;
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
}

.register-header {
  text-align: center;
  margin-bottom: 30px;
}

.register-header h2 {
  margin-bottom: 10px;
  color: #303133;
}

.register-header p {
  color: #909399;
  margin: 0;
}

.register-form {
  margin-top: 20px;
}

.submit-btn {
  width: 100%;
}

.login-link {
  margin-top: 15px;
  text-align: center;
}

.login-link span {
  color: #909399;
  margin-right: 5px;
}
</style>