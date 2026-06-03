<template>
  <div class="recommend-page">
    <div class="page-header">
      <h1>智能推荐</h1>
      <p>基于你的学习行为，为你精选以下课程</p>
    </div>

    <div class="content-wrapper">
      <!-- User Profile Panel -->
      <div class="profile-panel">
        <div class="panel-card">
          <h3>我的学习画像</h3>
          <div v-if="profile" class="profile-content">
            <div class="profile-item">
              <label>偏好分类</label>
              <div class="tags">
                <el-tag v-for="(weight, name) in profile.category_names" :key="name" size="small" :type="getTagType(weight)">
                  {{ name }}
                </el-tag>
              </div>
            </div>
            <div class="profile-item">
              <label>难度偏好</label>
              <div class="difficulty-bars">
                <div v-for="(weight, diff) in profile.difficulty_preferences" :key="diff" class="diff-bar">
                  <span class="diff-label">{{ diffMap[diff] || diff }}</span>
                  <el-progress :percentage="Math.round(weight * 100)" :stroke-width="12" :show-text="false" :color="diffColor[diff]" />
                </div>
              </div>
            </div>
            <div class="profile-item">
              <label>学习节奏</label>
              <span class="stat-value">{{ profile.avg_learning_pace }} 分钟/天</span>
            </div>
            <div class="profile-item">
              <label>已学课程</label>
              <span class="stat-value">{{ profile.total_courses_learned }} 门</span>
            </div>
            <div class="profile-item">
              <label>偏好时长</label>
              <span class="stat-value">{{ durationMap[profile.preferred_duration] }}</span>
            </div>
            <el-button type="primary" size="small" :loading="refreshing" @click="handleRefresh">
              刷新画像
            </el-button>
          </div>
          <el-skeleton v-else :rows="6" animated />
        </div>
      </div>

      <!-- Recommendations Area -->
      <div class="recommend-area">
        <div class="strategy-tabs">
          <el-radio-group v-model="currentStrategy" @change="fetchRecommendations">
            <el-radio-button value="all">综合推荐</el-radio-button>
            <el-radio-button value="collaborative">协同推荐</el-radio-button>
            <el-radio-button value="content">相似推荐</el-radio-button>
            <el-radio-button value="popularity">热门推荐</el-radio-button>
          </el-radio-group>
        </div>

        <div class="recommend-grid" v-loading="loading">
          <div
            v-for="(item, index) in recommendations"
            :key="item.course.id"
            class="recommend-card"
            @click="handleClick(item, index)"
          >
            <div class="cover">
              <img :src="item.course.cover_image || 'https://picsum.photos/seed/default/400/225'" :alt="item.course.title" />
              <span class="rank-badge">#{{ item.rank }}</span>
              <span class="score-badge">{{ Math.round(item.score * 100) }}%</span>
            </div>
            <div class="info">
              <h3 class="title">{{ item.course.title }}</h3>
              <p class="reason">
                <el-icon><InfoFilled /></el-icon>
                {{ item.reason }}
              </p>
              <div class="meta">
                <span><el-icon><User /></el-icon> {{ item.course.teacher_name }}</span>
                <span class="difficulty" :class="item.course.difficulty">{{ diffMap[item.course.difficulty] }}</span>
              </div>
              <div class="bottom">
                <span class="price" v-if="item.course.price > 0">¥{{ item.course.price }}</span>
                <span class="price free" v-else>免费</span>
                <span class="students">{{ item.course.student_count }}人学习</span>
              </div>
            </div>
          </div>
        </div>

        <div class="empty" v-if="!loading && recommendations.length === 0">
          <el-empty description="暂无推荐，多学习几门课程后将为你生成个性化推荐" />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { getRecommendations, getUserProfile, refreshProfile, trackClick } from '../../api/recommend'

const router = useRouter()
const recommendations = ref([])
const logIds = ref([])
const profile = ref(null)
const loading = ref(false)
const refreshing = ref(false)
const currentStrategy = ref('all')

const diffMap = { beginner: '入门', intermediate: '中级', advanced: '高级' }
const diffColor = { beginner: '#67c23a', intermediate: '#e6a23c', advanced: '#f56c6c' }
const durationMap = { short: '短课程(≤12h)', medium: '中等(12-24h)', long: '长课程(>24h)' }

function getTagType(weight) {
  if (weight >= 0.4) return ''
  if (weight >= 0.2) return 'success'
  return 'info'
}

async function fetchRecommendations() {
  loading.value = true
  try {
    const res = await getRecommendations({ limit: 10, strategy: currentStrategy.value })
    recommendations.value = res.recommendations
    logIds.value = res.log_ids
  } finally {
    loading.value = false
  }
}

async function fetchProfile() {
  try {
    const res = await getUserProfile()
    profile.value = res.profile
  } catch (e) {
    // profile may not exist yet
  }
}

async function handleRefresh() {
  refreshing.value = true
  try {
    await refreshProfile()
    await fetchProfile()
    await fetchRecommendations()
  } finally {
    refreshing.value = false
  }
}

function handleClick(item, index) {
  if (logIds.value[index]) {
    trackClick({ log_id: logIds.value[index], course_id: item.course.id }).catch(() => {})
  }
  router.push(`/course/${item.course.id}`)
}

onMounted(() => {
  fetchProfile()
  fetchRecommendations()
})
</script>

<style scoped>
.recommend-page {
  max-width: 1200px;
}
.page-header {
  margin-bottom: 24px;
}
.page-header h1 {
  font-size: 24px;
  color: #333;
  margin: 0 0 8px;
}
.page-header p {
  color: #909399;
  margin: 0;
}
.content-wrapper {
  display: flex;
  gap: 24px;
}
.profile-panel {
  width: 280px;
  flex-shrink: 0;
}
.panel-card {
  background: #fff;
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.06);
  position: sticky;
  top: 80px;
}
.panel-card h3 {
  font-size: 16px;
  color: #333;
  margin: 0 0 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid #f0f0f0;
}
.profile-item {
  margin-bottom: 16px;
}
.profile-item label {
  display: block;
  font-size: 12px;
  color: #909399;
  margin-bottom: 6px;
}
.tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}
.difficulty-bars {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.diff-bar {
  display: flex;
  align-items: center;
  gap: 8px;
}
.diff-label {
  font-size: 12px;
  color: #666;
  width: 30px;
}
.stat-value {
  font-size: 14px;
  color: #333;
  font-weight: 500;
}
.recommend-area {
  flex: 1;
  min-width: 0;
}
.strategy-tabs {
  margin-bottom: 20px;
}
.recommend-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
  gap: 20px;
}
.recommend-card {
  background: #fff;
  border-radius: 8px;
  overflow: hidden;
  cursor: pointer;
  transition: transform 0.2s, box-shadow 0.2s;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}
.recommend-card:hover {
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
.rank-badge {
  position: absolute;
  top: 8px;
  left: 8px;
  background: rgba(0, 0, 0, 0.7);
  color: #fff;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: bold;
}
.score-badge {
  position: absolute;
  top: 8px;
  right: 8px;
  background: rgba(64, 158, 255, 0.9);
  color: #fff;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 12px;
}
.info {
  padding: 14px;
}
.title {
  font-size: 14px;
  color: #333;
  margin: 0 0 8px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.reason {
  font-size: 12px;
  color: #909399;
  margin: 0 0 10px;
  display: flex;
  align-items: center;
  gap: 4px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.meta {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 12px;
  color: #999;
  margin-bottom: 10px;
}
.meta span {
  display: flex;
  align-items: center;
  gap: 4px;
}
.difficulty {
  padding: 1px 6px;
  border-radius: 3px;
  color: #fff;
  font-size: 11px;
}
.difficulty.beginner { background: #67c23a; }
.difficulty.intermediate { background: #e6a23c; }
.difficulty.advanced { background: #f56c6c; }
.bottom {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.price {
  font-size: 16px;
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

@media (max-width: 768px) {
  .content-wrapper {
    flex-direction: column;
  }
  .profile-panel {
    width: 100%;
  }
  .panel-card {
    position: static;
  }
}
</style>
