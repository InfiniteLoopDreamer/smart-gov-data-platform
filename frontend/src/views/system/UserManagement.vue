<template>
  <div class="page">
    <el-alert
      title="账号、角色、所属部门与启停状态均由后端持久化；停用后现有登录凭证会立即失效。"
      type="success"
      show-icon
      :closable="false"
      style="margin-bottom: 16px"
    />
    <div class="panel-card">
      <!-- 顶部操作 -->
      <div class="toolbar">
        <div>
          <el-input v-model="keyword" placeholder="搜索姓名 / 用户名" clearable style="width: 220px">
            <template #prefix><el-icon><Search /></el-icon></template>
          </el-input>
          <el-select v-model="roleFilter" placeholder="角色" clearable style="width: 150px; margin-left: 12px">
            <el-option v-for="r in roles" :key="r.value" :label="r.label" :value="r.label" />
          </el-select>
        </div>
        <el-button type="primary" @click="openDialog()">
          <el-icon style="margin-right: 4px"><Plus /></el-icon>新增用户
        </el-button>
      </div>

      <!-- 用户表格 -->
      <el-table :data="filteredUsers" stripe>
        <el-table-column prop="name" label="姓名" width="130" />
        <el-table-column prop="username" label="用户名" width="130" />
        <el-table-column prop="role" label="角色" width="140">
          <template #default="{ row }">
            <el-tag :type="row.role === '超级管理员' ? 'danger' : row.role === '部门人员' ? 'warning' : 'primary'" effect="light" round>
              {{ row.role }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="department" label="部门" width="140" />
        <el-table-column prop="createdAt" label="创建时间" width="170" />
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.status === '启用' ? 'success' : 'info'" effect="light" round>
              {{ row.status }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="180">
          <template #default="{ row }">
            <el-button type="primary" link size="small" @click="openDialog(row)">编辑</el-button>
            <el-button
              :type="row.status === '启用' ? 'warning' : 'success'"
              link
              size="small"
              :disabled="row.username === 'admin'"
              @click="toggleStatus(row)"
            >
              {{ row.status === '启用' ? '停用' : '启用' }}
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <!-- 新增 / 编辑弹窗 -->
    <el-dialog v-model="dialogVisible" :title="editingId ? '编辑用户' : '新增用户'" width="460px">
      <el-form ref="formRef" :model="form" :rules="rules" label-width="80px">
        <el-form-item label="姓名" prop="name">
          <el-input v-model="form.name" placeholder="请输入姓名" />
        </el-form-item>
        <el-form-item label="用户名" prop="username">
          <el-input v-model="form.username" :disabled="Boolean(editingId)" placeholder="请输入登录用户名" />
        </el-form-item>
        <el-form-item v-if="!editingId" label="初始密码" prop="password">
          <el-input v-model="form.password" type="password" show-password placeholder="至少 6 位" />
        </el-form-item>
        <el-form-item label="角色" prop="role">
          <el-select v-model="form.role" style="width: 100%">
            <el-option v-for="r in roles" :key="r.value" :label="r.label" :value="r.value" />
          </el-select>
        </el-form-item>
        <el-form-item v-if="form.role === 'staff'" label="部门" prop="department">
          <el-select v-model="form.department" placeholder="请选择所属部门" style="width: 100%">
            <el-option v-for="item in departments" :key="item" :label="item" :value="item" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="saveUser">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { api } from '@/api'
import { departments } from '@/constants/catalog'

const roles = [
  { label: '超级管理员', value: 'admin' },
  { label: '部门人员', value: 'staff' },
  { label: '群众用户', value: 'user' }
]
const roleLabels = { admin: '超级管理员', staff: '部门人员', user: '群众用户' }

const keyword = ref('')
const roleFilter = ref('')
const dialogVisible = ref(false)
const editingId = ref(null)

const list = ref([])
async function loadUsers() {
  try {
    const real = await api.users()
    list.value = real.map((u) => ({
      id: u.id,
      name: u.name,
      username: u.username,
      roleCode: u.role,
      role: roleLabels[u.role] || u.role,
      department: u.department || '-',
      status: u.active ? '启用' : '停用',
      active: Boolean(u.active),
      createdAt: u.created_at || '-'
    }))
  } catch (e) {
    list.value = []
    ElMessage.error('加载用户列表失败，请确认已登录管理员账号')
  }
}
onMounted(loadUsers)

const form = reactive({
  name: '',
  username: '',
  password: '',
  role: 'user',
  department: ''
})

const formRef = ref(null)
const rules = {
  name: [{ required: true, message: '请输入姓名', trigger: 'blur' }],
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, min: 6, message: '密码至少 6 位', trigger: 'blur' }],
  role: [{ required: true, message: '请选择角色', trigger: 'change' }],
  department: [{ required: true, message: '请选择所属部门', trigger: 'change' }]
}

const filteredUsers = computed(() => {
  return list.value.filter((u) => {
    const matchKeyword =
      !keyword.value || u.name.includes(keyword.value) || u.username.includes(keyword.value)
    const matchRole = !roleFilter.value || u.role === roleFilter.value
    return matchKeyword && matchRole
  })
})

function openDialog(row) {
  editingId.value = row ? row.id : null
  if (row) {
    Object.assign(form, {
      name: row.name,
      username: row.username,
      password: '',
      role: row.roleCode,
      department: row.department === '-' ? '' : row.department
    })
  } else {
    Object.assign(form, { name: '', username: '', password: '', role: 'user', department: '' })
  }
  dialogVisible.value = true
}

async function saveUser() {
  await formRef.value.validate(async (valid) => {
    if (!valid) return
    try {
      const payload = {
        name: form.name,
        role: form.role,
        department: form.role === 'staff' ? form.department : ''
      }
      if (editingId.value) {
        const target = list.value.find((u) => u.id === editingId.value)
        await api.updateUser(editingId.value, { ...payload, active: target.active })
        ElMessage.success('用户资料已保存')
      } else {
        await api.createUser({ ...payload, username: form.username, password: form.password })
        ElMessage.success('用户已创建')
      }
      dialogVisible.value = false
      await loadUsers()
    } catch (e) {
      ElMessage.error(e.response?.data?.detail || '保存失败')
    }
  })
}

async function toggleStatus(row) {
  const nextActive = !row.active
  try {
    await ElMessageBox.confirm(
      `确认${nextActive ? '启用' : '停用'}账号「${row.username}」？`,
      '账号状态变更',
      { type: nextActive ? 'info' : 'warning', confirmButtonText: '确认', cancelButtonText: '取消' }
    )
    await api.updateUser(row.id, {
      name: row.name,
      role: row.roleCode,
      department: row.department === '-' ? '' : row.department,
      active: nextActive
    })
    ElMessage.success(`已${nextActive ? '启用' : '停用'}「${row.name}」`)
    await loadUsers()
  } catch (e) {
    if (e !== 'cancel' && e !== 'close') ElMessage.error(e.response?.data?.detail || '状态更新失败')
  }
}
</script>

<style scoped lang="scss">
.toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
}
</style>
