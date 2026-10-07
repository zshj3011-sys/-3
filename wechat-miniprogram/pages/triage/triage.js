// AI 预问诊页面
const api = require('../../utils/api.js')
const demo = require('../../utils/demo.js')

Page({
  data: {
    backendOnline: false,
    messages: [],
    inputText: '',
    round: 1,
    maxRounds: 5,
    progress: 20,
    loading: false,
    sessionId: '',
    summary: null,
    lastMsgId: '',
    _msgSeq: 0,
    _demoStep: 0,
  },

  onLoad() {
    const app = getApp()
    this.setData({ backendOnline: app.globalData.backendOnline })
    this.startSession()
  },

  appendMsg(role, content, options) {
    const seq = this.data._msgSeq + 1
    const msg = { id: 'm' + seq, role, content, options: options || [] }
    this.setData({
      messages: [...this.data.messages, msg],
      lastMsgId: msg.id,
      _msgSeq: seq,
    })
    return msg.id
  },

  async startSession() {
    this.setData({ loading: true })
    // 演示模式
    if (!this.data.backendOnline) {
      setTimeout(() => {
        const reply = demo.demoTriageReplies.start
        this.appendMsg('ai', reply.reply, reply.options)
        this.setData({
          loading: false,
          sessionId: reply.session_id,
          round: 1,
          progress: 20,
        })
      }, 800)
      return
    }
    try {
      const res = await api.Triage.start({ chief_complaint: '请描述您的不适' })
      this.appendMsg('ai', res.reply || '请问您哪里不舒服?', res.options)
      this.setData({
        loading: false,
        sessionId: res.session_id,
        round: res.round || 1,
        progress: Math.round((res.round || 1) / this.data.maxRounds * 100),
      })
    } catch (e) {
      wx.showToast({ title: e.message, icon: 'none' })
      this.setData({ loading: false })
    }
  },

  onInput(e) {
    this.setData({ inputText: e.detail.value })
  },

  chooseOption(e) {
    const option = e.currentTarget.dataset.option
    this.appendMsg('user', option)
    this.send(option)
  },

  sendMessage() {
    const txt = (this.data.inputText || '').trim()
    if (!txt) return
    this.appendMsg('user', txt)
    this.setData({ inputText: '' })
    this.send(txt)
  },

  async send(text) {
    this.setData({ loading: true })
    if (!this.data.backendOnline) {
      // demo 模式
      setTimeout(() => {
        const step = this.data._demoStep
        const rounds = demo.demoTriageReplies.rounds
        if (step < rounds.length) {
          const r = rounds[step]
          this.appendMsg('ai', r.reply, r.options)
          const newRound = this.data.round + 1
          this.setData({
            loading: false,
            round: newRound,
            progress: Math.round(newRound / this.data.maxRounds * 100),
            _demoStep: step + 1,
          })
          if (r.finished) {
            setTimeout(() => this.loadSummary(), 600)
          }
        } else {
          this.loadSummary()
        }
      }, 900)
      return
    }
    try {
      const res = await api.Triage.message({ session_id: this.data.sessionId, message: text })
      this.appendMsg('ai', res.reply, res.options)
      const newRound = (res.round || this.data.round + 1)
      this.setData({
        loading: false,
        round: newRound,
        progress: Math.min(100, Math.round(newRound / this.data.maxRounds * 100)),
      })
      if (res.finished || res.session_ended) {
        this.loadSummary()
      }
    } catch (e) {
      wx.showToast({ title: e.message, icon: 'none' })
      this.setData({ loading: false })
    }
  },

  async loadSummary() {
    if (!this.data.backendOnline) {
      this.setData({ summary: demo.demoTriageReplies.summary, progress: 100 })
      return
    }
    try {
      const s = await api.Triage.summary(this.data.sessionId)
      this.setData({ summary: s, progress: 100 })
    } catch (e) {
      // 后端拿不到摘要就用 demo
      this.setData({ summary: demo.demoTriageReplies.summary, progress: 100 })
    }
  },

  voiceTip() {
    wx.showModal({
      title: '语音输入',
      content: '生产环境将集成微信原生 RecorderManager 录音 → 上传 /v1/ws/asr 实时转写',
      showCancel: false,
    })
  },

  restart() {
    this.setData({
      messages: [],
      summary: null,
      round: 1,
      progress: 20,
      _msgSeq: 0,
      _demoStep: 0,
    })
    this.startSession()
  },

  goBook() {
    wx.showToast({ title: '跳转预约挂号', icon: 'success' })
    setTimeout(() => wx.navigateTo({ url: '/pages/depts/depts' }), 600)
  },
})
