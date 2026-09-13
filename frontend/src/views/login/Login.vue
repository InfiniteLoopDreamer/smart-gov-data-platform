<template>
  <div class="login-page">
    <div class="login-card">
      <div class="login-logo">政</div>
      <h1 class="login-title">{{ mode === 'login' ? '登录' : '注册' }}</h1>
      <p class="login-sub">智慧政务数据管理系统</p>

      <!-- 登录表单 -->
      <el-form v-if="mode === 'login'" :model="loginForm" @keyup.enter="handleLogin">
        <el-form-item>
          <el-input v-model="loginForm.username" placeholder="用户名" size="large" clearable>
            <template #prefix><el-icon><User /></el-icon></template>
          </el-input>
        </el-form-item>
        <el-form-item>
          <el-input v-model="loginForm.password" type="password" placeholder="密码" size="large" show-password>
            <template #prefix><el-icon><Lock /></el-icon></template>
          </el-input>
        </el-form-item>
        <el-button type="primary" size="large" class="login-btn" :loading="loading" @click="handleLogin">
          登 录
        </el-button>
      </el-form>

      <!-- 注册表单 -->
      <el-form v-else :model="registerForm" @keyup.enter="handleRegister">
        <el-form-item>
          <el-input v-model="registerForm.username" placeholder="用户名" size="large" clearable>
            <template #prefix><el-icon><User /></el-icon></template>
          </el-input>
        </el-form-item>
        <el-form-item>
          <el-input v-model="registerForm.password" type="password" placeholder="密码" size="large" show-password>
            <template #prefix><el-icon><Lock /></el-icon></template>
          </el-input>
        </el-form-item>
        <el-form-item>
          <el-input v-model="registerForm.name" placeholder="姓名" size="large" clearable>
            <template #prefix><el-icon><Postcard /></el-icon></template>
          </el-input>
        </el-form-item>
        <el-form-item>
          <el-input v-model="registerForm.department" placeholder="所属部门（选填）" size="large" clearable>
            <template #prefix><el-icon><OfficeBuilding /></el-icon></template>
          </el-input>
        </el-form-item>
        <el-button type="primary" size="large" class="login-btn" :loading="loading" @click="handleRegister">
          注册并登录
        </el-button>
      </el-form>

      <div class="login-switch">
        <span v-if="mode === 'login'">没有账号？<a @click="mode = 'register'">立即注册</a></span>
        <span v-else>已有账号？<a @click="mode = 'login'">返回登录</a></span>
      </div>

      <p class="login-tip">管理员：admin / admin123　·　普通用户：user / user123</p>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { api } from '@/api'
import { auth } from '@/auth'

const router = useRouter()
const mode = ref('login')
const loading = ref(false)

const loginForm = reactive({
  username: 'admin',
  password: 'admin123'
})

const registerForm = reactive({
  username: '',
  password: '',
  name: '',
  department: ''
})

async function handleLogin() {
  if (!loginForm.username || !loginForm.password) {
    ElMessage.warning('请输入用户名和密码')
    return
  }
  loading.value = true
  try {
    const { token, user } = await api.login(loginForm.username, loginForm.password)
    auth.set(token, user)
    ElMessage.success(`欢迎回来，${user.name}`)
    router.push(user.role === 'admin' ? '/home' : '/citizen')
  } catch (err) {
    const detail = err.response?.data?.detail || '登录失败'
    ElMessage.error(detail === '用户名或密码错误' ? detail : '无法连接后端，请确认服务已启动')
  } finally {
    loading.value = false
  }
}

async function handleRegister() {
  if (!registerForm.username || !registerForm.password) {
    ElMessage.warning('请填写用户名和密码')
    return
  }
  loading.value = true
  try {
    await api.register(registerForm)
    ElMessage.success('注册成功，正在登录…')
    // 注册成功后自动登录
    const { token, user } = await api.login(registerForm.username, registerForm.password)
    auth.set(token, user)
    router.push(user.role === 'admin' ? '/home' : '/citizen')
  } catch (err) {
    const detail = err.response?.data?.detail || '注册失败'
    ElMessage.error(detail)
  } finally {
    loading.value = false
  }
}
</script>

<style scoped lang="scss">
.login-page {
  height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #1a2b4c 0%, #2b5fd7 100%);
}

.login-card {
  width: 400px;
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.25);
  padding: 40px 36px;
  text-align: center;
}

.login-logo {
  width: 56px;
  height: 56px;
  border-radius: 14px;
  background: linear-gradient(135deg, #2b5fd7, #5581e0);
  color: #fff;
  font-size: 28px;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto 16px;
}

.login-title {
  font-size: 22px;
  font-weight: 700;
  color: #1e293b;
  margin: 0 0 4px;
}

.login-sub {
  font-size: 13px;
  color: #94a3b8;
  margin: 0 0 24px;
}

.login-btn {
  width: 100%;
  margin-top: 4px;
}

.login-switch {
  margin-top: 16px;
  font-size: 13px;
  color: #64748b;
}

.login-switch a {
  color: #2b5fd7;
  cursor: pointer;
}

.login-tip {
  font-size: 12px;
  color: #94a3b8;
  margin-top: 16px;
}
</style>
