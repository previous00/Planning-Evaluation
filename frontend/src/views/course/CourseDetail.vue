<template>
  <div class="course-detail" v-loading="loading">
    <template v-if="course">
      <div class="detail-header">
        <div class="cover">
          <img :src="course.cover_image || 'https://picsum.photos/seed/default/400/225'" :alt="course.title" />
        </div>
        <div class="header-info">
          <h1>{{ course.title }}</h1>
          <div class="tags">
            <el-tag v-if="course.category_name">{{ course.category_name }}</el-tag>
            <el-tag :type="difficultyType[course.difficulty]">{{ difficultyMap[course.difficulty] }}</el-tag>
            <el-tag v-if="course.price <= 0" type="success">免费</el-tag>
          </div>
          <div class="meta-info">
            <p><el-icon><User /></el-icon> 讲师：{{ course.teacher_name }}</p>
            <p><el-icon><Clock /></el-icon> 时长：{{ formatDuration(course.duration) }}</p>
            <p><el-icon><View /></el-icon> 浏览：{{ course.view_count }}次</p>
            <p><el-icon><UserFilled /></el-icon> {{ course.student_count }}人学习</p>
          </div>
          <div class="price-area">
            <span class="price" v-if="course.price > 0">¥{{ course.price }}</span>
            <span class="price free" v-else>免费</span>
          </div>

          <!-- 操作按钮区 -->
          <div class="actions">
            <!-- 未登录 -->
            <template v-if="!userStore.isLoggedIn">
              <el-button type="primary" size="large" @click="$router.push('/login')">登录后学习</el-button>
            </template>

            <!-- 已登录 + 已报名/免费课程 -->
            <template v-else-if="enrolled">
              <el-button v-if="!isLearning" type="primary" size="large" :loading="learningLoading" @click="startLearning">
                {{ userProgress ? '继续学习' : '开始学习' }}
              </el-button>
              <el-button v-else type="danger" size="large" @click="stopLearning">
                结束本次学习
              </el-button>
              <span v-if="isLearning" class="timer">
                <el-icon><Clock /></el-icon> 本次已学习：{{ currentSessionTime }}
              </span>
              <span v-if="userProgress && !isLearning" class="progress-text">
                已学习 {{ userProgress.progress }}%
              </span>
            </template>

            <!-- 已登录 + 未购买付费课程 -->
            <template v-else>
              <el-button type="warning" size="large" @click="handleEnroll">
                购买课程 ¥{{ course.price }}
              </el-button>
              <el-button size="large" @click="trialLearn" :disabled="trialUsed">
                {{ trialUsed ? '试学已结束' : '免费试学' }}
              </el-button>
            </template>
          </div>

          <el-alert v-if="!enrolled && userStore.isLoggedIn && course.price > 0" type="info" :closable="false" style="margin-top: 12px;">
            该课程为付费课程，购买后可完整学习。未购买只能试学前10%的内容。
          </el-alert>
        </div>
      </div>

      <el-card class="detail-body">
        <template #header><h3>课程介绍</h3></template>
        <div class="description">{{ course.description }}</div>
      </el-card>

      <!-- 课程章节 -->
      <el-card class="detail-body">
        <template #header>
          <div class="chapter-header">
            <h3>课程章节</h3>
            <span class="chapter-count">共 {{ chapters.length }} 章</span>
          </div>
        </template>
        <div class="chapter-list" v-if="chapters.length > 0">
          <div
            v-for="ch in chapters"
            :key="ch.id"
            class="chapter-row"
            :class="{ locked: !canAccessChapter(ch), clickable: canAccessChapter(ch) && userStore.isLoggedIn }"
            @click="handleChapterClick(ch)"
          >
            <div class="chapter-left">
              <span class="chapter-order">{{ ch.order_num }}</span>
              <div class="chapter-info">
                <span class="chapter-title">{{ ch.title }}</span>
                <span class="chapter-duration">{{ ch.duration }}分钟</span>
              </div>
            </div>
            <div class="chapter-right">
              <el-tag v-if="ch.is_free" size="small" type="success">免费</el-tag>
              <el-icon v-else-if="!canAccessChapter(ch)" class="lock-icon"><Lock /></el-icon>
              <el-icon v-else class="play-icon"><VideoPlay /></el-icon>
            </div>
          </div>
        </div>
        <el-empty v-else description="暂无章节" :image-size="60" />
      </el-card>

      <el-card v-if="userProgress" class="detail-body">
        <template #header><h3>学习进度</h3></template>
        <el-progress :percentage="userProgress.progress" :stroke-width="20" :text-inside="true" />
        <div class="progress-detail">
          <p>累计学习时长：{{ formatSeconds(userProgress.total_duration) }}</p>
          <p>开始时间：{{ formatTime(userProgress.started_at) }}</p>
          <p>最近学习：{{ formatTime(userProgress.last_learn_at) }}</p>
          <p v-if="userProgress.status === 'completed'" style="color:#67c23a;font-weight:bold;">已完成学习！</p>
        </div>
      </el-card>
    </template>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { getCourse } from '../../api/course'
import { getCourseProgress, recordLearning, checkEnrollment, enrollCourse } from '../../api/learning'
import { getChapters } from '../../api/chapter'
import { useUserStore } from '../../store/user'
import { ElMessage, ElMessageBox } from 'element-plus'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()

const course = ref(null)
const userProgress = ref(null)
const loading = ref(true)
const learningLoading = ref(false)
const enrolled = ref(false)
const trialUsed = ref(false)
const chapters = ref([])

// 学习计时相关
const isLearning = ref(false)
const learnStartTime = ref(null)
const elapsedSeconds = ref(0)
let timerInterval = null

const difficultyMap = { beginner: '入门', intermediate: '中级', advanced: '高级' }
const difficultyType = { beginner: 'success', intermediate: 'warning', advanced: 'danger' }

const currentSessionTime = computed(() => formatSeconds(elapsedSeconds.value))

function formatDuration(min) {
  if (min >= 60) return `${Math.floor(min / 60)}小时${min % 60 ? min % 60 + '分' : ''}`
  return `${min}分钟`
}

function formatSeconds(sec) {
  if (!sec || sec <= 0) return '0秒'
  const h = Math.floor(sec / 3600)
  const m = Math.floor((sec % 3600) / 60)
  const s = sec % 60
  if (h > 0) return `${h}小时${m}分${s}秒`
  if (m > 0) return `${m}分${s}秒`
  return `${s}秒`
}

function formatTime(iso) {
  if (!iso) return ''
  return new Date(iso).toLocaleString('zh-CN')
}

function startTimer() {
  learnStartTime.value = Date.now()
  elapsedSeconds.value = 0
  timerInterval = setInterval(() => {
    elapsedSeconds.value = Math.floor((Date.now() - learnStartTime.value) / 1000)
  }, 1000)
}

function stopTimer() {
  if (timerInterval) {
    clearInterval(timerInterval)
    timerInterval = null
  }
  const duration = Math.floor((Date.now() - learnStartTime.value) / 1000)
  return duration
}

async function startLearning() {
  isLearning.value = true
  startTimer()
  ElMessage.success('学习计时开始，点击"结束本次学习"保存进度')
}

async function stopLearning() {
  const duration = stopTimer()
  isLearning.value = false
  learningLoading.value = true

  try {
    const currentProgress = userProgress.value ? userProgress.value.progress : 0
    // 根据学习时长计算进度增长：每分钟增加约课程总时长的对应比例
    const courseTotalSeconds = course.value.duration * 60
    const progressIncrement = Math.round((duration / courseTotalSeconds) * 100)
    const newProgress = Math.min(currentProgress + Math.max(progressIncrement, 1), 100)

    const res = await recordLearning({
      course_id: course.value.id,
      action: userProgress.value ? 'progress' : 'start',
      progress: newProgress,
      duration: duration
    })

    userProgress.value = res.progress
    ElMessage.success(
      `本次学习 ${formatSeconds(duration)}，进度更新至 ${newProgress}%` +
      (newProgress >= 100 ? ' 恭喜完成课程！' : '')
    )
  } catch (e) {
    console.error('保存学习记录失败:', e)
  } finally {
    learningLoading.value = false
  }
}

async function trialLearn() {
  isLearning.value = true
  startTimer()
  trialUsed.value = true

  // 试学限制：30秒后自动结束
  setTimeout(async () => {
    if (!isLearning.value) return
    const duration = stopTimer()
    isLearning.value = false

    try {
      const currentProgress = userProgress.value ? userProgress.value.progress : 0
      const newProgress = Math.min(currentProgress + 5, 10) // 试学最多到10%

      await recordLearning({
        course_id: course.value.id,
        action: 'progress',
        progress: newProgress,
        duration: duration
      })

      const pRes = await getCourseProgress(route.params.id)
      userProgress.value = pRes.progress
    } catch (e) {
      // 忽略，试学可能被限制
    }

    ElMessageBox.alert(
      '试学时间已结束，购买课程后可完整学习全部内容。',
      '试学结束',
      { confirmButtonText: '我知道了', type: 'info' }
    )
  }, 30000)

  ElMessage.info('试学模式：可体验30秒，购买后解锁完整课程')
}

function canAccessChapter(ch) {
  if (ch.is_free) return true
  if (course.value && course.value.price <= 0) return true
  return enrolled.value
}

function handleChapterClick(ch) {
  if (!userStore.isLoggedIn) {
    ElMessage.info('请先登录')
    router.push('/login')
    return
  }
  if (!canAccessChapter(ch)) {
    ElMessage.warning('请购买课程后解锁此章节')
    return
  }
  router.push(`/course/${course.value.id}/chapter/${ch.id}`)
}

async function handleEnroll() {
  try {
    await ElMessageBox.confirm(
      `确认购买课程「${course.value.title}」？价格：¥${course.value.price}`,
      '购买课程',
      { confirmButtonText: '确认购买', cancelButtonText: '取消', type: 'info' }
    )
    await enrollCourse({ course_id: course.value.id })
    enrolled.value = true
    ElMessage.success('购买成功！现在可以开始学习了')
  } catch (e) {
    if (e !== 'cancel') console.error('购买失败:', e)
  }
}

async function loadProgress() {
  if (!userStore.isLoggedIn) return
  try {
    const res = await getCourseProgress(route.params.id)
    userProgress.value = res.progress
  } catch (e) {
    console.error('获取进度失败:', e)
  }
}

async function loadEnrollment() {
  if (!userStore.isLoggedIn) return
  try {
    const res = await checkEnrollment(route.params.id)
    enrolled.value = res.enrolled
  } catch (e) {
    console.error('检查报名状态失败:', e)
  }
}

onMounted(async () => {
  try {
    const res = await getCourse(route.params.id)
    course.value = res.course

    // Load chapters
    try {
      const chRes = await getChapters(route.params.id)
      chapters.value = chRes.chapters
    } catch (e) { /* no chapters */ }

    if (userStore.isLoggedIn) {
      // 记录浏览
      try {
        await recordLearning({ course_id: course.value.id, action: 'view', progress: 0, duration: 0 })
      } catch (e) { /* ignore view record errors */ }

      await Promise.all([loadProgress(), loadEnrollment()])
    }
  } catch (e) {
    ElMessage.error('加载课程信息失败')
  } finally {
    loading.value = false
  }
})

onBeforeUnmount(() => {
  if (timerInterval) {
    clearInterval(timerInterval)
  }
})
</script>

<style scoped>
.detail-header {
  display: flex;
  gap: 32px;
  background: #fff;
  padding: 24px;
  border-radius: 8px;
  margin-bottom: 20px;
}
.cover {
  width: 400px;
  flex-shrink: 0;
  border-radius: 8px;
  overflow: hidden;
}
.cover img {
  width: 100%;
  aspect-ratio: 16/9;
  object-fit: cover;
}
.header-info {
  flex: 1;
}
.header-info h1 {
  font-size: 24px;
  margin-bottom: 12px;
}
.tags {
  display: flex;
  gap: 8px;
  margin-bottom: 16px;
}
.meta-info {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
  color: #666;
  margin-bottom: 16px;
}
.meta-info p {
  display: flex;
  align-items: center;
  gap: 6px;
}
.price-area {
  margin-bottom: 16px;
}
.price {
  font-size: 28px;
  font-weight: bold;
  color: #f56c6c;
}
.price.free {
  color: #67c23a;
}
.actions {
  display: flex;
  align-items: center;
  gap: 16px;
  flex-wrap: wrap;
}
.timer {
  display: flex;
  align-items: center;
  gap: 4px;
  color: #e6a23c;
  font-size: 16px;
  font-weight: bold;
}
.progress-text {
  color: #409eff;
  font-size: 14px;
}
.detail-body {
  margin-bottom: 20px;
}
.description {
  line-height: 1.8;
  color: #555;
  white-space: pre-wrap;
}
.progress-detail {
  margin-top: 16px;
  display: flex;
  flex-direction: column;
  gap: 6px;
  color: #666;
  font-size: 14px;
}
.chapter-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.chapter-header h3 {
  margin: 0;
}
.chapter-count {
  font-size: 13px;
  color: #909399;
}
.chapter-list {
  display: flex;
  flex-direction: column;
}
.chapter-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 14px 16px;
  border-radius: 6px;
  transition: background 0.2s;
}
.chapter-row.clickable {
  cursor: pointer;
}
.chapter-row.clickable:hover {
  background: #f5f7fa;
}
.chapter-row.locked {
  opacity: 0.6;
  cursor: not-allowed;
}
.chapter-row + .chapter-row {
  border-top: 1px solid #f5f5f5;
}
.chapter-left {
  display: flex;
  align-items: center;
  gap: 14px;
}
.chapter-order {
  width: 28px;
  height: 28px;
  background: #f0f2f5;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 13px;
  color: #666;
  flex-shrink: 0;
}
.chapter-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.chapter-title {
  font-size: 14px;
  color: #333;
}
.chapter-duration {
  font-size: 12px;
  color: #999;
}
.chapter-right {
  display: flex;
  align-items: center;
  gap: 8px;
}
.lock-icon {
  color: #c0c4cc;
  font-size: 16px;
}
.play-icon {
  color: #409eff;
  font-size: 18px;
}
</style>
