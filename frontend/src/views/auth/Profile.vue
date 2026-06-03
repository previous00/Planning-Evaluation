<template>
  <div class="profile-page">
    <el-card>
      <template #header>
        <h3>个人中心</h3>
      </template>
      <el-form ref="formRef" :model="form" :rules="rules" label-width="80px" style="max-width: 500px;">
        <el-form-item label="用户名" prop="username">
          <el-input v-model="form.username" />
        </el-form-item>
        <el-form-item label="邮箱" prop="email">
          <el-input v-model="form.email" />
        </el-form-item>
        <el-form-item label="头像URL">
          <el-input v-model="form.avatar" placeholder="输入头像图片URL" />
        </el-form-item>
        <el-form-item label="新密码">
          <el-input v-model="form.password" type="password" placeholder="留空则不修改" show-password />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="loading" @click="handleUpdate">保存修改</el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useUserStore } from '../../store/user'
import { updateProfile } from '../../api/auth'
import { ElMessage } from 'element-plus'

const userStore = useUserStore()
const formRef = ref(null)
const loading = ref(false)

const form = reactive({
  username: '',
  email: '',
  avatar: '',
  password: ''
})

const rules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  email: [{ required: true, type: 'email', message: '请输入有效邮箱', trigger: 'blur' }]
}

onMounted(() => {
  if (userStore.user) {
    form.username = userStore.user.username
    form.email = userStore.user.email
    form.avatar = userStore.user.avatar || ''
  }
})

async function handleUpdate() {
  await formRef.value.validate()
  loading.value = true
  try {
    const data = { username: form.username, email: form.email, avatar: form.avatar }
    if (form.password) data.password = form.password
    await updateProfile(data)
    await userStore.fetchProfile()
    ElMessage.success('更新成功')
    form.password = ''
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.profile-page {
  max-width: 600px;
}
</style>
