<template>
  <div class="page">
    <el-alert
      title="演示页说明"
      type="info"
      :closable="false"
      show-icon
      style="margin-bottom: 16px"
      description="系统设置仅为界面演示，配置不会写入后端。正式环境可对接配置中心或数据库持久化。"
    />
    <div class="panel-card settings-card">
      <el-tabs v-model="activeTab">
        <!-- 基础设置 -->
        <el-tab-pane label="基础设置" name="basic">
          <el-form :model="form" label-width="120px" class="settings-form">
            <el-form-item label="系统名称">
              <el-input v-model="form.systemName" />
            </el-form-item>
            <el-form-item label="主题色">
              <el-color-picker v-model="form.primaryColor" />
            </el-form-item>
            <el-form-item label="数据刷新周期">
              <el-select v-model="form.refresh" style="width: 200px">
                <el-option label="30 秒" value="30s" />
                <el-option label="1 分钟" value="1m" />
                <el-option label="5 分钟" value="5m" />
              </el-select>
            </el-form-item>
            <el-form-item label="通知设置">
              <el-switch v-model="form.emailNotice" active-text="邮件通知" style="margin-right: 24px" />
              <el-switch v-model="form.smsNotice" active-text="短信通知" />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="save">保存配置</el-button>
              <el-button @click="reset">重置</el-button>
            </el-form-item>
          </el-form>
        </el-tab-pane>

        <!-- 安全设置 -->
        <el-tab-pane label="安全设置" name="security">
          <el-form :model="securityForm" label-width="120px" class="settings-form">
            <el-form-item label="原密码">
              <el-input v-model="securityForm.oldPassword" type="password" show-password />
            </el-form-item>
            <el-form-item label="新密码">
              <el-input v-model="securityForm.newPassword" type="password" show-password />
            </el-form-item>
            <el-form-item label="确认新密码">
              <el-input v-model="securityForm.confirmPassword" type="password" show-password />
            </el-form-item>
            <el-form-item label="登录保护">
              <el-switch v-model="securityForm.twoFactor" active-text="开启双因子验证" />
            </el-form-item>
            <el-form-item label="IP 白名单">
              <el-input
                v-model="securityForm.ipWhitelist"
                type="textarea"
                :rows="2"
                placeholder="每行一个 IP 地址"
              />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="saveSecurity">保存安全设置</el-button>
            </el-form-item>
          </el-form>
        </el-tab-pane>
      </el-tabs>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { ElMessage } from 'element-plus'

const activeTab = ref('basic')

const form = reactive({
  systemName: '智慧政务数据管理系统',
  primaryColor: '#2B5FD7',
  refresh: '1m',
  emailNotice: true,
  smsNotice: false
})

const securityForm = reactive({
  oldPassword: '',
  newPassword: '',
  confirmPassword: '',
  twoFactor: false,
  ipWhitelist: ''
})

function save() {
  ElMessage.success('基础配置已保存')
}

function reset() {
  form.systemName = '智慧政务数据管理系统'
  form.primaryColor = '#2B5FD7'
  form.refresh = '1m'
  form.emailNotice = true
  form.smsNotice = false
}

function saveSecurity() {
  if (securityForm.newPassword && securityForm.newPassword !== securityForm.confirmPassword) {
    ElMessage.error('两次输入的新密码不一致')
    return
  }
  ElMessage.success('安全设置已保存')
}
</script>

<style scoped lang="scss">
.settings-card {
  max-width: 680px;
}

.settings-form {
  margin-top: 8px;
}
</style>
