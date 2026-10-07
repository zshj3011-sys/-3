// 智能分诊
const api = require('../../utils/api.js')
const demo = require('../../utils/demo.js')

// 简易关键词 -> 科室 匹配
const KEYWORD_MAP = [
  { keys: ['头痛', '头晕', '失眠', '记忆', '癫痫', '中风', '面瘫'], dept: '神经内科', conf: 92 },
  { keys: ['胸痛', '胸闷', '心悸', '高血压', '心慌'], dept: '心血管内科', conf: 95 },
  { keys: ['腹痛', '胃痛', '腹泻', '便秘', '反酸', '黄疸'], dept: '消化内科', conf: 93 },
  { keys: ['咳嗽', '咳痰', '气喘', '哮喘', '气短', '发热'], dept: '呼吸内科', conf: 90 },
  { keys: ['糖尿病', '甲状腺', '尿多', '消瘦', '肥胖'], dept: '内分泌科', conf: 91 },
  { keys: ['皮疹', '湿疹', '痤疮', '脱发', '瘙痒'], dept: '皮肤科', conf: 94 },
  { keys: ['视力', '眼痛', '眼干', '近视', '白内障'], dept: '眼科', conf: 96 },
  { keys: ['骨折', '腰痛', '关节', '颈椎', '腰椎'], dept: '骨科', conf: 92 },
]

Page({
  data: {
    keyword: '',
    aiSuggestion: null,
    depts: [],
    _timer: null,
  },

  onLoad() {
    this.loadDepts()
  },

  async loadDepts() {
    const app = getApp()
    if (app.globalData.backendOnline) {
      try {
        const list = await api.listDepartments()
        if (list && list.length) {
          this.setData({ depts: list.map((d, i) => ({
            id: d.id, name: d.name, code: d.code || ('d'+i),
            icon: this.iconFor(d.name), desc: d.description || ''
          })) })
          return
        }
      } catch (e) {/* fallback */}
    }
    this.setData({ depts: demo.demoDepartments })
  },

  iconFor(name) {
    if (name.includes('心')) return '❤️'
    if (name.includes('消化')) return '🫁'
    if (name.includes('呼吸')) return '🌬️'
    if (name.includes('内分泌')) return '🩸'
    if (name.includes('神经')) return '🧠'
    if (name.includes('皮肤')) return '🧴'
    if (name.includes('眼')) return '👁️'
    if (name.includes('骨')) return '🦴'
    return '🏥'
  },

  onSearch(e) {
    const kw = e.detail.value
    this.setData({ keyword: kw })
    if (this.data._timer) clearTimeout(this.data._timer)
    if (!kw.trim()) {
      this.setData({ aiSuggestion: null })
      return
    }
    this.data._timer = setTimeout(() => this.aiMatch(kw), 300)
  },

  aiMatch(kw) {
    for (const m of KEYWORD_MAP) {
      for (const k of m.keys) {
        if (kw.includes(k)) {
          this.setData({ aiSuggestion: { name: m.dept, confidence: m.conf } })
          return
        }
      }
    }
    this.setData({ aiSuggestion: { name: '全科 / 内科门诊', confidence: 60 } })
  },

  goBook(e) {
    const id = e.currentTarget.dataset.id
    wx.showToast({ title: '跳转挂号 (Demo)', icon: 'none' })
  },
})
