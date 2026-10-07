// 用药提醒
const demo = require('../../utils/demo.js')

Page({
  data: {
    streakDays: 7,
    meds: [],
  },

  onShow() {
    const list = demo.demoMeds.map(m => ({
      ...m,
      status: 'pending',
    }))
    this.setData({ meds: list })
  },

  markTaken(e) {
    const id = e.currentTarget.dataset.id
    const meds = this.data.meds.map(m =>
      m.id === id ? { ...m, status: 'taken' } : m
    )
    this.setData({ meds })
    wx.showToast({ title: '已记录, 提醒已关闭', icon: 'success' })
  },

  addMed() {
    wx.showModal({
      title: '添加药品',
      content: '生产版本支持: 扫码识别 / 拍照 OCR / 处方一键导入',
      showCancel: false,
    })
  },
})
