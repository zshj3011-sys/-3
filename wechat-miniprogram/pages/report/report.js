// 报告解读
const api = require('../../utils/api.js')
const demo = require('../../utils/demo.js')

Page({
  data: { loading: false, result: null },

  chooseImage() {
    wx.chooseMedia({
      count: 1,
      mediaType: ['image'],
      sourceType: ['camera', 'album'],
      success: (res) => {
        const f = res.tempFiles[0]
        console.log('选择图片:', f.tempFilePath)
        this.parseReport(f.tempFilePath)
      },
      fail: () => {
        // 选择取消, 直接演示
        this.parseReport(null)
      }
    })
  },

  async parseReport(filePath) {
    this.setData({ loading: true, result: null })
    const app = getApp()
    // 真实场景:走 OCR + /v1/reports/interpret
    // 演示模式直接返回 demo 结果
    setTimeout(async () => {
      if (app.globalData.backendOnline) {
        try {
          const r = await api.interpretReport({
            report_type: '血常规',
            ocr_text: 'WBC 12.5, N% 82.3, RBC 4.8',
          })
          this.setData({ loading: false, result: r })
          return
        } catch (e) {/* fallback */}
      }
      this.setData({ loading: false, result: demo.demoReportInterpret })
    }, 1800)
  },

  reset() {
    this.setData({ result: null })
  },
})
