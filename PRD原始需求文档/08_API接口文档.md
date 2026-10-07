# API接口文档

## 1. 文档概述

本文档定义MedMind Nexus后端API接口规范，基于**OpenAPI 3.0**标准，支持**RESTful**风格。

**基础信息**：
- **Base URL**：`https://api.medmind-nexus.com/v1`（生产环境）
- **本地开发**：`http://localhost:8000/v1`
- **认证方式**：Bearer Token（JWT）
- **内容类型**：`application/json`

## 2. 认证与鉴权

### 2.1 登录认证

**POST /auth/login**

```yaml
summary: 用户登录
requestBody:
  required: true
  content:
    application/json:
      schema:
        type: object
        properties:
          username:
            type: string
            example: "dr_zhang"
          password:
            type: string
            format: password
            example: "encrypted_password"
          mfa_code:
            type: string
            description: "MFA验证码（如果启用2FA）"
            example: "123456"
responses:
  200:
    description: 登录成功
    content:
      application/json:
        schema:
          type: object
          properties:
            access_token:
              type: string
              example: "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
            refresh_token:
              type: string
            expires_in:
              type: integer
              example: 3600
  401:
    description: 用户名或密码错误
  403:
    description: MFA验证码错误
```

**示例请求**：
```bash
curl -X POST "https://api.medmind-nexus.com/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "dr_zhang",
    "password": "encrypted_password",
    "mfa_code": "123456"
  }'
```

**示例响应**：
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "b3JkZXJfaWQ6MzAw...",
  "expires_in": 3600,
  "token_type": "Bearer"
}
```

### 2.2 Token刷新

**POST /auth/refresh**

```yaml
summary: 刷新Token
requestBody:
  required: true
  content:
    application/json:
      schema:
        type: object
        properties:
          refresh_token:
            type: string
responses:
  200:
    description: Token刷新成功
  401:
    description: refresh_token无效或过期
```

### 2.3 登出

**POST /auth/logout**

```yaml
summary: 用户登出
security:
  - BearerAuth: []
responses:
  200:
    description: 登出成功，Token已失效
```

## 3. 患者管理API

### 3.1 创建患者档案

**POST /patients**

```yaml
summary: 创建患者档案
security:
  - BearerAuth: []
requestBody:
  required: true
  content:
    application/json:
      schema:
        type: object
        properties:
          real_name_encrypted:
            type: string
            description: "AES-256加密的患者姓名"
          id_card_encrypted:
            type: string
            description: "加密的身份证号"
          phone_encrypted:
            type: string
          birth_date:
            type: string
            format: date
            example: "1978-05-20"
          gender:
            type: string
            enum: ["男", "女", "其他"]
          allergy_history:
            type: array
            items:
              type: string
            example: ["青霉素", "磺胺类"]
          past_history:
            type: array
            items:
              type: string
            example: ["高血压", "糖尿病"]
responses:
  201:
    description: 患者档案创建成功
    content:
      application/json:
        schema:
          type: object
          properties:
            patient_id:
              type: string
              format: uuid
  400:
    description: 参数错误
  401:
    description: 未授权
```

### 3.2 查询患者列表

**GET /patients**

```yaml
summary: 查询患者列表（分页）
security:
  - BearerAuth: []
parameters:
  - name: page
    in: query
    schema:
      type: integer
      default: 1
  - name: "page_size"
    in: query
    schema:
      type: integer
      default: 20
      maximum: 100
  - name: "search"
    in: query
    description: "按姓名/身份证号搜索"
    schema:
      type: string"
  - name: "doctor_id"
    in: query
    description: "按主管医生筛选"
    schema:
      type: string
      format: uuid
responses:
  200:
    description: 查询成功
    content:
      application/json:
        schema:
          type: object
          properties:
            total:
              type: integer
            patients:
              type: array
              items:
                $ref: '#/components/schemas/Patient'
```

### 3.3 获取患者详情

**GET /patients/{patient_id}**

```yaml
summary: 获取患者详情
security:
  - BearerAuth: []
parameters:
  - name: patient_id
    in: path
    required: true
    schema:
      type: string
      format: uuid
responses:
  200:
    description: 查询成功
    content:
      application/json:
        schema:
          $ref: '#/components/schemas/PatientDetail'
  404:
    description: 患者不存在
  403:
    description: 无权访问该患者
```

## 4. AI预问诊API

### 4.1 启动预问诊会话

**POST /ai/pre-consultation/start**

```yaml
summary: 启动AI预问诊会话
security:
  - BearerAuth: []
requestBody:
  required: true
  content:
    application/json:
      schema:
        type: object
        properties:
          patient_id:
            type: string
            format: uuid
          department:
            type: string
            example: "心内科"
responses:
  200:
    description: 会话创建成功
    content:
      application/json:
        schema:
          type: object
          properties:
            session_id:
              type: string
              format: uuid
            first_question:
              type: string
              example: "您好！请描述您的症状。"
  500:
    description: AI服务异常
```

### 4.2 发送消息（多轮对话）

**POST /ai/pre-consultation/{session_id}/message**

```yaml
summary: 发送消息并获取AI回复
security:
  - BearerAuth: []
parameters:
  - name: session_id
    in: path
    required: true
    schema:
      type: string
      format: uuid
requestBody:
  required: true
  content:
    application/json:
      schema:
        type: object
        properties:
          message:
            type: string
            example: "我最近经常胸闷，尤其是活动后。"
          message_type:
            type: string
            enum: ["text", "voice"]
            default: "text"
responses:
  200:
    description: AI回复成功
    content:
      application/json:
        schema:
          type: object
          properties:
            reply:
              type: string
              example: "明白了。胸闷有多久了？是活动时加重还是休息时也有？"
            is_final:
              type: boolean
              description: "是否为最后一轮对话（采集完成）"
            summary:
              type: object
              description: "如果is_final=true，返回结构化摘要"
              properties:
                chief_complaint:
                  type: string
                history_present_illness:
                  type: string
                past_history:
                  type: array
                  items:
                    type: string
                medications:
                  type: array
                  items:
                    type: string
                allergies:
                  type: array
                  items:
                    type: string
                urgency_level:
                  type: string
                  enum: ["low", "medium", "high", "emergency"]
  400:
    description: 参数错误
```

**示例请求**：
```bash
curl -X POST "https://api.medmind-nexus.com/v1/ai/pre-consultation/{session_id}/message" \
  -H "Authorization: Bearer {access_token}" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "我最近经常胸闷，尤其是活动后。",
    "message_type": "text"
  }'
```

**示例响应**：
```json
{
  "reply": "明白了。胸闷有多久了？是活动时加重还是休息时也有？",
  "is_final": false,
  "summary": null
}
```

### 4.3 获取预问诊摘要

**GET /ai/pre-consultation/{session_id}/summary**

```yaml
summary: 获取预问诊结构化摘要
security:
  - BearerAuth: []
parameters:
  - name: session_id
    in: path
    required: true
    schema:
      type: string
      format: uuid
responses:
  200:
    description: 查询成功
    content:
      application/json:
        schema:
          type: object
          properties:
            summary:
              $ref: '#/components/schemas/PreConsultationSummary'
  404:
    description: 会话不存在或未完成
```

## 5. 病历管理API

### 5.1 AI生成病历草稿

**POST /ai/consultation/generate-note**

```yaml
summary: AI生成SOAP格式病历草稿
security:
  - BearerAuth: []
requestBody:
  required: true
  content:
    application/json:
      schema:
        type: object
        properties:
          patient_id:
            type: string
            format: uuid
          pre_consultation_id:
            type: string
            format: uuid
            description: "关联的预问诊会话ID"
          conversation:
            type: array
            items:
              type: object
              properties:
                role:
                  type: string
                  enum: ["doctor", "patient"]
                content:
                  type: string
          physical_exam:
            type: string
            description: "体格检查结果"
responses:
  200:
    description: 病历草稿生成成功
    content:
      application/json:
        schema:
          type: object
          properties:
            note_id:
              type: string
              format: uuid
            soap_note:
              type: object
              properties:
                subjective:
                  type: string
                objective:
                  type: string
                assessment:
                  type: array
                  items:
                    type: object
                    properties:
                      icd10:
                        type: string
                      diagnosis:
                        type: string
                      probability:
                        type: number
                plan:
                  type: string
            confidence_score:
              type: number
              format: float
              description: "AI置信度 0-1"
  202:
    description: 正在生成中，请轮询
    content:
      application/json:
        schema:
          type: object
          properties:
            task_id:
              type: string
              format: uuid
            status_url:
              type: string
              example: "/ai/tasks/{task_id}"
```

### 5.2 保存病历

**POST /medical-records**

```yaml
summary: 保存病历（新建或更新）
security:
  - BearerAuth: []
requestBody:
  required: true
  content:
    application/json:
      schema:
        type: object
        properties:
          patient_id:
            type: string
            format: uuid
          note_id:
            type: string
            format: uuid
            description: "AI生成的草稿ID（如果有）"
          soap_note:
            type: object
            properties:
              subjective:
                type: string
              objective:
                type: string
              assessment:
                type: string
              plan:
                type: string
          icd10_codes:
            type: array
            items:
              type: string
            example: ["I20.0", "E11.9"]
          status:
            type: string
            enum: ["draft", "completed", "signed"]
responses:
  201:
    description: 病历保存成功
  400:
    description: 参数错误
  401:
    description: 未授权
```

### 5.3 病历质控检查

**POST /ai/medical-records/quality-check**

```yaml
summary: AI病历质控检查
security:
  - BearerAuth: []
requestBody:
  required: true
  content:
    application/json:
      schema:
        type: object
        properties:
          medical_record_id:
            type: string
            format: uuid
          soap_note:
            type: object
            description: "如果还未保存，直接传SOAP内容"
responses:
  200:
    description: 质控检查完成
    content:
      application/json:
        schema:
          type: object
          properties:
            passed:
              type: boolean
            issues:
              type: array
              items:
                type: object
                properties:
                  field:
                    type: string
                    example: "assessment"
                  severity:
                    type: string
                    enum: ["high", "medium", "low"]
                  message:
                    type: string
                  suggestion:
                    type: string
            overall_quality_score:
              type: number
              format: float
              description: "0-1，质量评分"
```

## 6. 处方管理API

### 6.1 AI辅助开方

**POST /ai/prescriptions/suggest**

```yaml
summary: AI根据诊断建议处方
security:
  - BearerAuth: []
requestBody:
  required: true
  content:
    application/json:
      schema:
        type: object
        properties:
          patient_id:
            type: string
            format: uuid
          diagnosis:
            type: array
            items:
              type: string
            example: ["I20.0 不稳定型心绞痛", "E11.9 2型糖尿病"]
          allergy_history:
            type: array
            items:
              type: string
responses:
  200:
    description: 处方建议生成成功
    content:
      application/json:
        schema:
          type: object
          properties:
            suggestions:
              type: array
              items:
                type: object
                properties:
                  drug_name:
                    type: string
                  dosage:
                    type: string
                  frequency:
                    type: string
                  duration:
                    type: string
                  reason:
                    type: string
                  contraindications:
                    type: array
                    items:
                      type: string
```

### 6.2 处方审核

**POST /ai/prescriptions/audit**

```yaml
summary: AI审核处方合理性
security:
  - BearerAuth: []
requestBody:
  required: true
  content:
    application/json:
      schema:
        type: object
        properties:
          prescription_id:
            type: string
            format: uuid
          medications:
            type: array
            items:
              type: object
              properties:
                drug_name:
                  type: string
                dosage:
                  type: string
                frequency:
                  type: string
          patient_allergies:
            type: array
            items:
              type: string
responses:
  200:
    description: 审核完成
    content:
      application/json:
        schema:
          type: object
          properties:
            passed:
              type: boolean
            alerts:
              type: array
              items:
                type: object
                properties:
                  severity:
                    type: string
                    enum: ["high", "medium", "low"]
                  message:
                    type: string
                  suggestion:
                    type: string
```

## 7. DRG控费API

### 7.1 DRG分组预测

**POST /ai/drg/predict**

```yaml
summary: 预测DRG分组和费用
security:
  - BearerAuth: []
requestBody:
  required: true
  content:
    application/json:
      schema:
        type: object
        properties:
          patient_id:
            type: string
            format: uuid
          admission_id:
            type: string
          main_diagnosis_icd10:
            type: string
            example: "I21.0"
          procedures:
            type: array
            items:
              type: string
            example: ["00.66", "36.06"]
          age:
            type: integer
          gender:
            type: string
          admission_source:
            type: string
            example: "急诊"
responses:
  200:
    description: 预测成功
    content:
      application/json:
        schema:
          type: object
          properties:
            predicted_drg_code:
              type: string
              example: "CV1"
            predicted_drg_name:
              type: string
              example: "心血管介入"
            predicted_cost:
              type: number
              format: float
            drg_quota:
              type: number
              format: float
              description: "本市该病种定额"
            profit_loss:
              type: number
              format: float
              description: "预期盈亏 = 定额 - 预测费用"
```

### 7.2 费用预警

**GET /ai/drg/cost-alert**

```yaml
summary: 获取在院患者的费用预警列表
security:
  - BearerAuth: []
parameters:
  - name: department_id
    in: query
    description: "科室ID（不传则查全院）"
    schema:
      type: string
      format: uuid
  - name: alert_level
    in: query
    description: "预警级别筛选"
    schema:
      type: string
      enum: ["red", "yellow", "green"]
responses:
  200:
    description: 查询成功
    content:
      application/json:
        schema:
          type: object
          properties:
            alerts:
              type: array
              items:
                type: object
                properties:
                  patient_id:
                    type: string
                    format: uuid
                  patient_name:
                    type: string
                  department:
                    type: string
                  cost_ratio:
                    type: number
                    format: float
                    description: "费用进度（实际费用/DRG定额）"
                  alert_level:
                    type: string
                    enum: ["red", "yellow", "green"]
                  suggestion:
                    type: string
```

## 8. 科研端API

### 8.1 文献检索

**POST /ai/research/literature-search**

```yaml
summary: AI智能文献检索
security:
  - BearerAuth: []
requestBody:
  required: true
  content:
    application/json:
      schema:
        type: object
        properties:
          query:
            type: string
            example: "冠心病 免疫治疗 最新进展"
          databases:
            type: array
            items:
              type: string
              enum: ["pubmed", "cnki", "cochrane", "arxiv"]
            default: ["pubmed", "cnki"]
          year_range:
            type: array
            items:
              type: integer
            example: [2022, 2026]
          max_results:
            type: integer
            default: 100
responses:
  200:
    description: 检索成功
    content:
      application/json:
        schema:
          type: object
          properties:
            total_count:
              type: integer
            papers:
              type: array
              items:
                type: object
                properties:
                  pmid:
                    type: string
                  title:
                    type: string
                  authors:
                    type: array
                    type: string
                  journal:
                    type: string
                  publication_date:
                    type: string
                    format: date
                  abstract:
                    type: string
                  ai_summary:
                    type: string
                    description: "AI生成的摘要"
```

### 8.2 标书生成

**POST /ai/research/proposal/generate**

```yaml
summary: AI生成基金标书初稿
security:
  - BearerAuth: []
requestBody:
  required: true
  content:
    application/json:
      schema:
        type: object
        properties:
          proposal_type:
            type: string
            enum: ["nsfc", "clinical_trial", "observational"]
          user_idea:
            type: string
            description: "用户的初步研究想法"
          research_team:
            type: array
            items:
              type: string
            description: "研究团队成员（用于生成研究基础）"
responses:
  200:
    description: 标书生成成功
    content:
      application/json:
        schema:
          type: object
          properties:
            proposal_id:
              type: string
              format: uuid
            content:
              type: string
              description: "Markdown格式的标书全文"
            quality_score:
              type: number
              format: float
              description: "AI质量评分（0-10）"
  202:
    description: 正在生成中，请轮询
```

## 9. WebSocket实时接口

### 9.1 语音转写实时流

**WS /ws/asr/stream**

```yaml
summary: 实时语音转写（WebSocket）
security:
  - BearerAuth: []
events:
  - type: "audio_chunk"
    description: "客户端发送音频块（每2秒发送一次）"
    payload:
      type: "binary"
      description: "音频数据（WebM/Opus格式）"
  
  - type: "transcript_result"
    description: "服务端返回转写结果"
    payload:
      type: "json"
      schema:
        type: object
        properties:
          role:
            type: string
            enum: ["doctor", "patient"]
          text:
            type: string
          timestamp:
            type: number
            format: float
          is_final:
            type: boolean
            description: "是否为该音频块的最终结果"
```

**示例交互**：
```
Client → Server: (Binary) 音频数据块1（2秒）
Server → Client: {"role": "patient", "text": "我最近经常胸闷", "timestamp": 1717567200.123, "is_final": true}

Client → Server: (Binary) 音频数据块2（2秒）
Server → Client: {"role": "doctor", "text": "胸闷有多久了？", "timestamp": 1717567202.456, "is_final": true}
```

### 9.2 AI建议实时推送

**WS /ws/ai/suggestions**

```yaml
summary: AI实时诊断建议推送（WebSocket）
security:
  - BearerAuth: []
events:
  - type: "suggestion_update"
    description: "服务端推送AI实时建议"
    payload:
      type: "json"
      schema:
        type: object
        properties:
          type:
            type: string
            enum: ["diagnosis", "drug_interaction", "guideline"]
          content:
            type: string
          confidence:
            type: number
            format: float
```

## 10. 错误码定义

| HTTP状态码 | 错误码 | 说明 | 处理建议 |
|-----------|--------|------|----------|
| 400 | BAD_REQUEST | 请求参数错误 | 检查请求参数格式 |
| 401 | UNAUTHORIZED | 未授权（Token无效/过期） | 重新登录获取Token |
| 403 | FORBIDDEN | 无权访问（权限不足） | 检查用户角色权限 |
| 404 | NOT_FOUND | 资源不存在 | 检查资源ID是否正确 |
| 409 | CONFLICT | 资源冲突（如重复创建） | 检查是否已存在 |
| 422 | UNPROCESSABLE_ENTITY | 参数验证失败 | 检查参数值和类型 |
| 429 | TOO_MANY_REQUESTS | 请求频率超限 | 降低请求频率，使用指数退避重试 |
| 500 | INTERNAL_ERROR | 服务器内部错误 | 联系技术支持 |
| 503 | SERVICE_UNAVAILABLE | 服务不可用（AI服务异常） | 稍后重试 |

## 11. 通用响应格式

### 11.1 成功响应

```json
{
  "code": 200,
  "message": "success",
  "data": {
    // 业务数据
  },
  "request_id": "req_12345",
  "timestamp": "2026-06-03T12:00:00Z"
}
```

### 11.2 错误响应

```json
{
  "code": 401,
  "message": "UNAUTHORIZED",
  "errors": [
    {
      "field": "access_token",
      "message": "Token已过期"
    }
  ],
  "request_id": "req_12345",
  "timestamp": "2026-06-03T12:00:00Z"
}
```

---

> **交付说明**：本文档定义了MedMind Nexus的全部后端API接口，可直接用于前后端联调和接口测试。作为练手项目，你可以优先实现"患者管理+AI预问诊+病历生成"这三个核心API（MVP）。
