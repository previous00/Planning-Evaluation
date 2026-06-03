<template>
  <div class="course-list">
    <RecommendSection :isLoggedIn="userStore.isLoggedIn" />

    <div class="filter-bar">
      <el-input v-model="keyword" placeholder="搜索课程..." prefix-icon="Search" clearable style="width: 300px;" @keyup.enter="fetchCourses" @clear="fetchCourses" />
      <el-select v-model="categoryId" placeholder="全部分类" clearable @change="fetchCourses">
        <el-option v-for="c in categories" :key="c.id" :label="c.name" :value="c.id" />
      </el-select>
      <el-select v-model="difficulty" placeholder="难度" clearable @change="fetchCourses">
        <el-option label="入门" value="beginner" />
        <el-option label="中级" value="intermediate" />
        <el-option label="高级" value="advanced" />
      </el-select>
      <el-select v-model="sortBy" @change="fetchCourses">
        <el-option label="最新" value="newest" />
        <el-option label="最热" value="popular" />
      </el-select>
    </div>

    <div class="course-grid" v-loading="loading">
      <div v-for="course in courses" :key="course.id" class="course-card" @click="$router.push(`/course/${course.id}`)">
        <div class="cover">
          <img :src="course.cover_image || 'https://picsum.photos/seed/default/400/225'" :alt="course.title" />
          <span class="difficulty-tag" :class="course.difficulty">{{ difficultyMap[course.difficulty] }}</span>
        </div>
        <div class="info">
          <h3 class="title">{{ course.title }}</h3>
          <div class="meta">
            <span><el-icon><User /></el-icon> {{ course.teacher_name }}</span>
            <span><el-icon><Clock /></el-icon> {{ formatDuration(course.duration) }}</span>
          </div>
          <div class="bottom">
            <span class="price" v-if="course.price > 0">¥{{ course.price }}</span>
            <span class="price free" v-else>免费</span>
            <span class="students">{{ course.student_count }}人学习</span>
          </div>
        </div>
      </div>
    </div>

    <div class="empty" v-if="!loading && courses.length === 0">
      <el-empty description="暂无课程" />
    </div>

    <div class="pagination" v-if="total > 0">
      <el-pagination background layout="prev, pager, next" :total="total" :page-size="perPage" v-model:current-page="page" @current-change="fetchCourses" />
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { getCourses, getCategories } from '../../api/course'
import { useUserStore } from '../../store/user'
import RecommendSection from '../../components/RecommendSection.vue'

const userStore = useUserStore()

const courses = ref([])
const categories = ref([])
const loading = ref(false)
const keyword = ref('')
const categoryId = ref(null)
const difficulty = ref('')
const sortBy = ref('newest')
const page = ref(1)
const perPage = 12
const total = ref(0)

const difficultyMap = { beginner: '入门', intermediate: '中级', advanced: '高级' }

function formatDuration(min) {
  if (min >= 60) return `${Math.floor(min / 60)}小时${min % 60 ? min % 60 + '分' : ''}`
  return `${min}分钟`
}

async function fetchCourses() {
  loading.value = true
  try {
    const res = await getCourses({
      page: page.value,
      per_page: perPage,
      category_id: categoryId.value || undefined,
      difficulty: difficulty.value || undefined,
      keyword: keyword.value || undefined,
      sort_by: sortBy.value
    })
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

onMounted(() => {
  fetchCategories()
  fetchCourses()
})
</script>

<style scoped>
.filter-bar {
  display: flex;
  gap: 12px;
  margin-bottom: 24px;
  flex-wrap: wrap;
}
.course-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 20px;
}
.course-card {
  background: #fff;
  border-radius: 8px;
  overflow: hidden;
  cursor: pointer;
  transition: transform 0.2s, box-shadow 0.2s;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}
.course-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);
}
.cover {
  position: relative;
  aspect-ratio: 16/9;
  overflow: hidden;
}
.cover img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}
.difficulty-tag {
  position: absolute;
  top: 8px;
  right: 8px;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 12px;
  color: #fff;
}
.difficulty-tag.beginner { background: #67c23a; }
.difficulty-tag.intermediate { background: #e6a23c; }
.difficulty-tag.advanced { background: #f56c6c; }
.info {
  padding: 16px;
}
.title {
  font-size: 15px;
  color: #333;
  margin-bottom: 8px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.meta {
  display: flex;
  gap: 16px;
  font-size: 13px;
  color: #999;
  margin-bottom: 12px;
}
.meta span {
  display: flex;
  align-items: center;
  gap: 4px;
}
.bottom {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.price {
  font-size: 18px;
  font-weight: bold;
  color: #f56c6c;
}
.price.free {
  color: #67c23a;
}
.students {
  font-size: 12px;
  color: #999;
}
.pagination {
  display: flex;
  justify-content: center;
  margin-top: 32px;
}
</style>
