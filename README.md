# Itinerary Planner

一个简单的行程管理服务，支持动态添加日程、查询/修改/删除行程，并在行程开始前通过 SMTP 邮件发送提醒。

## ✨ 功能亮点
- REST API 管理行程：创建、查询、更新、删除
- 支持自定义分类、地点、备注等信息
- 可为单个行程配置邮件提醒，支持自定义提前分钟数
- 后台轮询提醒调度器，自动触发邮件并防止重复发送
- 使用 SQLite（默认）或自定义 `DATABASE_URL` 持久化数据

## 🚀 快速开始

### 本地开发
```bash
cd Calendar4me
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # 填写 SMTP 配置
uvicorn app.main:app --reload
```
访问 `http://127.0.0.1:8000/` 体验日历界面；API 文档位于 `http://127.0.0.1:8000/docs`

### 生产部署（阿里云）
```bash
# 一键部署
./quick-deploy.sh
```

## 📖 API 示例

### 创建行程
```bash
curl -X POST http://127.0.0.1:8000/events \
  -H "Content-Type: application/json" \
  -d '{
    "title": "产品评审会议",
    "description": "和市场、研发讨论需求范围",
    "category": "meeting",
    "location": "Zoom",
    "start_time": "2024-03-10T13:00:00+08:00",
    "end_time": "2024-03-10T14:00:00+08:00",
    "reminder_minutes_before": 30,
    "reminder_email": "me@example.com"
  }'
```

### 查询行程
```bash
curl "http://127.0.0.1:8000/events?start_after=2024-03-01T00:00:00Z&category=meeting"
```

### 更新/删除行程
```bash
curl -X PATCH http://127.0.0.1:8000/events/1 -H "Content-Type: application/json" -d '{"location": "会议室 A"}'
curl -X DELETE http://127.0.0.1:8000/events/1
```

### 批量删除
```bash
curl -X DELETE "http://127.0.0.1:8000/events/by-category?category=meeting"
curl -X DELETE "http://127.0.0.1:8000/events/by-title?title=产品评审会议"
```

## 🌐 Web 日历界面
- 基于 FullCalendar 的视图，支持月/周/日/列表视图切换
- 点击空白日期快速创建行程，或使用右上角按钮打开完整表单
- 单击已存在的日程可查看并编辑详细信息
- 支持拖拽调整时间或拉伸修改持续时长
- 表单支持填写分类、地点、备注以及邮件提醒信息

## 📧 邮件提醒说明
- 需提供可用的 SMTP 服务器信息，默认使用 TLS
- `EMAIL_SENDER` 将作为邮件的 From 字段
- `REMINDER_POLL_INTERVAL`（秒）可调整轮询频率，默认 60 秒
- 系统会在提醒成功后将该行程标记为已发送，避免重复提醒

## 🚨 部署常见问题

### 1. 端口配置错误
确保nginx配置中 `listen 80;`

### 2. 默认站点冲突
```bash
# sudo rm -f /etc/nginx/sites-enabled/default
sudo ln -sf /etc/nginx/sites-available/your_app /etc/nginx/sites-enabled/your_app
sudo systemctl reload nginx
```

### 3. 静态文件权限问题
**问题**：静态文件返回403 Forbidden，网页渲染异常
**问题**：没有权限
**解决**：
```bash
sudo mkdir -p /var/www/html/static
sudo cp -r app/static/* /var/www/html/static/
sudo sed -i 's|alias /root/path/static/;|alias /var/www/html/static/;|' /etc/nginx/sites-available/your_app
sudo systemctl reload nginx
```

### 4. 快速诊断
```bash
# 检查服务状态
sudo systemctl status nginx
ps aux | grep uvicorn
netstat -tlnp | grep :8000

# 测试访问
curl http://your-server-ip/
curl http://your-server-ip/static/styles.css

# 查看日志
sudo tail -f /var/log/nginx/error.log
tail -f /var/log/app.log
```

## ⚡ 快速部署脚本
使用 `quick-deploy.sh` 一键部署
```bash
./quick-deploy.sh
```

## 🔧 开发提示
- 数据库表会在应用启动时自动创建
- 若需扩展事件类型、引入队列或多用户支持，可在 `app/models.py` 中扩展模型
- 目前的邮件发送使用同步 `smtplib`，通过 `asyncio.to_thread` 放入线程池
