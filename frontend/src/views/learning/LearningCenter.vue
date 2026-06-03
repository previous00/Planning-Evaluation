<template>
  <div class="learning-center">
    <h2>学习中心</h2>

    <el-row :gutter="16" class="stats-row">
      <el-col :span="6">
        <el-card shadow="hover">
          <el-statistic title="学习课程" :value="stats.total_courses" />
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover">
          <el-statistic title="学习中" :value="stats.learning_courses" />
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover">
          <el-statistic title="已完成" :value="stats.completed_courses" />
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover">
          <el-statistic title="学习总时长" :value="formatSeconds(stats.total_duration)" />
        </el-card>
      </el-col>
    </el-row>

    <el-card class="section">
      <template #header>
        <div class="section-header">
          <h3>最近学习</h3>
        </div>
      </template>
      <div class="recent-list" v-if="recent.length">
        <div v-for="item in recent" :key="item.id" class="recent-item" @click="$router.push(`/course/${item.course_id}`)">
          <img :src="item.course_cover || 'https://picsum.photos/seed/default/400/225'" class="mini-cover" />
          <div class="recent-info">
            <h4>{{ item.course_title }}</h4>
            <el-progress :percentage="item.progress" :stroke-width="8" />
            <span class="time">最近学习：{{ formatTime(item.last_learn_at) }}</span>
          </div>
        </div>
      </div>
      <el-empty v-else description="暂无学习记录" />
    </el-card>

    <el-card class="section">
      <template #header>
        <div class="section-header">
          <h3>全部课程进度</h3>
          <el-radio-group v-model="progressFilter" @change="fetchProgress">
            <el-radio-button label="">全部</el-radio-button>
            <el-radio-button label="learning">学习中</el-radio-button>
            <el-radio-button label="completed">已完成</el-radio-button>
          </el-radio-group>
        </div>
      </template>
      <el-table :data="progressList" style="width: 100%">
        <el-table-column prop="course_title" label="课程" />
        <el-table-column label="进度" width="200">
          <template #default="{ row }">
            <el-progress :percentage="row.progress" :stroke-width="8" />
          </template>
        </el-table-column>
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.status === 'completed' ? 'success' : 'primary'" size="small">
              {{ row.status === 'completed' ? '已完成' : '学习中' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="学习时长" width="120">
          <template #default="{ row }">{{ formatSeconds(row.total_duration) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="100">
          <template #default="{ row }">
            <el-button text type="primary" @click="$router.push(`/course/${row.course_id}`)">继续</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-card class="section">
      <template #header><h3>学习历史</h3></template>
      <el-timeline>
        <el-timeline-item v-for="record in history" :key="record.id" :timestamp="formatTime(record.created_at)" placement="top">
          <span class="action-tag">{{ actionMap[record.action] }}</span>
          {{ record.course_title }}
          <span v-if="record.duration"> · {{ formatSeconds(record.duration) }}</span>
        </el-timeline-item>
      </el-timeline>
      <el-empty v-if="!history.length" description="暂无学习历史" />
      <div class="load-more" v-if="historyHasMore">
        <el-button @click="loadMoreHistory">加载更多</el-button>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { getStats, getRecent, getAllProgress, getHistory } from '../../api/learning'

const stats = reactive({
  total_courses: 0,
  learning_courses: 0,
  completed_courses: 0,
  total_duration: 0,
  total_records: 0
})

const recent = ref([])
const progressList = ref([])
const progressFilter = ref('')
const history = ref([])
const historyPage = ref(1)
const historyHasMore = ref(false)

const actionMap = { view: '浏览', start: '开始', progress: '学习', complete: '完成' }

function formatSeconds(sec) {
  if (!sec) return '0分钟'
  if (sec >= 3600) return `${Math.floor(sec / 3600)}小时${Math.floor((sec % 3600) / 60)}分`
  if (sec >= 60) return `${Math.floor(sec / 60)}分钟`
  return `${sec}秒`
}

function formatTime(iso) {
  if (!iso) return ''
  return new Date(iso).toLocaleString('zh-CN')
}

async function fetchProgress() {
  const res = await getAllProgress({ status: progressFilter.value || undefined })
  progressList.value = res.progress
}

async function loadMoreHistory() {
  historyPage.value++
  const res = await getHistory({ page: historyPage.value, per_page: 10 })
  history.value.push(...res.records)
  historyHasMore.value = res.page < res.pages
}

onMounted(async () => {
  const [statsRes, recentRes, histRes] = await Promise.all([
    getStats(),
    getRecent({ limit: 5 }),
    getHistory({ page: 1, per_page: 10 })
  ])
  Object.assign(stats, statsRes.stats)
  recent.value = recentRes.recent
  history.value = histRes.records
  historyHasMore.value = histRes.page < histRes.pages
  await fetchProgress()
})
</script>

<style scoped>
.learning-center h2 {
  margin-bottom: 20px;
}
.stats-row {
  margin-bottom: 20px;
}
.section {
  margin-bottom: 20px;
}
.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.recent-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.recent-item {
  display: flex;
  gap: 16px;
  align-items: center;
  padding: 12px;
  border-radius: 8px;
  cursor: pointer;
  transition: background 0.2s;
}
.recent-item:hover {
  background: #f5f7fa;
}
.mini-cover {
  width: 120px;
  height: 68px;
  object-fit: cover;
  border-radius: 4px;
}
.recent-info {
  flex: 1;
}
.recent-info h4 {
  margin-bottom: 8px;
}
.time {
  font-size: 12px;
  color: #999;
  margin-top: 4px;
  display: block;
}
.action-tag {
  display: inline-block;
  padding: 2px 6px;
  background: #ecf5ff;
  color: #409eff;
  border-radius: 3px;
  font-size: 12px;
  margin-right: 4px;
}
.load-more {
  text-align: center;
  margin-top: 16px;
}
</style>
