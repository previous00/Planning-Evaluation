<template>
  <div class="mall-page">
    <div class="mall-header">
      <h2>积分商城</h2>
      <div class="points-badge">
        <el-icon><Coin /></el-icon>
        <span>我的积分：<strong>{{ pointsBalance }}</strong></span>
      </div>
    </div>

    <!-- 分类筛选 -->
    <div class="filter-bar">
      <el-radio-group v-model="typeFilter" @change="loadItems">
        <el-radio-button label="">全部</el-radio-button>
        <el-radio-button label="coupon">优惠券</el-radio-button>
        <el-radio-button label="vip">VIP会员</el-radio-button>
        <el-radio-button label="resource">学习资源</el-radio-button>
        <el-radio-button label="physical">实物奖品</el-radio-button>
      </el-radio-group>
    </div>

    <!-- 商品列表 -->
    <div class="items-grid" v-loading="loading">
      <div v-for="item in items" :key="item.id" class="item-card">
        <div class="item-image">
          <img :src="item.image || 'https://picsum.photos/seed/item/200/200'" :alt="item.name" />
          <el-tag class="item-type-tag" size="small" :type="typeTagMap[item.type]">
            {{ typeNameMap[item.type] }}
          </el-tag>
        </div>
        <div class="item-info">
          <h4>{{ item.name }}</h4>
          <p class="item-desc">{{ item.description }}</p>
          <div class="item-footer">
            <span class="item-price">
              <el-icon><Coin /></el-icon>
              {{ item.points_cost }} 积分
            </span>
            <span v-if="item.stock >= 0" class="item-stock">
              剩余 {{ item.stock }}
            </span>
          </div>
          <el-button
            type="primary"
            size="small"
            :disabled="pointsBalance < item.points_cost || item.stock === 0"
            @click="handleRedeem(item)"
          >
            {{ item.stock === 0 ? '已兑完' : '立即兑换' }}
          </el-button>
        </div>
      </div>
    </div>

    <el-empty v-if="!loading && items.length === 0" description="暂无商品" />

    <div class="pagination" v-if="total > perPage">
      <el-pagination
        v-model:current-page="page"
        :page-size="perPage"
        :total="total"
        layout="prev, pager, next"
        @current-change="loadItems"
      />
    </div>

    <!-- 我的兑换记录 -->
    <el-card class="orders-section">
      <template #header>
        <div class="section-header">
          <h3>我的兑换记录</h3>
          <el-button text type="primary" @click="showOrders = !showOrders">
            {{ showOrders ? '收起' : '展开' }}
          </el-button>
        </div>
      </template>
      <template v-if="showOrders">
        <el-table :data="orders" stripe v-loading="ordersLoading">
          <el-table-column prop="item_name" label="商品" />
          <el-table-column prop="points_spent" label="花费积分" width="100" />
          <el-table-column prop="status" label="状态" width="100">
            <template #default="{ row }">
              <el-tag :type="row.status === 'fulfilled' ? 'success' : 'warning'" size="small">
                {{ row.status === 'fulfilled' ? '已完成' : '待处理' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="created_at" label="兑换时间" width="180">
            <template #default="{ row }">
              {{ formatTime(row.created_at) }}
            </template>
          </el-table-column>
        </el-table>
        <el-empty v-if="orders.length === 0" description="暂无兑换记录" :image-size="40" />
      </template>
    </el-card>

    <!-- 积分规则 -->
    <el-card class="rules-section">
      <template #header><h3>积分获取规则</h3></template>
      <div class="rules-list">
        <div class="rule-item">
          <span class="rule-name">每日打卡</span>
          <span class="rule-value">+5积分（连续打卡额外奖励）</span>
        </div>
        <div class="rule-item">
          <span class="rule-name">每日学习</span>
          <span class="rule-value">每10分钟+1积分（每日上限20积分）</span>
        </div>
        <div class="rule-item">
          <span class="rule-name">完成章节</span>
          <span class="rule-value">+30积分</span>
        </div>
        <div class="rule-item">
          <span class="rule-name">完成课程</span>
          <span class="rule-value">+50积分</span>
        </div>
        <div class="rule-item">
          <span class="rule-name">完成学习计划</span>
          <span class="rule-value">+100积分</span>
        </div>
        <div class="rule-item">
          <span class="rule-name">购买课程</span>
          <span class="rule-value">消费金额的10%返还为积分</span>
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { getMallItems, redeemItem, getMyOrders, getMyPoints } from '../../api/mall'
import { ElMessage, ElMessageBox } from 'element-plus'

const items = ref([])
const orders = ref([])
const loading = ref(true)
const ordersLoading = ref(false)
const showOrders = ref(false)
const pointsBalance = ref(0)
const typeFilter = ref('')
const page = ref(1)
const perPage = 12
const total = ref(0)

const typeNameMap = { coupon: '优惠券', vip: 'VIP', resource: '资源', physical: '实物' }
const typeTagMap = { coupon: 'warning', vip: 'danger', resource: 'success', physical: '' }

function formatTime(iso) {
  if (!iso) return ''
  return new Date(iso).toLocaleString('zh-CN')
}

async function loadItems() {
  loading.value = true
  try {
    const params = { page: page.value, per_page: perPage }
    if (typeFilter.value) params.type = typeFilter.value
    const res = await getMallItems(params)
    items.value = res.items
    total.value = res.total
  } catch (e) {
    console.error('加载商品失败:', e)
  } finally {
    loading.value = false
  }
}

async function loadPoints() {
  try {
    const res = await getMyPoints()
    pointsBalance.value = res.points.balance
  } catch (e) {
    console.error('获取积分失败:', e)
  }
}

async function loadOrders() {
  ordersLoading.value = true
  try {
    const res = await getMyOrders({ page: 1, per_page: 50 })
    orders.value = res.orders
  } catch (e) {
    console.error('获取订单失败:', e)
  } finally {
    ordersLoading.value = false
  }
}

async function handleRedeem(item) {
  try {
    await ElMessageBox.confirm(
      `确认使用 ${item.points_cost} 积分兑换「${item.name}」？`,
      '确认兑换',
      { confirmButtonText: '确认兑换', cancelButtonText: '取消', type: 'info' }
    )
    await redeemItem({ item_id: item.id })
    ElMessage.success('兑换成功！')
    await Promise.all([loadItems(), loadPoints(), loadOrders()])
    showOrders.value = true
  } catch (e) {
    if (e !== 'cancel' && e?.response) {
      // error already shown by interceptor
    }
  }
}

onMounted(async () => {
  await Promise.all([loadItems(), loadPoints(), loadOrders()])
})
</script>

<style scoped>
.mall-page {
  max-width: 1200px;
}
.mall-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}
.mall-header h2 {
  margin: 0;
  font-size: 22px;
}
.points-badge {
  display: flex;
  align-items: center;
  gap: 6px;
  background: linear-gradient(135deg, #f6d365, #fda085);
  color: #fff;
  padding: 8px 16px;
  border-radius: 20px;
  font-size: 14px;
}
.points-badge strong {
  font-size: 18px;
}
.filter-bar {
  margin-bottom: 20px;
}
.items-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
  gap: 20px;
  margin-bottom: 24px;
}
.item-card {
  background: #fff;
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 2px 8px rgba(0,0,0,0.06);
  transition: transform 0.2s, box-shadow 0.2s;
}
.item-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 16px rgba(0,0,0,0.1);
}
.item-image {
  position: relative;
  height: 160px;
  overflow: hidden;
}
.item-image img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}
.item-type-tag {
  position: absolute;
  top: 8px;
  right: 8px;
}
.item-info {
  padding: 16px;
}
.item-info h4 {
  margin: 0 0 8px;
  font-size: 15px;
  color: #333;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.item-desc {
  font-size: 12px;
  color: #999;
  margin: 0 0 12px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.item-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}
.item-price {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 16px;
  font-weight: bold;
  color: #e6a23c;
}
.item-stock {
  font-size: 12px;
  color: #999;
}
.pagination {
  display: flex;
  justify-content: center;
  margin-bottom: 24px;
}
.orders-section, .rules-section {
  margin-bottom: 20px;
}
.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.section-header h3 {
  margin: 0;
}
.rules-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.rule-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 0;
  border-bottom: 1px dashed #f0f0f0;
}
.rule-name {
  font-weight: 500;
  color: #333;
}
.rule-value {
  color: #e6a23c;
  font-size: 14px;
}
</style>
