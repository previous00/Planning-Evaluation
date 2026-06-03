<template>
  <div class="admin-layout">
    <el-container>
      <el-aside width="220px" class="aside">
        <div class="admin-logo">
          <el-icon :size="20"><Setting /></el-icon>
          <span>管理后台</span>
        </div>
        <el-menu router :default-active="$route.path" class="admin-menu">
          <el-menu-item index="/admin">
            <el-icon><DataAnalysis /></el-icon>
            <span>仪表盘</span>
          </el-menu-item>
          <el-menu-item index="/admin/users">
            <el-icon><User /></el-icon>
            <span>用户管理</span>
          </el-menu-item>
          <el-menu-item index="/admin/courses">
            <el-icon><Reading /></el-icon>
            <span>课程管理</span>
          </el-menu-item>
          <el-menu-item index="/admin/categories">
            <el-icon><Menu /></el-icon>
            <span>分类管理</span>
          </el-menu-item>
        </el-menu>
        <div class="back-link">
          <el-button text @click="$router.push('/')">
            <el-icon><Back /></el-icon> 返回前台
          </el-button>
        </div>
      </el-aside>
      <el-main class="admin-main">
        <router-view />
      </el-main>
    </el-container>
  </div>
</template>

<script setup>
</script>

<style scoped>
.admin-layout {
  min-height: 100vh;
}
.aside {
  background: #001529;
  min-height: 100vh;
  position: fixed;
  left: 0;
  top: 0;
  bottom: 0;
}
.admin-logo {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 20px;
  color: #fff;
  font-size: 16px;
  font-weight: bold;
}
.admin-menu {
  border-right: none;
  background: #001529;
}
.admin-menu .el-menu-item {
  color: #ffffffa6;
}
.admin-menu .el-menu-item:hover,
.admin-menu .el-menu-item.is-active {
  background: #1890ff;
  color: #fff;
}
.back-link {
  position: absolute;
  bottom: 20px;
  left: 20px;
}
.back-link .el-button {
  color: #ffffffa6;
}
.admin-main {
  margin-left: 220px;
  padding: 24px;
  background: #f0f2f5;
  min-height: 100vh;
}
</style>
