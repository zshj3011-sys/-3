// utils/demo.js · 离线 demo 数据(后端不可达时使用)

const demoDepartments = [
  { id: 1, name: '心血管内科', code: 'cardio', icon: '❤️', desc: '高血压·冠心病·心律失常' },
  { id: 2, name: '消化内科', code: 'gastro', icon: '🫁', desc: '胃炎·肝病·胆囊炎' },
  { id: 3, name: '呼吸内科', code: 'resp', icon: '🌬️', desc: '哮喘·肺炎·慢阻肺' },
  { id: 4, name: '内分泌科', code: 'endo', icon: '🩸', desc: '糖尿病·甲状腺·肥胖' },
  { id: 5, name: '神经内科', code: 'neuro', icon: '🧠', desc: '头痛·脑卒中·癫痫' },
  { id: 6, name: '皮肤科', code: 'derma', icon: '🧴', desc: '湿疹·痤疮·脱发' },
  { id: 7, name: '眼科', code: 'eye', icon: '👁️', desc: '近视·白内障·干眼症' },
  { id: 8, name: '骨科', code: 'ortho', icon: '🦴', desc: '骨折·关节炎·腰椎间盘' },
]

const demoTriageReplies = {
  start: {
    session_id: 'demo-session-001',
    reply: '您好,我是 AI 预问诊助手。听到您说"头痛 3 天伴发热",我需要进一步了解一些情况。\n\n请问头痛的具体位置在哪?是整个头部、太阳穴、还是后脑勺?',
    options: ['整个头部', '太阳穴', '后脑勺', '前额'],
    round: 1,
  },
  rounds: [
    {
      reply: '好的,前额痛。请问体温最高到了多少度?是否伴有怕冷?',
      options: ['37.5-38℃', '38-39℃', '超过 39℃', '伴有寒战'],
    },
    {
      reply: '了解。除了头痛和发热,有没有以下症状?',
      options: ['鼻塞流涕', '咽痛咳嗽', '恶心呕吐', '全身肌肉酸痛'],
    },
    {
      reply: '最近有去过人流密集的地方吗?家里有人感冒吗?',
      options: ['有,周围有人感冒', '没有', '不确定'],
    },
    {
      reply: '感谢您提供的信息,我已经收集到足够内容。AI 初步建议如下,请医生最终判断。',
      options: [],
      finished: true,
    },
  ],
  summary: {
    chief_complaint: '头痛 3 天伴发热',
    history: 'HPI: 患者 3 天前无明显诱因出现前额钝痛, 伴体温 38.2℃, 鼻塞流涕, 周围有人感冒。',
    suggested_dept: '呼吸内科 / 全科',
    urgency: 'low',
    possible_diagnoses: ['普通感冒', '上呼吸道感染', '流行性感冒'],
    suggested_tests: ['血常规', '甲乙流抗原', 'C 反应蛋白'],
    warning: '若 24 小时内出现高热 (≥39.5℃)、剧烈头痛、意识改变、颈项强直, 请立即急诊。',
  },
}

const demoReportInterpret = {
  report_type: '血常规',
  abnormal_items: [
    { name: '白细胞', value: '12.5', unit: '×10⁹/L', ref: '4.0-10.0', flag: 'high', explain: '白细胞升高,常见于细菌感染。' },
    { name: '中性粒细胞%', value: '82.3', unit: '%', ref: '50-70', flag: 'high', explain: '中性粒细胞比例增高,支持细菌感染。' },
  ],
  ai_summary: '本次血常规提示白细胞和中性粒细胞均升高,符合细菌感染表现,结合您头痛发热的症状,建议医生评估是否需要抗生素治疗。',
  suggestions: ['多休息, 多饮水', '体温超过 38.5℃ 可口服布洛芬', '如 3 天未好转, 复诊'],
  disclaimer: '本解读仅供参考,最终诊断以医生为准。',
}

const demoMeds = [
  { id: 1, name: '布洛芬缓释胶囊', dose: '0.3g', freq: '每 12 小时 1 次', startDate: '2026-06-10', remain: 12, nextAlarm: '今晚 20:00' },
  { id: 2, name: '阿莫西林胶囊', dose: '0.5g', freq: '每 8 小时 1 次', startDate: '2026-06-10', remain: 18, nextAlarm: '今晚 18:00' },
]

const demoHealthArchive = {
  name: '李女士',
  age: 35,
  sex: '女',
  blood_type: 'A+',
  allergies: ['青霉素'],
  chronic: [],
  recent_visits: [
    { date: '2026-06-10', dept: '呼吸内科', doctor: '张医生', diagnosis: '上呼吸道感染' },
    { date: '2026-03-15', dept: '体检中心', doctor: '——', diagnosis: '健康' },
  ],
  reports: 5,
  prescriptions: 3,
}

module.exports = {
  demoDepartments,
  demoTriageReplies,
  demoReportInterpret,
  demoMeds,
  demoHealthArchive,
}
