<template>
  <div class="dashboard">
    <h2>数据概览</h2>
    <el-row :gutter="16" class="stats-row">
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card">
          <el-statistic title="总用户数" :value="data.user_count">
            <template #prefix><el-icon><User /></el-icon></template>
          </el-statistic>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card">
          <el-statistic title="总课程数" :value="data.course_count">
            <template #prefix><el-icon><Reading /></el-icon></template>
          </el-statistic>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card">
          <el-statistic title="活跃学员" :value="data.active_learners">
            <template #prefix><el-icon><TrendCharts /></el-icon></template>
          </el-statistic>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card">
          <el-statistic title="学习记录" :value="data.record_count">
            <template #prefix><el-icon><Document /></el-icon></template>
          </el-statistic>
        </el-card>
      </el-col>
    </el-row>

    <!-- Recommendation Stats -->
    <el-card class="recommend-stats-card">
      <template #header><h3>推荐系统效果分析</h3></template>
      <div v-if="recStats">
        <el-row :gutter="16" class="rec-stats-row">
          <el-col :span="6">
            <div class="rec-stat">
              <span class="rec-stat-value">{{ recStats.total_impressions }}</span>
              <span class="rec-stat-label">总曝光数</span>
            </div>
          </el-col>
          <el-col :span="6">
            <div class="rec-stat">
              <span class="rec-stat-value">{{ recStats.total_clicks }}</span>
              <span class="rec-stat-label">总点击数</span>
            </div>
          </el-col>
          <el-col :span="6">
            <div class="rec-stat">
              <span class="rec-stat-value">{{ (recStats.ctr * 100).toFixed(1) }}%</span>
              <span class="rec-stat-label">点击率(CTR)</span>
            </div>
          </el-col>
          <el-col :span="6">
            <div class="rec-stat">
              <span class="rec-stat-value">{{ (recStats.coverage * 100).toFixed(1) }}%</span>
              <span class="rec-stat-label">课程覆盖率</span>
            </div>
          </el-col>
        </el-row>
        <el-table :data="strategyStats" style="width: 100%; margin-top: 16px;">
          <el-table-column prop="name" label="推荐策略" />
          <el-table-column prop="impressions" label="曝光数" width="100" />
          <el-table-column prop="clicks" label="点击数" width="100" />
          <el-table-column label="点击率" width="120">
            <template #default="{ row }">
              <el-tag :type="row.ctr > 0.1 ? 'success' : 'info'">{{ (row.ctr * 100).toFixed(1) }}%</el-tag>
            </template>
          </el-table-column>
        </el-table>
      </div>
      <el-empty v-else description="暂无推荐数据" :image-size="60" />
    </el-card>

    <el-card>
      <template #header><h3>热门课程学习统计</h3></template>
      <el-table :data="learningStats" style="width: 100%">
        <el-table-column prop="course_title" label="课程名称" />
        <el-table-column prop="learner_count" label="学习人数" width="120" sortable />
        <el-table-column label="平均进度" width="200">
          <template #default="{ row }">
            <el-progress :percentage="row.avg_progress" :stroke-width="8" />
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { getDashboard, getLearningStats } from '../../api/admin'
import { getRecommendStats } from '../../api/recommend'

const data = reactive({
  user_count: 0,
  course_count: 0,
  active_learners: 0,
  record_count: 0,
  total_duration: 0
})

const learningStats = ref([])
const recStats = ref(null)
const strategyStats = ref([])

const strategyNameMap = {
  collaborative: '协同过滤',
  content_based: '内容推荐',
  popularity: '热门推荐'
}

onMounted(async () => {
  const [dashRes, statsRes] = await Promise.all([getDashboard(), getLearningStats()])
  Object.assign(data, dashRes.dashboard)
  learningStats.value = statsRes.learning_stats

  try {
    const recRes = await getRecommendStats()
    recStats.value = recRes.stats
    if (recRes.stats.per_strategy) {
      strategyStats.value = Object.entries(recRes.stats.per_strategy).map(([key, val]) => ({
        name: strategyNameMap[key] || key,
        ...val
      }))
    }
  } catch (e) {
    // stats may be empty
  }
})
</script>

<style scoped>
.dashboard h2 {
  margin-bottom: 20px;
}
.stats-row {
  margin-bottom: 24px;
}
.stat-card {
  text-align: center;
}
.recommend-stats-card {
  margin-bottom: 24px;
}
.rec-stats-row {
  text-align: center;
}
.rec-stat {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 12px 0;
}
.rec-stat-value {
  font-size: 24px;
  font-weight: bold;
  color: #409eff;
}
.rec-stat-label {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
}
</style>
