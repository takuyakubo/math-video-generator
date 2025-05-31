<template>
  <div id="app">
    <el-container>
      <el-header>
        <div class="header-content">
          <h1>Math Video Generator</h1>
          <nav>
            <router-link to="/">ホーム</router-link>
          </nav>
        </div>
      </el-header>
      
      <el-main>
        <router-view />
      </el-main>
      
      <el-footer>
        <div class="footer-content">
          <p>&copy; 2024 Math Video Generator. Built with ❤️ for the mathematical community.</p>
        </div>
      </el-footer>
    </el-container>
  </div>
</template>

<style>
#app {
  font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
  color: #2c3e50;
  min-height: 100vh;
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  height: 100%;
}

.header-content h1 {
  margin: 0;
  color: #409eff;
}

.header-content nav a {
  color: #606266;
  text-decoration: none;
  margin-left: 20px;
}

.header-content nav a:hover {
  color: #409eff;
}

.footer-content {
  text-align: center;
  color: #909399;
}

.el-main {
  padding: 20px;
  min-height: calc(100vh - 120px);
}
</style>