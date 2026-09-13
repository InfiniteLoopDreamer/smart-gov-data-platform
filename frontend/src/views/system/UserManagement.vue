<template>
  <div class="page">
    <div class="panel-card">
      <!-- 顶部操作 -->
      <div class="toolbar">
        <div>
          <el-input v-model="keyword" placeholder="搜索姓名 / 用户名" clearable style="width: 220px">
            <template #prefix><el-icon><Search /></el-icon></template>
          </el-input>
          <el-select v-model="roleFilter" placeholder="角色" clearable style="width: 150px; margin-left: 12px">
            <el-option v-for="r in roles" :key="r" :label="r" :value="r" />
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
            <el-tag :type="row.role === '管理员' ? 'danger' : 'primary'" effect="light" round>
              {{ row.role }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="department" label="部门" width="140" />
        <el-table-column prop="lastLogin" label="最后登录" width="170" />
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
          <el-input v-model="form.username" placeholder="请输入登录用户名" />
        </el-form-item>
        <el-form-item label="角色" prop="role">
          <el-select v-model="form.role" style="width: 100%">
            <el-option v-for="r in roles" :key="r" :label="r" :value="r" />
          </el-select>
        </el-form-item>
        <el-form-item label="部门">
          <el-input v-model="form.department" placeholder="请输入所属部门" />
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
import { ElMessage } from 'element-plus'
import { api } from '@/api'

const roles = ['管理员', '普通用户']

const keyword = ref('')
const roleFilter = ref('')
const dialogVisible = ref(false)
const editingId = ref(null)

const list = ref([])
onMounted(async () => {
  try {
    const real = await api.users()
    list.value = real.map((u) => ({
      id: u.id,
      name: u.name,
      username: u.username,
      role: u.role === 'admin' ? '管理员' : '普通用户',
      department: u.department || '-',
      status: '启用',
      lastLogin: u.created_at || '-'
    }))
  } catch (e) {
    list.value = []
    ElMessage.error('加载用户列表失败，请确认已登录管理员账号')
  }
})

const form = reactive({
  name: '',
  username: '',
  role: '普通用户',
  department: ''
})

const formRef = ref(null)
const rules = {
  name: [{ required: true, message: '请输入姓名', trigger: 'blur' }],
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  role: [{ required: true, message: '请选择角色', trigger: 'change' }]
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
      role: row.role,
      department: row.department
    })
  } else {
    Object.assign(form, { name: '', username: '', role: '普通用户', department: '' })
  }
  dialogVisible.value = true
}

function saveUser() {
  formRef.value.validate((valid) => {
    if (!valid) return
    if (editingId.value) {
      const target = list.value.find((u) => u.id === editingId.value)
      Object.assign(target, { ...form })
      ElMessage.success('已更新用户')
    } else {
      list.value.push({ id: Date.now(), ...form, status: '启用', lastLogin: '-' })
      ElMessage.success('已新增用户')
    }
    dialogVisible.value = false
  })
}

function toggleStatus(row) {
  row.status = row.status === '启用' ? '停用' : '启用'
  ElMessage.success(`已${row.status}「${row.name}」`)
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
