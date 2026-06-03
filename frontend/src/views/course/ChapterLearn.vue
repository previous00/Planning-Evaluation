<template>
  <div class="chapter-learn" v-loading="loading">
    <template v-if="chapter && course">
      <!-- Header -->
      <div class="learn-header">
        <div class="breadcrumb">
          <el-breadcrumb separator="/">
            <el-breadcrumb-item :to="{ path: '/' }">课程中心</el-breadcrumb-item>
            <el-breadcrumb-item :to="{ path: `/course/${course.id}` }">{{ course.title }}</el-breadcrumb-item>
            <el-breadcrumb-item>{{ chapter.title }}</el-breadcrumb-item>
          </el-breadcrumb>
        </div>
        <div class="timer-bar">
          <span class="learning-indicator">
            <span class="pulse-dot"></span>
            正在学习中
          </span>
          <span class="timer">
            <el-icon><Clock /></el-icon>
            本次学习：{{ formatSeconds(elapsedSeconds) }}
          </span>
        </div>
      </div>

      <!-- Main Content -->
      <div class="learn-body">
        <div class="content-area">
          <div class="chapter-title">
            <span class="chapter-num">第{{ chapter.order_num }}章</span>
            <h1>{{ chapter.title }}</h1>
          </div>
          <div class="chapter-content">
            <div class="content-text">
              <p>{{ chapter.description }}</p>
              <div class="simulated-content">
                <el-icon :size="48" color="#c0c4cc"><Reading /></el-icon>
                <p>课程内容学习区域</p>
                <p class="hint">请认真学习本章内容，系统正在自动记录学习时长</p>
              </div>
            </div>
          </div>
        </div>

        <!-- Chapter Navigation Sidebar -->
        <div class="chapter-sidebar">
          <h3>章节目录</h3>
          <div class="chapter-list">
            <div
              v-for="ch in chapters"
              :key="ch.id"
              class="chapter-item"
              :class="{ active: ch.id === chapter.id, locked: !canAccess(ch) }"
              @click="navigateChapter(ch)"
            >
              <span class="ch-num">{{ ch.order_num }}</span>
              <span class="ch-title">{{ ch.title }}</span>
              <el-icon v-if="!canAccess(ch)" class="lock-icon"><Lock /></el-icon>
              <el-tag v-if="ch.is_free" size="small" type="success">免费</el-tag>
            </div>
          </div>
        </div>
      </div>

      <!-- Bottom Navigation -->
      <div class="learn-footer">
        <el-button :disabled="!prevChapter" @click="navigateChapter(prevChapter)">
          ← 上一章
        </el-button>
        <el-button @click="handleLeave">返回课程</el-button>
        <el-button :disabled="!nextChapter || !canAccess(nextChapter)" type="primary" @click="navigateChapter(nextChapter)">
          下一章 →
        </el-button>
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import { useRoute, useRouter, onBeforeRouteLeave } from 'vue-router'
import { getChapter, getChapters } from '../../api/chapter'
import { getCourse } from '../../api/course'
import { recordLearning, checkEnrollment } from '../../api/learning'
import { useUserStore } from '../../store/user'
import { ElMessage } from 'element-plus'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()

const course = ref(null)
const chapter = ref(null)
const chapters = ref([])
const loading = ref(true)
const enrolled = ref(false)

const elapsedSeconds = ref(0)
let startTime = null
let timerInterval = null
let recordSent = false

const prevChapter = computed(() => {
  if (!chapter.value) return null
  const idx = chapters.value.findIndex(c => c.id === chapter.value.id)
  return idx > 0 ? chapters.value[idx - 1] : null
})

const nextChapter = computed(() => {
  if (!chapter.value) return null
  const idx = chapters.value.findIndex(c => c.id === chapter.value.id)
  return idx < chapters.value.length - 1 ? chapters.value[idx + 1] : null
})

function canAccess(ch) {
  if (!ch) return false
  if (ch.is_free) return true
  if (course.value && course.value.price <= 0) return true
  return enrolled.value
}

function formatSeconds(sec) {
  if (!sec || sec <= 0) return '00:00'
  const h = Math.floor(sec / 3600)
  const m = Math.floor((sec % 3600) / 60)
  const s = sec % 60
  const mm = String(m).padStart(2, '0')
  const ss = String(s).padStart(2, '0')
  if (h > 0) return `${h}:${mm}:${ss}`
  return `${mm}:${ss}`
}

function startTimer() {
  startTime = Date.now()
  elapsedSeconds.value = 0
  recordSent = false
  timerInterval = setInterval(() => {
    elapsedSeconds.value = Math.floor((Date.now() - startTime) / 1000)
  }, 1000)
}

function stopTimer() {
  if (timerInterval) {
    clearInterval(timerInterval)
    timerInterval = null
  }
  return Math.floor((Date.now() - startTime) / 1000)
}

async function sendLearningRecord() {
  if (recordSent) return
  const duration = stopTimer()
  if (duration < 5) return
  recordSent = true

  try {
    await recordLearning({
      course_id: parseInt(route.params.id),
      chapter_id: parseInt(route.params.chapterId),
      action: 'progress',
      progress: 0,
      duration: duration
    })
  } catch (e) {
    // silent fail
  }
}

function handleBeforeUnload() {
  if (recordSent) return
  const duration = Math.floor((Date.now() - startTime) / 1000)
  if (duration < 5) return
  const data = JSON.stringify({
    course_id: parseInt(route.params.id),
    chapter_id: parseInt(route.params.chapterId),
    action: 'progress',
    progress: 0,
    duration: duration
  })
  const token = localStorage.getItem('access_token')
  navigator.sendBeacon('/api/learning/record-beacon', new Blob([JSON.stringify({
    data: data,
    token: token
  })], { type: 'application/json' }))
}

function handleLeave() {
  router.push(`/course/${route.params.id}`)
}

async function navigateChapter(ch) {
  if (!ch || !canAccess(ch)) return
  await sendLearningRecord()
  router.push(`/course/${route.params.id}/chapter/${ch.id}`)
  await loadChapter(ch.id)
  startTimer()
}

async function loadChapter(chapterId) {
  try {
    const res = await getChapter(chapterId)
    chapter.value = res.chapter
  } catch (e) {
    ElMessage.error('加载章节失败')
  }
}

onBeforeRouteLeave(async (to, from, next) => {
  await sendLearningRecord()
  next()
})

onMounted(async () => {
  try {
    const courseId = route.params.id
    const chapterId = route.params.chapterId

    const [courseRes, chaptersRes, chapterRes] = await Promise.all([
      getCourse(courseId),
      getChapters(courseId),
      getChapter(chapterId)
    ])

    course.value = courseRes.course
    chapters.value = chaptersRes.chapters
    chapter.value = chapterRes.chapter

    if (userStore.isLoggedIn && course.value.price > 0) {
      const enrollRes = await checkEnrollment(courseId)
      enrolled.value = enrollRes.enrolled
    } else {
      enrolled.value = true
    }

    if (!canAccess(chapter.value)) {
      ElMessage.warning('此章节需要购买课程后解锁')
      router.push(`/course/${courseId}`)
      return
    }

    startTimer()
    window.addEventListener('beforeunload', handleBeforeUnload)
  } catch (e) {
    ElMessage.error('加载失败')
  } finally {
    loading.value = false
  }
})

onBeforeUnmount(() => {
  window.removeEventListener('beforeunload', handleBeforeUnload)
  if (timerInterval) {
    clearInterval(timerInterval)
  }
})
</script>

<style scoped>
.chapter-learn {
  max-width: 1200px;
}
.learn-header {
  background: #fff;
  padding: 16px 24px;
  border-radius: 8px;
  margin-bottom: 20px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.timer-bar {
  display: flex;
  align-items: center;
  gap: 20px;
}
.learning-indicator {
  display: flex;
  align-items: center;
  gap: 6px;
  color: #67c23a;
  font-size: 14px;
}
.pulse-dot {
  width: 8px;
  height: 8px;
  background: #67c23a;
  border-radius: 50%;
  animation: pulse 1.5s infinite;
}
@keyframes pulse {
  0%, 100% { opacity: 1; transform: scale(1); }
  50% { opacity: 0.5; transform: scale(1.3); }
}
.timer {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 18px;
  font-weight: bold;
  color: #e6a23c;
}
.learn-body {
  display: flex;
  gap: 20px;
}
.content-area {
  flex: 1;
  background: #fff;
  border-radius: 8px;
  padding: 32px;
  min-height: 500px;
}
.chapter-title {
  margin-bottom: 24px;
  padding-bottom: 16px;
  border-bottom: 1px solid #f0f0f0;
}
.chapter-num {
  font-size: 13px;
  color: #909399;
  display: block;
  margin-bottom: 4px;
}
.chapter-title h1 {
  font-size: 22px;
  color: #333;
  margin: 0;
}
.content-text p {
  font-size: 15px;
  line-height: 1.8;
  color: #555;
  margin-bottom: 24px;
}
.simulated-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
  background: #f9fafc;
  border-radius: 8px;
  border: 2px dashed #e4e7ed;
}
.simulated-content p {
  margin: 12px 0 0;
  color: #909399;
  font-size: 14px;
}
.simulated-content .hint {
  font-size: 12px;
  color: #c0c4cc;
}
.chapter-sidebar {
  width: 280px;
  flex-shrink: 0;
  background: #fff;
  border-radius: 8px;
  padding: 20px;
  align-self: flex-start;
  position: sticky;
  top: 80px;
  max-height: calc(100vh - 160px);
  overflow-y: auto;
}
.chapter-sidebar h3 {
  font-size: 16px;
  color: #333;
  margin: 0 0 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid #f0f0f0;
}
.chapter-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 12px;
  border-radius: 6px;
  cursor: pointer;
  transition: background 0.2s;
  margin-bottom: 4px;
}
.chapter-item:hover {
  background: #f5f7fa;
}
.chapter-item.active {
  background: #ecf5ff;
  color: #409eff;
  font-weight: 500;
}
.chapter-item.locked {
  color: #c0c4cc;
  cursor: not-allowed;
}
.chapter-item.locked:hover {
  background: transparent;
}
.ch-num {
  width: 20px;
  height: 20px;
  background: #f0f0f0;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 11px;
  flex-shrink: 0;
}
.chapter-item.active .ch-num {
  background: #409eff;
  color: #fff;
}
.ch-title {
  flex: 1;
  font-size: 13px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.lock-icon {
  color: #c0c4cc;
  font-size: 14px;
}
.learn-footer {
  display: flex;
  justify-content: center;
  gap: 16px;
  margin-top: 24px;
  padding: 20px;
  background: #fff;
  border-radius: 8px;
}
</style>
