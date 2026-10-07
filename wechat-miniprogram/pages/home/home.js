// pages/home/home.js
const demo = require('../../utils/demo.js')

Page({
  data: {
    backendOnline: false,
    userName: '李女士',
    stats: { reports: 0, prescriptions: 0, visits: 0 },
    todayReminders: [],
    news: [],
  },

  onShow() {
    const app = getApp()
    this.setData({
      backendOnline: app.globalData.backendOnline,
      userName: (app.globalData.userInfo && app.globalData.userInfo.full_name) || '李女士',
    })
    this.loadData()
  },

  loadData() {
    // 演示数据(后端探活按 app.checkBackend 处理, 这里直接展示)
    const archive = demo.demoHealthArchive
    this.setData({
      stats: {
        reports: archive.reports,
        prescriptions: archive.prescriptions,
        visits: archive.recent_visits.length,
      },
      todayReminders: [
        { id: 1, icon: '💊', title: '布洛芬缓释胶囊 0.3g', time: '今晚 20:00 · 第 2 次', status: '待服', tagColor: 'teal' },
        { id: 2, icon: '🩺', title: '复诊提醒: 呼吸内科 张医生', time: '明天 09:30', status: '已预约', tagColor: 'blue' },
        { id: 3, icon: '📋', title: '血常规复查', time: '本周内', status: '待预约', tagColor: 'yellow' },
      ],
      news: [
        { id: 1, title: '夏季高温 这 5 类人群尤其要警惕中暑', source: '中国疾控中心', read: '12.3w' },
        { id: 2, title: '感冒发烧, 这些情况下千万别硬扛', source: '医智中枢科普', read: '8.4w' },
        { id: 3, title: '糖尿病患者饮食的 7 个核心原则', source: '中华医学会', read: '15.6w' },
      ],
    })
  },

  goTriage() { wx.switchTab({ url: '/pages/triage/triage' }) },
  goDepts() { wx.navigateTo({ url: '/pages/depts/depts' }) },
  goReport() { wx.navigateTo({ url: '/pages/report/report' }) },
  goMeds() { wx.switchTab({ url: '/pages/meds/meds' }) },
})
