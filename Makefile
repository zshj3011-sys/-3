# MedMind Nexus 项目快捷命令
# Usage: make <target>

.PHONY: help install run test smoke clean docker docker-up docker-down lint

help:	## 显示帮助
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-15s\033[0m %s\n", $$1, $$2}'

install:	## 安装后端依赖
	cd medmind-backend && pip install -r requirements.txt

run:	## 启动后端 (开发模式 + 热重载)
	cd medmind-backend && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

test:	## 运行 pytest (53 个用例)
	cd medmind-backend && pytest tests/ -v

smoke:	## 联调冒烟测试 (33 项 API，需后端已在 :8000 运行)
	bash scripts/smoke_test.sh http://localhost:8000

seed:	## 重新播种演示数据
	cd medmind-backend && rm -f data/medmind.db && python -m scripts.seed

clean:	## 清理临时文件
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	rm -f medmind-backend/data/medmind.db medmind-backend/test_medmind.db

docker:	## 构建 Docker 镜像
	cd medmind-backend && docker build -t medmind-backend:latest .

docker-up:	## 启动 docker compose (后端 + PG + Redis)
	cd medmind-backend && docker compose up -d

docker-down:	## 关闭 docker compose
	cd medmind-backend && docker compose down

lint:	## 代码风格检查 (需先 pip install ruff)
	cd medmind-backend && ruff check app/ tests/ || true

stats:	## 项目代码量统计
	@echo "=== 后端 Python ==="
	@find medmind-backend -name "*.py" -type f | xargs wc -l | tail -1
	@echo "=== 前端 HTML/CSS/JS ==="
	@find MedMindNexus -type f \( -name "*.html" -o -name "*.css" -o -name "*.js" \) | xargs wc -l | tail -1
	@echo "=== 微信小程序 ==="
	@find wechat-miniprogram -type f \( -name "*.js" -o -name "*.wxml" -o -name "*.wxss" -o -name "*.json" \) | xargs wc -l | tail -1
	@echo "=== 测试 ==="
	@find medmind-backend/tests -name "*.py" | xargs wc -l | tail -1

all: install seed test smoke	## 一键全流程: 安装→播种→测试→冒烟
