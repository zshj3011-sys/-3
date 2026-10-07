/**
 * MedMind Nexus · 前端"渐进增强"接通后端 — v3.6
 *
 * 设计原则:
 *   1. 静态页保留原样, 后端不可达时页面仍可演示 (0 副作用)
 *   2. 后端可达时, 在原 UI 顶部注入"实时联通"标志, 加入真实 API 调用按钮
 *   3. 调用结果以追加卡片/toast 展示, 不破坏原版面
 *
 * 自动根据 location.pathname 识别页面并执行对应增强器。
 */
(function () {
  function ready(cb) {
    if (window.MedMind && window.MedMind.ping) cb();
    else setTimeout(() => ready(cb), 50);
  }

  function injectBadge(text, color) {
    const bar = document.createElement('div');
    bar.className = 'medmind-live-bar';
    bar.style.cssText = 'position:sticky;top:0;z-index:40;background:' + color +
      ';color:#fff;font-size:12px;padding:6px 18px;display:flex;align-items:center;gap:10px;font-weight:500';
    bar.innerHTML = '<span style="width:8px;height:8px;border-radius:50%;background:#10F0A8;display:inline-block"></span>' + text;
    document.body.insertBefore(bar, document.body.firstChild);
  }

  function injectAfter(elOrSel, html) {
    const el = (typeof elOrSel === 'string') ? document.querySelector(elOrSel) : elOrSel;
    if (!el) return null;
    const wrap = document.createElement('div');
    wrap.innerHTML = html;
    const node = wrap.firstElementChild;
    el.parentNode.insertBefore(node, el.nextSibling);
    return node;
  }

  function formatJson(o, max) {
    max = max || 1500;
    let s = JSON.stringify(o, null, 2);
    if (s.length > max) s = s.slice(0, max) + ' …';
    return s;
  }

  const ENHANCERS = {
    'doctor/diagnosis.html': async () => {
      const target = document.querySelector('.card');
      if (!target) return;
      injectAfter(target, '<div class="card" style="margin-top:14px;border:2px solid #0EA5A4">' +
        '<h3><span class="dot"></span> 🔴 实时联通后端 · POST /v1/reports/diagnose</h3>' +
        '<div style="display:flex;gap:8px;flex-wrap:wrap;margin-bottom:10px">' +
        '<button id="live-diag-btn" class="btn btn-primary btn-sm">⚡ 调用真实 AI 诊断辅助</button>' +
        '<span class="muted" style="font-size:12px;align-self:center">需以医生身份登录</span>' +
        '</div>' +
        '<pre id="live-diag-out" style="background:#0F172A;color:#A7F3D0;padding:12px;border-radius:8px;font-size:11px;max-height:280px;overflow:auto;margin:0;display:none"></pre>' +
        '</div>');
      document.getElementById('live-diag-btn').onclick = async function () {
        this.disabled = true; this.textContent = '调用中...';
        try {
          const r = await MedMind.Reports.diagnose({
            symptoms: ['胸痛', '胸闷', '左肩放射痛'],
            patient_age: 58, patient_gender: 'male',
            past_history: ['高血压', '高脂血症'],
          });
          const out = document.getElementById('live-diag-out');
          out.style.display = 'block'; out.textContent = formatJson(r);
          MedMind.toast('✅ AI 诊断辅助返回成功', 'success');
        } catch (e) {
          MedMind.toast('❌ ' + e.message + ' — 请用 dr_zhang/doctor123 登录', 'error');
        } finally {
          this.disabled = false; this.textContent = '⚡ 重新调用';
        }
      };
    },

    'doctor/quality.html': async () => {
      const target = document.querySelector('.card');
      if (!target) return;
      injectAfter(target, '<div class="card" style="margin-top:14px;border:2px solid #0EA5A4">' +
        '<h3><span class="dot"></span> 🔴 实时联通后端 · POST /v1/records/{id}/quality-check</h3>' +
        '<div style="display:flex;gap:8px;flex-wrap:wrap;margin-bottom:10px">' +
        '<input id="live-qc-id" placeholder="病历ID(默认1)" value="1" style="max-width:140px">' +
        '<button id="live-qc-btn" class="btn btn-primary btn-sm">⚡ 调用 AI 质控</button>' +
        '</div>' +
        '<pre id="live-qc-out" style="background:#0F172A;color:#A7F3D0;padding:12px;border-radius:8px;font-size:11px;max-height:280px;overflow:auto;margin:0;display:none"></pre>' +
        '</div>');
      document.getElementById('live-qc-btn').onclick = async function () {
        const id = +document.getElementById('live-qc-id').value || 1;
        this.disabled = true; this.textContent = '检查中...';
        try {
          const r = await MedMind.Records.qualityCheck(id);
          const out = document.getElementById('live-qc-out');
          out.style.display = 'block'; out.textContent = formatJson(r);
          MedMind.toast('✅ 质控完成', 'success');
        } catch (e) { MedMind.toast('❌ ' + e.message, 'error'); }
        finally { this.disabled = false; this.textContent = '⚡ 重新检查'; }
      };
    },

    'doctor/records.html': async () => {
      const target = document.querySelector('.card');
      if (!target) return;
      injectAfter(target, '<div class="card" style="margin-top:14px;border:2px solid #0EA5A4">' +
        '<h3><span class="dot"></span> 🔴 实时联通后端 · GET /v1/records</h3>' +
        '<button id="live-rec-btn" class="btn btn-primary btn-sm">⚡ 拉取后端真实病历</button>' +
        '<div id="live-rec-out" style="margin-top:10px"></div>' +
        '</div>');
      document.getElementById('live-rec-btn').onclick = async function () {
        this.disabled = true; this.textContent = '加载中...';
        try {
          const r = await MedMind.Records.list({ page: 1, size: 5 });
          const items = r.data || [];
          const html = items.length
            ? '<table style="width:100%;font-size:13px"><tr><th>ID</th><th>主诉</th><th>状态</th><th>AI辅助</th></tr>' +
              items.map(x => '<tr><td>#' + x.id + '</td><td>' + (x.chief_complaint || '—') +
                '</td><td><span class="tag green">' + x.status + '</span></td><td>' + (x.ai_assisted ? '✅' : '—') + '</td></tr>').join('') +
              '</table>'
            : '<div class="muted">暂无病历</div>';
          document.getElementById('live-rec-out').innerHTML = html;
          MedMind.toast('✅ 后端返回 ' + items.length + ' 份病历', 'success');
        } catch (e) { MedMind.toast('❌ ' + e.message, 'error'); }
        finally { this.disabled = false; this.textContent = '⚡ 重新拉取'; }
      };
    },

    'admin/quality.html': async () => {
      const target = document.querySelector('.card');
      if (!target) return;
      injectAfter(target, '<div class="card" style="margin-top:14px;border:2px solid #0EA5A4">' +
        '<h3><span class="dot"></span> 🔴 实时联通后端 · GET /v1/admin/quality</h3>' +
        '<button id="live-aq-btn" class="btn btn-primary btn-sm">⚡ 拉取实时质控指标</button>' +
        '<pre id="live-aq-out" style="background:#0F172A;color:#A7F3D0;padding:12px;border-radius:8px;font-size:11px;max-height:280px;overflow:auto;margin-top:10px;display:none"></pre>' +
        '</div>');
      document.getElementById('live-aq-btn').onclick = async function () {
        this.disabled = true; this.textContent = '加载中...';
        try {
          const r = await MedMind.Admin.quality();
          const out = document.getElementById('live-aq-out');
          out.style.display = 'block'; out.textContent = formatJson(r);
          MedMind.toast('✅ 实时质控数据拉取成功', 'success');
        } catch (e) { MedMind.toast('❌ ' + e.message, 'error'); }
        finally { this.disabled = false; this.textContent = '⚡ 重新拉取'; }
      };
    },

    'admin/ai-analytics.html': async () => {
      const target = document.querySelector('.card');
      if (!target) return;
      injectAfter(target, '<div class="card" style="margin-top:14px;border:2px solid #0EA5A4">' +
        '<h3><span class="dot"></span> 🔴 实时联通后端 · GET /v1/admin/ai-analytics</h3>' +
        '<button id="live-ai-btn" class="btn btn-primary btn-sm">⚡ 拉取 AI 使用统计</button>' +
        '<pre id="live-ai-out" style="background:#0F172A;color:#A7F3D0;padding:12px;border-radius:8px;font-size:11px;max-height:280px;overflow:auto;margin-top:10px;display:none"></pre>' +
        '</div>');
      document.getElementById('live-ai-btn').onclick = async function () {
        this.disabled = true; this.textContent = '加载中...';
        try {
          const r = await MedMind.Admin.aiAnalytics();
          const out = document.getElementById('live-ai-out');
          out.style.display = 'block'; out.textContent = formatJson(r);
          MedMind.toast('✅ AI 使用统计拉取成功', 'success');
        } catch (e) { MedMind.toast('❌ ' + e.message, 'error'); }
        finally { this.disabled = false; this.textContent = '⚡ 重新拉取'; }
      };
    },

    'research/grant.html': async () => {
      const target = document.querySelector('.card');
      if (!target) return;
      injectAfter(target, '<div class="card" style="margin-top:14px;border:2px solid #0EA5A4">' +
        '<h3><span class="dot"></span> 🔴 实时联通后端 · POST /v1/research/grant/generate</h3>' +
        '<div style="display:flex;gap:8px;margin-bottom:10px">' +
        '<input id="live-grant-topic" placeholder="研究主题" value="基于 RAG 的 ACS 早期识别系统" style="flex:1;min-width:240px">' +
        '<button id="live-grant-btn" class="btn btn-primary btn-sm">⚡ 生成标书章节</button>' +
        '</div>' +
        '<pre id="live-grant-out" style="background:#0F172A;color:#A7F3D0;padding:12px;border-radius:8px;font-size:11px;max-height:320px;overflow:auto;margin:0;display:none"></pre>' +
        '</div>');
      document.getElementById('live-grant-btn').onclick = async function () {
        this.disabled = true; this.textContent = '生成中...';
        try {
          const topic = document.getElementById('live-grant-topic').value;
          const r = await MedMind.Research.generateGrant({ topic, project_type: 'NSFC' });
          const out = document.getElementById('live-grant-out');
          out.style.display = 'block'; out.textContent = formatJson(r, 2500);
          MedMind.toast('✅ 标书生成完成', 'success');
        } catch (e) { MedMind.toast('❌ ' + e.message, 'error'); }
        finally { this.disabled = false; this.textContent = '⚡ 重新生成'; }
      };
    },

    'research/paper.html': async () => {
      const target = document.querySelector('.card');
      if (!target) return;
      injectAfter(target, '<div class="card" style="margin-top:14px;border:2px solid #0EA5A4">' +
        '<h3><span class="dot"></span> 🔴 实时联通后端 · POST /v1/research/paper/polish</h3>' +
        '<div style="display:flex;gap:8px;margin-bottom:10px;flex-direction:column">' +
        '<textarea id="live-polish-in" rows="3" style="width:100%">本研究纳入 200 例急性冠脉综合征患者, 对比传统模型与 AI 辅助模型的诊断准确率, 结果显示 AI 模型准确率明显提高。</textarea>' +
        '<button id="live-polish-btn" class="btn btn-primary btn-sm" style="align-self:flex-start">⚡ 调用 AI 润色</button>' +
        '</div>' +
        '<pre id="live-polish-out" style="background:#0F172A;color:#A7F3D0;padding:12px;border-radius:8px;font-size:11px;max-height:280px;overflow:auto;margin:0;display:none"></pre>' +
        '</div>');
      document.getElementById('live-polish-btn').onclick = async function () {
        this.disabled = true; this.textContent = '润色中...';
        try {
          const text = document.getElementById('live-polish-in').value;
          const r = await MedMind.Research.polishPaper(text);
          const out = document.getElementById('live-polish-out');
          out.style.display = 'block'; out.textContent = formatJson(r, 2500);
          MedMind.toast('✅ AI 润色完成', 'success');
        } catch (e) { MedMind.toast('❌ ' + e.message, 'error'); }
        finally { this.disabled = false; this.textContent = '⚡ 重新润色'; }
      };
    },

    'research/statistics.html': async () => {
      const target = document.querySelector('.card');
      if (!target) return;
      injectAfter(target, '<div class="card" style="margin-top:14px;border:2px solid #0EA5A4">' +
        '<h3><span class="dot"></span> 🔴 实时联通后端 · POST /v1/research/statistics/recommend</h3>' +
        '<div style="display:flex;gap:8px;margin-bottom:10px;flex-wrap:wrap">' +
        '<select id="live-stat-q" style="max-width:340px;flex:1">' +
        '<option value="比较两组ACS患者AI辅助前后的诊断准确率">两组比较 (率)</option>' +
        '<option value="冠脉支架术后5年生存率分析">生存分析</option>' +
        '<option value="HbA1c 与心血管事件的关联">连续变量相关性</option>' +
        '</select>' +
        '<button id="live-stat-btn" class="btn btn-primary btn-sm">⚡ 推荐统计方法</button>' +
        '</div>' +
        '<pre id="live-stat-out" style="background:#0F172A;color:#A7F3D0;padding:12px;border-radius:8px;font-size:11px;max-height:280px;overflow:auto;margin:0;display:none"></pre>' +
        '</div>');
      document.getElementById('live-stat-btn').onclick = async function () {
        this.disabled = true; this.textContent = '推荐中...';
        try {
          const research_question = document.getElementById('live-stat-q').value;
          const r = await MedMind.Research.recommendStats({ research_question });
          const out = document.getElementById('live-stat-out');
          out.style.display = 'block'; out.textContent = formatJson(r, 2500);
          MedMind.toast('✅ 统计方法推荐完成', 'success');
        } catch (e) { MedMind.toast('❌ ' + e.message, 'error'); }
        finally { this.disabled = false; this.textContent = '⚡ 重新推荐'; }
      };
    },
  };

  ready(async function () {
    const path = location.pathname.replace(/^.*\/web\//, '').replace(/^\//, '');
    let key = null;
    for (const k of Object.keys(ENHANCERS)) {
      if (path.endsWith(k)) { key = k; break; }
    }
    if (!key) return;

    const r = await MedMind.ping();
    if (!r.ok) {
      injectBadge('⚠ 后端未启动 · 页面以静态演示模式运行 — 启动后端后刷新即可看到"实时联通"卡片', '#92400E');
      return;
    }
    injectBadge('🟢 后端 v' + r.version + ' · LLM ' + r.llm + ' · 本页底部含"实时联通"卡片', '#0F766E');
    try { await ENHANCERS[key](); } catch (e) { console.error('[live-enhance]', e); }
  });
})();
