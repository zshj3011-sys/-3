/**
 * MedMind Nexus 前端 API 客户端
 * 统一封装与 FastAPI 后端的 HTTP / WebSocket 交互
 */
(function (global) {
  function autoDetectBase() {
    // Tauri 桌面端: 后端默认本机 8000
    if (typeof window !== 'undefined' && window.__TAURI__) return 'http://localhost:8000/v1';
    // file:// 单独打开 HTML: 默认本机 8000
    if (window.location.protocol === 'file:') return 'http://localhost:8000/v1';
    // 同源挂载 (FastAPI /web): 同源下 /v1
    return window.location.origin + '/v1';
  }
  const API_BASE = (localStorage.getItem('MEDMIND_API_BASE') || autoDetectBase()).replace(/\/$/, '');

  const TOKEN_KEY = 'medmind_access_token';
  const REFRESH_KEY = 'medmind_refresh_token';
  const USER_KEY = 'medmind_user';

  function getToken() { return localStorage.getItem(TOKEN_KEY); }
  function setToken(t) { t ? localStorage.setItem(TOKEN_KEY, t) : localStorage.removeItem(TOKEN_KEY); }
  function getRefresh() { return localStorage.getItem(REFRESH_KEY); }
  function setRefresh(t) { t ? localStorage.setItem(REFRESH_KEY, t) : localStorage.removeItem(REFRESH_KEY); }
  function getUser() { try { return JSON.parse(localStorage.getItem(USER_KEY) || 'null'); } catch (e) { return null; } }
  function setUser(u) { u ? localStorage.setItem(USER_KEY, JSON.stringify(u)) : localStorage.removeItem(USER_KEY); }

  class ApiError extends Error {
    constructor(status, code, message, detail) {
      super(message);
      this.status = status; this.code = code; this.detail = detail;
    }
  }

  async function request(method, path, body, opts) {
    opts = opts || {};
    const url = path.startsWith('http') ? path : API_BASE + path;
    const headers = Object.assign({ 'Content-Type': 'application/json' }, opts.headers || {});
    const token = getToken();
    if (token && !opts.skipAuth) headers['Authorization'] = 'Bearer ' + token;
    const init = { method, headers };
    if (body !== undefined && body !== null) init.body = JSON.stringify(body);
    let resp;
    try {
      resp = await fetch(url, init);
    } catch (e) {
      throw new ApiError(0, 'network_error', '无法连接后端 ' + API_BASE + ' (' + e.message + ')', e);
    }
    let data = null;
    const ct = resp.headers.get('content-type') || '';
    if (ct.includes('application/json')) {
      try { data = await resp.json(); } catch (e) { data = null; }
    } else {
      data = await resp.text();
    }
    if (!resp.ok) {
      const msg = (data && data.message) || resp.statusText || ('HTTP ' + resp.status);
      throw new ApiError(resp.status, (data && data.code) || resp.status, msg, data);
    }
    return data;
  }

  function qs(params) {
    if (!params) return '';
    const arr = [];
    Object.keys(params).forEach(k => {
      if (params[k] !== undefined && params[k] !== null && params[k] !== '') {
        arr.push(encodeURIComponent(k) + '=' + encodeURIComponent(params[k]));
      }
    });
    return arr.length ? '?' + arr.join('&') : '';
  }

  const Auth = {
    async login(username, password, mfa_code) {
      const r = await request('POST', '/auth/login', { username, password, mfa_code }, { skipAuth: true });
      const d = r.data;
      setToken(d.access_token); setRefresh(d.refresh_token); setUser(d.user);
      return d;
    },
    async logout() {
      try { await request('POST', '/auth/logout'); } catch (e) {}
      setToken(null); setRefresh(null); setUser(null);
    },
    async register(payload) { return (await request('POST', '/auth/register', payload, { skipAuth: true })).data; },
    async me() { return (await request('GET', '/auth/me')).data; },
    isLoggedIn() { return !!getToken(); },
    getUser, getToken,
  };

  const Patients = {
    list: (params) => request('GET', '/patients/' + qs(params)),
    get: (id) => request('GET', '/patients/' + id).then(r => r.data),
    create: (body) => request('POST', '/patients/', body).then(r => r.data),
    update: (id, body) => request('PATCH', '/patients/' + id, body).then(r => r.data),
    delete: (id) => request('DELETE', '/patients/' + id),
  };

  const Doctors = {
    list: (params) => request('GET', '/doctors/' + qs(params)).then(r => r.data),
    get: (id) => request('GET', '/doctors/' + id).then(r => r.data),
  };

  const Departments = {
    list: () => request('GET', '/departments/').then(r => r.data),
  };

  const Triage = {
    start: (body) => request('POST', '/triage/start', body || {}).then(r => r.data),
    send: (session_id, message) => request('POST', '/triage/message', { session_id, message }).then(r => r.data),
    summary: (session_id) => request('GET', '/triage/' + session_id + '/summary').then(r => r.data),
  };

  const Records = {
    aiDraft: (body) => request('POST', '/records/ai-draft', body).then(r => r.data),
    create: (body) => request('POST', '/records/', body).then(r => r.data),
    list: (params) => request('GET', '/records/' + qs(params)),
    get: (id) => request('GET', '/records/' + id).then(r => r.data),
    qualityCheck: (id) => request('POST', '/records/' + id + '/quality-check').then(r => r.data),
    sign: (id) => request('POST', '/records/' + id + '/sign').then(r => r.data),
  };

  const Prescriptions = {
    audit: (body) => request('POST', '/prescriptions/audit', body).then(r => r.data),
    // v3.4 新增: AI 辅助开方 - 对齐 PRD 6.1
    suggest: (body) => request('POST', '/prescriptions/suggest', body).then(r => r.data),
    create: (body) => request('POST', '/prescriptions/', body).then(r => r.data),
    list: (params) => request('GET', '/prescriptions/' + qs(params)),
    get: (id) => request('GET', '/prescriptions/' + id).then(r => r.data),
  };

  const DRG = {
    predict: (body) => request('POST', '/drg/predict', body).then(r => r.data),
    cases: (params) => request('GET', '/drg/cases' + qs(params)),
    dashboard: () => request('GET', '/drg/dashboard').then(r => r.data),
    // v3.4 新增: 费用预警 - 对齐 PRD 7.2
    costAlert: (params) => request('GET', '/drg/cost-alert' + qs(params)).then(r => r.data),
  };

  const Research = {
    searchLiterature: (body) => request('POST', '/research/literature/search', body).then(r => r.data),
    generateGrant: (body) => request('POST', '/research/grant/generate', body).then(r => r.data),
    polishPaper: (text) => request('POST', '/research/paper/polish', { text }).then(r => r.data),
    recommendStats: (body) => request('POST', '/research/statistics/recommend', body).then(r => r.data),
  };

  const Reports = {
    interpret: (body) => request('POST', '/reports/interpret', body).then(r => r.data),
    diagnose: (body) => request('POST', '/reports/diagnose', body).then(r => r.data),
  };

  const Admin = {
    dashboard: () => request('GET', '/admin/dashboard').then(r => r.data),
    quality: () => request('GET', '/admin/quality').then(r => r.data),
    aiAnalytics: () => request('GET', '/admin/ai-analytics').then(r => r.data),
  };

  const Demo = {
    wechatScreens: () => request('GET', '/demo/wechat-screens').then(r => r.data),
    doctorSchedule: () => request('GET', '/demo/doctor-schedule').then(r => r.data),
  };

  // v3.6 新增: 挂号预约 (PRD 用户故事 #46 Must)
  const Appointments = {
    list: (params) => request('GET', '/appointments/' + qs(params)),
    create: (body) => request('POST', '/appointments/', body).then(r => r.data),
    today: (params) => request('GET', '/appointments/today' + qs(params)).then(r => r.data),
    slots: (params) => request('GET', '/appointments/slots' + qs(params)).then(r => r.data),
    cancel: (id) => request('PATCH', '/appointments/' + id + '/cancel').then(r => r.data),
    checkIn: (id) => request('PATCH', '/appointments/' + id + '/check-in').then(r => r.data),
  };

  // v3.6 新增: 消息通知 (PRD 患者端 M1 必备模块)
  const Notifications = {
    list: (params) => request('GET', '/notifications/' + qs(params)),
    unreadCount: () => request('GET', '/notifications/unread-count').then(r => r.data),
    markRead: (id) => request('PATCH', '/notifications/' + id + '/read').then(r => r.data),
    markAllRead: () => request('POST', '/notifications/mark-all-read').then(r => r.data),
    send: (body) => request('POST', '/notifications/', body).then(r => r.data),
  };

  function wsUrl(path) {
    const proto = location.protocol === 'https:' ? 'wss:' : 'ws:';
    let base = API_BASE.replace(/^https?:/, proto).replace(/\/v1$/, '');
    return base + path;
  }

  const WS = {
    asr(onMessage, onClose, demo) {
      if (demo === undefined) demo = 1;
      const ws = new WebSocket(wsUrl('/v1/ws/asr?demo=' + (demo ? 1 : 0)));
      ws.onmessage = (e) => { try { onMessage(JSON.parse(e.data)); } catch (err) { onMessage({ raw: e.data }); } };
      ws.onclose = onClose || function () {};
      return ws;
    },
    aiSuggest(onMessage, onClose) {
      const ws = new WebSocket(wsUrl('/v1/ws/ai-suggest'));
      ws.onmessage = (e) => { try { onMessage(JSON.parse(e.data)); } catch (err) { onMessage({ raw: e.data }); } };
      ws.onclose = onClose || function () {};
      return ws;
    },
  };

  function toast(message, type) {
    let el = document.getElementById('__medmind_toast');
    if (!el) {
      el = document.createElement('div');
      el.id = '__medmind_toast';
      document.body.appendChild(el);
    }
    const color = (type === 'error') ? ['#FEE2E2', '#991B1B', '#FECACA']
      : (type === 'success') ? ['#DCFCE7', '#15803D', '#86EFAC']
      : ['#FEF3C7', '#92400E', '#FDE68A'];
    el.style.cssText = 'position:fixed;top:18px;right:18px;z-index:99999;padding:11px 18px;border-radius:10px;font-size:13px;box-shadow:0 8px 24px rgba(0,0,0,.14);max-width:420px;background:' + color[0] + ';color:' + color[1] + ';border:1px solid ' + color[2] + ';';
    // 允许消息中包含受控的 HTML（由调用方保证输入安全），使用 innerHTML 以正确渲染如“去登录”超链接
    el.innerHTML = String(message);
    clearTimeout(el._timer);
    el._timer = setTimeout(() => { el.remove(); }, 4500);
  }

  // 服务可达性自检
  async function ping() {
    try {
      const r = await fetch(API_BASE.replace(/\/v1$/, '') + '/health');
      if (!r.ok) throw new Error('http ' + r.status);
      const d = await r.json();
      return { ok: true, version: d.version, llm: d.llm_provider };
    } catch (e) {
      return { ok: false, error: e.message };
    }
  }

  // 显示后端状态指示器
  async function mountStatusBadge(target) {
    const r = await ping();
    const badge = document.createElement('div');
    badge.id = '__medmind_status';
    badge.style.cssText = 'position:fixed;bottom:14px;right:14px;z-index:9999;padding:6px 12px;border-radius:99px;font-size:11px;display:flex;align-items:center;gap:6px;box-shadow:0 4px 14px rgba(0,0,0,.1);background:#fff;border:1px solid #E2E8F0;cursor:pointer;font-family:-apple-system,sans-serif';
    badge.innerHTML = '<span style="width:8px;height:8px;border-radius:50%;background:' + (r.ok ? '#10B981' : '#EF4444') + ';display:inline-block"></span>' +
      (r.ok ? '后端 v' + r.version + ' · LLM ' + r.llm : '后端未连接');
    badge.title = '点击查看 API 文档';
    badge.onclick = () => window.open(API_BASE.replace(/\/v1$/, '') + '/docs', '_blank');
    (target || document.body).appendChild(badge);
    return r;
  }

  global.MedMind = {
    API_BASE, ApiError, request, qs,
    Auth, Patients, Doctors, Departments,
    Triage, Records, Prescriptions, DRG,
    Research, Reports, Admin, Demo, WS,
    Appointments, Notifications,  // v3.6
    toast, ping, mountStatusBadge,
    setApiBase: (url) => { localStorage.setItem('MEDMIND_API_BASE', url); location.reload(); },
  };
})(window);
