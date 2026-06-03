<template>
  <div class="category-manage">
    <div class="page-header">
      <h2>分类管理</h2>
      <el-button type="primary" @click="showCreate">新增分类</el-button>
    </div>

    <el-table :data="categories" v-loading="loading" style="width: 100%">
      <el-table-column prop="id" label="ID" width="60" />
      <el-table-column prop="name" label="分类名称" />
      <el-table-column prop="description" label="描述" />
      <el-table-column prop="course_count" label="课程数" width="100" />
      <el-table-column label="操作" width="150">
        <template #default="{ row }">
          <el-button text type="primary" @click="showEdit(row)">编辑</el-button>
          <el-button text type="danger" @click="handleDelete(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="dialogVisible" :title="isEdit ? '编辑分类' : '新增分类'" width="400px">
      <el-form :model="form" label-width="80px">
        <el-form-item label="名称" required>
          <el-input v-model="form.name" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="form.description" type="textarea" :rows="3" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSave">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { getCategories } from '../../api/course'
import { createCategory, updateCategory, deleteCategory } from '../../api/admin'
import { ElMessage, ElMessageBox } from 'element-plus'

const categories = ref([])
const loading = ref(false)
const dialogVisible = ref(false)
const isEdit = ref(false)
const form = reactive({ id: null, name: '', description: '' })

async function fetchCategories() {
  loading.value = true
  try {
    const res = await getCategories()
    categories.value = res.categories
  } finally {
    loading.value = false
  }
}

function showCreate() {
  Object.assign(form, { id: null, name: '', description: '' })
  isEdit.value = false
  dialogVisible.value = true
}

function showEdit(row) {
  Object.assign(form, { id: row.id, name: row.name, description: row.description })
  isEdit.value = true
  dialogVisible.value = true
}

async function handleSave() {
  if (!form.name) {
    ElMessage.warning('请输入分类名称')
    return
  }
  if (isEdit.value) {
    await updateCategory(form.id, { name: form.name, description: form.description })
    ElMessage.success('更新成功')
  } else {
    await createCategory({ name: form.name, description: form.description })
    ElMessage.success('创建成功')
  }
  dialogVisible.value = false
  fetchCategories()
}

async function handleDelete(row) {
  await ElMessageBox.confirm(`确定删除分类 "${row.name}"？关联课程将变为未分类。`, '提示', { type: 'warning' })
  await deleteCategory(row.id)
  ElMessage.success('删除成功')
  fetchCategories()
}

onMounted(fetchCategories)
</script>

<style scoped>
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}
</style>
