<template>
  <div class="user-manage">
    <div class="page-header">
      <h2>用户管理</h2>
      <el-input v-model="keyword" placeholder="搜索用户..." prefix-icon="Search" clearable style="width: 250px;" @keyup.enter="fetchUsers" @clear="fetchUsers" />
    </div>

    <el-table :data="users" v-loading="loading" style="width: 100%">
      <el-table-column prop="id" label="ID" width="60" />
      <el-table-column prop="username" label="用户名" />
      <el-table-column prop="email" label="邮箱" />
      <el-table-column label="角色" width="100">
        <template #default="{ row }">
          <el-tag :type="row.role === 'admin' ? 'danger' : 'info'" size="small">
            {{ row.role === 'admin' ? '管理员' : '学生' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="注册时间" width="180">
        <template #default="{ row }">{{ formatTime(row.created_at) }}</template>
      </el-table-column>
      <el-table-column label="操作" width="180">
        <template #default="{ row }">
          <el-button text type="primary" @click="showEdit(row)">编辑</el-button>
          <el-button text type="danger" @click="handleDelete(row)" :disabled="row.role === 'admin'">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <div class="pagination">
      <el-pagination background layout="prev, pager, next" :total="total" :page-size="10" v-model:current-page="page" @current-change="fetchUsers" />
    </div>

    <el-dialog v-model="editVisible" title="编辑用户" width="400px">
      <el-form :model="editForm" label-width="60px">
        <el-form-item label="用户名">
          <el-input v-model="editForm.username" />
        </el-form-item>
        <el-form-item label="邮箱">
          <el-input v-model="editForm.email" />
        </el-form-item>
        <el-form-item label="角色">
          <el-select v-model="editForm.role">
            <el-option label="学生" value="student" />
            <el-option label="管理员" value="admin" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="editVisible = false">取消</el-button>
        <el-button type="primary" @click="handleUpdate">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { getUsers, updateUser, deleteUser } from '../../api/admin'
import { ElMessage, ElMessageBox } from 'element-plus'

const users = ref([])
const loading = ref(false)
const keyword = ref('')
const page = ref(1)
const total = ref(0)
const editVisible = ref(false)
const editForm = reactive({ id: null, username: '', email: '', role: '' })

function formatTime(iso) {
  return new Date(iso).toLocaleString('zh-CN')
}

async function fetchUsers() {
  loading.value = true
  try {
    const res = await getUsers({ page: page.value, per_page: 10, keyword: keyword.value || undefined })
    users.value = res.users
    total.value = res.total
  } finally {
    loading.value = false
  }
}

function showEdit(row) {
  Object.assign(editForm, { id: row.id, username: row.username, email: row.email, role: row.role })
  editVisible.value = true
}

async function handleUpdate() {
  await updateUser(editForm.id, { username: editForm.username, email: editForm.email, role: editForm.role })
  ElMessage.success('更新成功')
  editVisible.value = false
  fetchUsers()
}

async function handleDelete(row) {
  await ElMessageBox.confirm(`确定删除用户 ${row.username}？`, '提示', { type: 'warning' })
  await deleteUser(row.id)
  ElMessage.success('删除成功')
  fetchUsers()
}

onMounted(fetchUsers)
</script>

<style scoped>
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}
.pagination {
  display: flex;
  justify-content: center;
  margin-top: 20px;
}
</style>
