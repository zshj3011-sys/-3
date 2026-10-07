// utils/api.js · MedMind Nexus 后端 API 客户端
// 对应后端: medmind-backend FastAPI · /v1 前缀

const getApp_ = () => getApp()

/**
 * 统一请求封装
 * - 自动注入 Authorization
 * - 自动解开后端 {code, message, data} 包络
 * - 401 自动尝试 refresh
 */
function request(method, path, data, opts = {}) {
  return new Promise((resolve, reject) => {
    const app = getApp_()
    const baseUrl = (app && app.globalData && app.globalData.baseUrl) || 'http://localhost:8000'
    const token = (app && app.globalData && app.globalData.token) || ''

    const header = {
      'Content-Type': 'application/json',
      ...opts.header,
    }
    if (token && !opts.noAuth) {
      header['Authorization'] = `Bearer ${token}`
    }

    wx.request({
      url: baseUrl + path,
      method: method.toUpperCase(),
      data: data || {},
      header,
      timeout: opts.timeout || 15000,
      success(res) {
        if (res.statusCode >= 200 && res.statusCode < 300) {
          const body = res.data
          // 后端标准包络 {code, message, data}
          if (body && typeof body === 'object' && 'code' in body) {
            if (body.code === 200) {
              resolve(body.data)
            } else {
              reject(new Error(body.message || `业务错误 ${body.code}`))
            }
          } else {
            resolve(body) // 非标准响应直接返回
          }
        } else if (res.statusCode === 401) {
          // TODO: refresh token 实现
          if (app) app.clearAuth()
          reject(new Error('登录已过期, 请重新登录'))
        } else {
          reject(new Error(`HTTP ${res.statusCode}: ${res.data && res.data.message || '服务器错误'}`))
        }
      },
      fail(err) {
        reject(new Error('网络异常: ' + (err.errMsg || '未知错误')))
      }
    })
  })
}

// ============== 接口封装 ==============

// 健康检查 (用于探活)
function healthCheck() {
  return request('GET', '/health', null, { noAuth: true, timeout: 3000 })
}

// 登录
function login(username, password) {
  return request('POST', '/v1/auth/login', { username, password }, { noAuth: true })
}

// 当前用户
function getMe() {
  return request('GET', '/v1/auth/me')
}

// AI 预问诊
const Triage = {
  start(payload) {
    return request('POST', '/v1/triage/start', payload)
  },
  message(payload) {
    return request('POST', '/v1/triage/message', payload)
  },
  summary(sessionId) {
    return request('GET', `/v1/triage/${sessionId}/summary`)
  },
}

// 科室
function listDepartments() {
  return request('GET', '/v1/departments/')
}

// 报告解读
function interpretReport(payload) {
  return request('POST', '/v1/reports/interpret', payload)
}

// 演示数据 fallback
function demoWechatScreens() {
  return request('GET', '/v1/demo/wechat-screens', null, { noAuth: true })
}

module.exports = {
  request,
  healthCheck,
  login,
  getMe,
  Triage,
  listDepartments,
  interpretReport,
  demoWechatScreens,
}
