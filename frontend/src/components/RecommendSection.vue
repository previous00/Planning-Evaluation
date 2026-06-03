<template>
  <div class="recommend-section" v-if="recommendations.length > 0">
    <div class="section-header">
      <h2>为你推荐</h2>
      <el-button link type="primary" @click="$router.push('/recommend')">查看更多 →</el-button>
    </div>
    <div class="recommend-list">
      <div
        v-for="(item, index) in recommendations"
        :key="item.course.id"
        class="recommend-card"
        @click="handleClick(item, index)"
      >
        <div class="cover">
          <img :src="item.course.cover_image || 'https://picsum.photos/seed/default/400/225'" :alt="item.course.title" />
          <span class="score-badge">{{ Math.round(item.score * 100) }}%匹配</span>
        </div>
        <div class="info">
          <h4 class="title">{{ item.course.title }}</h4>
          <p class="reason">{{ item.reason }}</p>
          <div class="meta">
            <span class="price" v-if="item.course.price > 0">¥{{ item.course.price }}</span>
            <span class="price free" v-else>免费</span>
            <span class="students">{{ item.course.student_count }}人学习</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { getRecommendations, getPopularRecommendations, trackClick } from '../api/recommend'

const router = useRouter()
const recommendations = ref([])
const logIds = ref([])

const props = defineProps({
  isLoggedIn: { type: Boolean, default: false }
})

async function fetchRecommendations() {
  try {
    if (props.isLoggedIn) {
      const res = await getRecommendations({ limit: 5 })
      recommendations.value = res.recommendations
      logIds.value = res.log_ids
    } else {
      const res = await getPopularRecommendations({ limit: 5 })
      recommendations.value = res.recommendations
    }
  } catch (e) {
    // silent fail for recommendation section
  }
}

function handleClick(item, index) {
  if (props.isLoggedIn && logIds.value[index]) {
    trackClick({ log_id: logIds.value[index], course_id: item.course.id }).catch(() => {})
  }
  router.push(`/course/${item.course.id}`)
}

onMounted(fetchRecommendations)
</script>

<style scoped>
.recommend-section {
  margin-bottom: 32px;
  padding: 24px;
  background: linear-gradient(135deg, #f0f7ff 0%, #e8f4f8 100%);
  border-radius: 12px;
}
.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}
.section-header h2 {
  font-size: 18px;
  color: #333;
  margin: 0;
}
.recommend-list {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 16px;
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
  transform: translateY(-3px);
  box-shadow: 0 6px 16px rgba(0, 0, 0, 0.12);
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
.score-badge {
  position: absolute;
  top: 6px;
  left: 6px;
  background: rgba(64, 158, 255, 0.9);
  color: #fff;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 11px;
}
.info {
  padding: 12px;
}
.title {
  font-size: 13px;
  color: #333;
  margin: 0 0 6px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.reason {
  font-size: 11px;
  color: #909399;
  margin: 0 0 8px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.meta {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.price {
  font-size: 14px;
  font-weight: bold;
  color: #f56c6c;
}
.price.free {
  color: #67c23a;
}
.students {
  font-size: 11px;
  color: #999;
}
</style>
