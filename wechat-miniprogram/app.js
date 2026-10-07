// app.js · MedMind Nexus 微信小程序入口
const api = require('./utils/api.js')

App({
  globalData: {
    userInfo: null,
    token: null,
    refreshToken: null,
    baseUrl: 'https://api.medmind.example.com', // 生产环境替换
    // 本地开发可改为: 'http://localhost:8000'
    backendOnline: false,
    version: '1.0.0'
  },

  onLaunch() {
    // 读取本地 token
    const token = wx.getStorageSync('access_token')
    const refresh = wx.getStorageSync('refresh_token')
    const user = wx.getStorageSync('user_info')
    if (token) this.globalData.token = token
    if (refresh) this.globalData.refreshToken = refresh
    if (user) this.globalData.userInfo = user

    // 后端探活
    this.checkBackend()

    // 启动时打 log
    console.log('[MedMind] 小程序启动', { version: this.globalData.version })
  },

  // 检测后端是否可用,不可用则进入 demo 模式
  async checkBackend() {
    try {
      const r = await api.healthCheck()
      this.globalData.backendOnline = (r && r.status === 'ok')
      console.log('[MedMind] 后端在线状态:', this.globalData.backendOnline)
    } catch (e) {
      this.globalData.backendOnline = false
      console.warn('[MedMind] 后端离线, 走 demo 数据模式')
    }
  },

  // 保存登录态
  setAuth(tokenInfo, userInfo) {
    this.globalData.token = tokenInfo.access_token
    this.globalData.refreshToken = tokenInfo.refresh_token
    this.globalData.userInfo = userInfo
    wx.setStorageSync('access_token', tokenInfo.access_token)
    wx.setStorageSync('refresh_token', tokenInfo.refresh_token)
    wx.setStorageSync('user_info', userInfo)
  },

  // 清除登录态
  clearAuth() {
    this.globalData.token = null
    this.globalData.refreshToken = null
    this.globalData.userInfo = null
    wx.removeStorageSync('access_token')
    wx.removeStorageSync('refresh_token')
    wx.removeStorageSync('user_info')
  }
})
