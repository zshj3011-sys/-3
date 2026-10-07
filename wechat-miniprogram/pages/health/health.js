// 健康档案
const demo = require('../../utils/demo.js')

Page({
  data: { archive: {} },

  onShow() {
    this.setData({ archive: demo.demoHealthArchive })
  },

  editProfile() { wx.showToast({ title: '编辑档案 (Demo)', icon: 'none' }) },
  goSettings() { wx.showToast({ title: '隐私设置 (Demo)', icon: 'none' }) },
  goAuth() { wx.showToast({ title: '我的医生 (Demo)', icon: 'none' }) },
  goAbout() {
    wx.showModal({
      title: 'MedMind Nexus 医智中枢',
      content: 'v1.0.0\n面向中小医疗机构的 AI 原生智能体平台\n等保三级 · 0 数据出院',
      showCancel: false,
    })
  },
})
