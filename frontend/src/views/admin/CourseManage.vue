<template>
  <div class="course-manage">
    <div class="page-header">
      <h2>课程管理</h2>
      <el-button type="primary" @click="showCreate">新增课程</el-button>
    </div>

    <el-table :data="courses" v-loading="loading" style="width: 100%">
      <el-table-column prop="id" label="ID" width="60" />
      <el-table-column prop="title" label="课程标题" min-width="200" />
      <el-table-column prop="category_name" label="分类" width="100" />
      <el-table-column prop="teacher_name" label="讲师" width="100" />
      <el-table-column label="难度" width="80">
        <template #default="{ row }">
          <el-tag :type="difficultyType[row.difficulty]" size="small">{{ difficultyMap[row.difficulty] }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="price" label="价格" width="80">
        <template #default="{ row }">{{ row.price > 0 ? `¥${row.price}` : '免费' }}</template>
      </el-table-column>
      <el-table-column label="状态" width="80">
        <template #default="{ row }">
          <el-tag :type="row.status === 'published' ? 'success' : 'info'" size="small">
            {{ statusMap[row.status] }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="150">
        <template #default="{ row }">
          <el-button text type="primary" @click="showEdit(row)">编辑</el-button>
          <el-button text type="danger" @click="handleDelete(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <div class="pagination">
      <el-pagination background layout="prev, pager, next" :total="total" :page-size="10" v-model:current-page="page" @current-change="fetchCourses" />
    </div>

    <el-dialog v-model="dialogVisible" :title="isEdit ? '编辑课程' : '新增课程'" width="600px">
      <el-form :model="form" label-width="80px">
        <el-form-item label="标题" required>
          <el-input v-model="form.title" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="form.description" type="textarea" :rows="3" />
        </el-form-item>
        <el-form-item label="分类">
          <el-select v-model="form.category_id" placeholder="选择分类" clearable>
            <el-option v-for="c in categories" :key="c.id" :label="c.name" :value="c.id" />
          </el-select>
        </el-form-item>
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="讲师">
              <el-input v-model="form.teacher_name" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="时长(分)">
              <el-input-number v-model="form.duration" :min="0" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="难度">
              <el-select v-model="form.difficulty">
                <el-option label="入门" value="beginner" />
                <el-option label="中级" value="intermediate" />
                <el-option label="高级" value="advanced" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="价格">
              <el-input-number v-model="form.price" :min="0" :precision="2" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="封面URL">
          <el-input v-model="form.cover_image" placeholder="课程封面图片URL" />
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="form.status">
            <el-option label="已发布" value="published" />
            <el-option label="草稿" value="draft" />
            <el-option label="已归档" value="archived" />
          </el-select>
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
import { getCourses, createCourse, updateCourse, deleteCourse, getCategories } from '../../api/course'
import { ElMessage, ElMessageBox } from 'element-plus'

const courses = ref([])
const categories = ref([])
const loading = ref(false)
const page = ref(1)
const total = ref(0)
const dialogVisible = ref(false)
const isEdit = ref(false)

const difficultyMap = { beginner: '入门', intermediate: '中级', advanced: '高级' }
const difficultyType = { beginner: 'success', intermediate: 'warning', advanced: 'danger' }
const statusMap = { published: '已发布', draft: '草稿', archived: '已归档' }

const defaultForm = {
  title: '', description: '', category_id: null, teacher_name: '',
  duration: 0, difficulty: 'beginner', price: 0, cover_image: '', status: 'published'
}
const form = reactive({ ...defaultForm, id: null })

async function fetchCourses() {
  loading.value = true
  try {
    const res = await getCourses({ page: page.value, per_page: 10 })
    courses.value = res.courses
    total.value = res.total
  } finally {
    loading.value = false
  }
}

async function fetchCategories() {
  const res = await getCategories()
  categories.value = res.categories
}

function showCreate() {
  Object.assign(form, defaultForm, { id: null })
  isEdit.value = false
  dialogVisible.value = true
}

function showEdit(row) {
  Object.assign(form, row)
  isEdit.value = true
  dialogVisible.value = true
}

async function handleSave() {
  if (!form.title) {
    ElMessage.warning('请输入课程标题')
    return
  }
  if (isEdit.value) {
    await updateCourse(form.id, form)
    ElMessage.success('更新成功')
  } else {
    await createCourse(form)
    ElMessage.success('创建成功')
  }
  dialogVisible.value = false
  fetchCourses()
}

async function handleDelete(row) {
  await ElMessageBox.confirm(`确定删除课程 "${row.title}"？`, '提示', { type: 'warning' })
  await deleteCourse(row.id)
  ElMessage.success('删除成功')
  fetchCourses()
}

onMounted(() => {
  fetchCategories()
  fetchCourses()
})
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
