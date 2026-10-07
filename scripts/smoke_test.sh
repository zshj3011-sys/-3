#!/usr/bin/env bash
# MedMind Nexus 联调冒烟测试脚本
# 用途: 启动后端后, 一键验证所有核心 API 是否真实可用
# 使用: bash scripts/smoke_test.sh [BASE_URL]
set -e

BASE_URL="${1:-http://localhost:8000}"
PASS=0
FAIL=0

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

check() {
  local name="$1"
  local cmd="$2"
  local expect="$3"
  echo -n "  → $name ... "
  local result
  result=$(eval "$cmd" 2>&1) || true
  if echo "$result" | grep -q "$expect"; then
    echo -e "${GREEN}✓${NC}"
    PASS=$((PASS+1))
  else
    echo -e "${RED}✗${NC}"
    echo "    expected: $expect"
    echo "    got:      ${result:0:200}"
    FAIL=$((FAIL+1))
  fi
}

echo -e "${YELLOW}=== MedMind Nexus 冒烟测试 (BASE_URL=$BASE_URL) ===${NC}"

# 1. 健康检查
echo "[1/7] 系统层"
check "GET /health" "curl -s $BASE_URL/health" '"status":"ok"'
check "GET /docs (Swagger)" "curl -s -o /dev/null -w '%{http_code}' $BASE_URL/docs" "200"
check "GET /web/sitemap.html" "curl -s -o /dev/null -w '%{http_code}' $BASE_URL/web/sitemap.html" "200"

# 2. 登录
echo "[2/7] 认证"
LOGIN_RESP=$(curl -s -X POST $BASE_URL/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"dr_zhang","password":"doctor123"}')
TOKEN=$(echo "$LOGIN_RESP" | python3 -c "import sys,json;print(json.load(sys.stdin)['data']['access_token'])" 2>/dev/null || echo "")

if [ -n "$TOKEN" ]; then
  echo -e "  → 登录拿 token ... ${GREEN}✓${NC}"
  PASS=$((PASS+1))
else
  echo -e "  → 登录拿 token ... ${RED}✗${NC}"
  echo "    $LOGIN_RESP"
  FAIL=$((FAIL+1))
  exit 1
fi

check "GET /v1/auth/me" "curl -s $BASE_URL/v1/auth/me -H 'Authorization: Bearer $TOKEN'" '"username":"dr_zhang"'

# 3. 基础资源
echo "[3/7] 基础资源"
check "GET /v1/patients" "curl -s $BASE_URL/v1/patients/?page=1\&size=5 -H 'Authorization: Bearer $TOKEN'" '"real_name"'
check "GET /v1/departments" "curl -s $BASE_URL/v1/departments/ -H 'Authorization: Bearer $TOKEN'" '"name"'
check "GET /v1/doctors" "curl -s $BASE_URL/v1/doctors/ -H 'Authorization: Bearer $TOKEN'" '"data"'

# 4. AI 能力
echo "[4/7] AI 能力"
check "POST /v1/reports/diagnose" \
  "curl -s -X POST $BASE_URL/v1/reports/diagnose -H 'Content-Type: application/json' -d '{\"chief_complaint\":\"胸痛\",\"symptoms\":[\"胸痛\"],\"age\":58}'" \
  '"primary_diagnosis"'

check "POST /v1/drg/predict" \
  "curl -s -X POST $BASE_URL/v1/drg/predict -H 'Authorization: Bearer $TOKEN' -H 'Content-Type: application/json' -d '{\"primary_diagnosis\":\"不稳定型心绞痛\",\"icd10\":\"I20.0\",\"actual_cost\":42000}'" \
  '"drg_code"'

check "POST /v1/research/literature/search" \
  "curl -s -X POST $BASE_URL/v1/research/literature/search -H 'Authorization: Bearer $TOKEN' -H 'Content-Type: application/json' -d '{\"query\":\"SGLT2\"}'" \
  '"results"'

check "POST /v1/research/grant/generate" \
  "curl -s -X POST $BASE_URL/v1/research/grant/generate -H 'Authorization: Bearer $TOKEN' -H 'Content-Type: application/json' -d '{\"title\":\"心衰研究\",\"grant_type\":\"面上项目\"}'" \
  '"sections"'

# 5. 管理端
echo "[5/7] 管理端"
check "GET /v1/admin/dashboard" "curl -s $BASE_URL/v1/admin/dashboard -H 'Authorization: Bearer $TOKEN'" '"kpis"'
check "GET /v1/admin/quality" "curl -s $BASE_URL/v1/admin/quality -H 'Authorization: Bearer $TOKEN'" '"data"'
check "GET /v1/drg/dashboard" "curl -s $BASE_URL/v1/drg/dashboard -H 'Authorization: Bearer $TOKEN'" '"data"'

# 6. 演示数据
echo "[6/7] 演示数据"
check "GET /v1/demo/wechat-screens" "curl -s $BASE_URL/v1/demo/wechat-screens" '"data"'

# 7. v3.4/v3.6 新增端点 + PRD 兼容路径
echo "[7/8] v3.4 新增 + PRD 兼容路由"
check "POST /v1/prescriptions/suggest (AI 辅助开方)" \
  "curl -s -X POST $BASE_URL/v1/prescriptions/suggest -H 'Authorization: Bearer $TOKEN' -H 'Content-Type: application/json' -d '{\"diagnosis\":[\"I20.0\"],\"patient_age\":58}'" \
  '"suggestions"'

check "POST /v1/ai/prescriptions/suggest (PRD 兼容)" \
  "curl -s -X POST $BASE_URL/v1/ai/prescriptions/suggest -H 'Authorization: Bearer $TOKEN' -H 'Content-Type: application/json' -d '{\"diagnosis\":[\"I20.0\"]}'" \
  '"suggestions"'

check "GET /v1/drg/cost-alert (DRG 费用预警)" \
  "curl -s $BASE_URL/v1/drg/cost-alert -H 'Authorization: Bearer $TOKEN'" \
  '"alerts"'

check "GET /v1/ai/drg/cost-alert?alert_level=red (PRD 兼容+筛选)" \
  "curl -s '$BASE_URL/v1/ai/drg/cost-alert?alert_level=red' -H 'Authorization: Bearer $TOKEN'" \
  '"summary"'

check "POST /v1/ai/pre-consultation/start (PRD 兼容预问诊)" \
  "curl -s -X POST $BASE_URL/v1/ai/pre-consultation/start -H 'Authorization: Bearer $TOKEN' -H 'Content-Type: application/json' -d '{\"chief_complaint\":\"头痛\"}'" \
  '"session_id"'

# 8. v3.6 新增端点 - 挂号 / 消息通知 / PRD 字面路径
echo "[8/9] v3.6 新增端点 (挂号 + 消息 + PRD 字面路径)"
check "POST /v1/ai/consultation/generate-note (PRD §5.1 字面路径)" \
  "curl -s -X POST $BASE_URL/v1/ai/consultation/generate-note -H 'Authorization: Bearer $TOKEN' -H 'Content-Type: application/json' -d '{\"patient_id\":1,\"transcript\":\"胸痛3天\"}'" \
  '"code"'

check "POST /v1/ai/pre-consultation/{sid}/message (PRD §4.2 路径参数式)" \
  "SID=\$(curl -s -X POST $BASE_URL/v1/ai/pre-consultation/start -H 'Content-Type: application/json' -d '{\"chief_complaint\":\"咳嗽\"}' | python3 -c 'import json,sys;print(json.load(sys.stdin)[\"data\"][\"session_id\"])'); curl -s -X POST $BASE_URL/v1/ai/pre-consultation/\$SID/message -H 'Content-Type: application/json' -d '{\"session_id\":\"'\$SID'\",\"message\":\"咳嗽3天\"}'" \
  '"step"'

check "GET /v1/appointments (挂号列表)" \
  "curl -s $BASE_URL/v1/appointments/ -H 'Authorization: Bearer $TOKEN'" \
  '"meta"'

check "GET /v1/appointments/today (今日预约)" \
  "curl -s $BASE_URL/v1/appointments/today -H 'Authorization: Bearer $TOKEN'" \
  '"code"'

check "GET /v1/appointments/slots (可用号源)" \
  "curl -s $BASE_URL/v1/appointments/slots -H 'Authorization: Bearer $TOKEN'" \
  '"remaining"'

# 患者帐号特有的消息通知测试
PATIENT_TOKEN=$(curl -s -X POST $BASE_URL/v1/auth/login -H 'Content-Type: application/json' -d '{"username":"patient_li","password":"patient123"}' | python3 -c 'import json,sys;print(json.load(sys.stdin)["data"]["access_token"])')

check "GET /v1/notifications (我的消息)" \
  "curl -s $BASE_URL/v1/notifications/ -H 'Authorization: Bearer $PATIENT_TOKEN'" \
  '"meta"'

check "GET /v1/notifications/unread-count (未读计数)" \
  "curl -s $BASE_URL/v1/notifications/unread-count -H 'Authorization: Bearer $PATIENT_TOKEN'" \
  '"by_category"'

# 9. v3.6.2 新增端点 - 安全事件 + 科研数据导入 (PRD §07 #139/#165)
echo "[9/9] v3.6.2 PRD §07 #139 #165 (Must·V1.0) 补齐项"

ADMIN_TOKEN=$(curl -s -X POST $BASE_URL/v1/auth/login -H 'Content-Type: application/json' -d '{"username":"admin","password":"admin123"}' | python3 -c 'import json,sys;print(json.load(sys.stdin)["data"]["access_token"])')
RESEARCHER_TOKEN=$(curl -s -X POST $BASE_URL/v1/auth/login -H 'Content-Type: application/json' -d '{"username":"prof_zhao","password":"researcher123"}' | python3 -c 'import json,sys;print(json.load(sys.stdin)["data"]["access_token"])')

check "GET /v1/safety-events (安全事件列表)" \
  "curl -s $BASE_URL/v1/safety-events/ -H 'Authorization: Bearer $ADMIN_TOKEN'" \
  '"meta"'

check "GET /v1/safety-events/stats (统计聚合)" \
  "curl -s $BASE_URL/v1/safety-events/stats -H 'Authorization: Bearer $ADMIN_TOKEN'" \
  '"by_status"'

check "POST /v1/safety-events (上报新事件)" \
  "curl -s -X POST $BASE_URL/v1/safety-events/ -H 'Authorization: Bearer $TOKEN' -H 'Content-Type: application/json' -d '{\"event_type\":\"other\",\"severity\":\"iv\",\"title\":\"smoke 测试\",\"description\":\"smoke 测试上报\",\"occurred_at\":\"2026-06-13T10:00:00\"}'" \
  '"reported"'

check "GET /v1/research/datasets (我的数据集)" \
  "curl -s $BASE_URL/v1/research/datasets/ -H 'Authorization: Bearer $RESEARCHER_TOKEN'" \
  '"meta"'

# CSV 上传
TMP_CSV=$(mktemp /tmp/smoke_XXXXXX.csv)
printf 'a,b\n1,foo\n2,bar\n' > $TMP_CSV
check "POST /v1/research/datasets/upload (CSV 上传)" \
  "curl -s -X POST $BASE_URL/v1/research/datasets/upload -H 'Authorization: Bearer $RESEARCHER_TOKEN' -F file=@$TMP_CSV -F name=smoke-csv" \
  '"schema"'
rm -f $TMP_CSV

# 总结
echo ""
echo "============================================="
echo -e "  通过: ${GREEN}$PASS${NC} · 失败: ${RED}$FAIL${NC}"
echo "============================================="

[ $FAIL -eq 0 ] && echo -e "${GREEN}🎉 全部通过, 系统健康${NC}" || (echo -e "${RED}❌ 有失败用例${NC}"; exit 1)
