# Itinerary Planner

一个简单的行程管理服务，支持动态添加日程、查询/修改/删除行程，并在行程开始前通过 SMTP 邮件发送提醒。可用于会议、课程、待办等多种场景。

## 功能亮点
- REST API 管理行程：创建、查询、更新、删除。
- 支持自定义分类、地点、备注等信息。
- 可为单个行程配置邮件提醒，支持自定义提前分钟数。
- 后台轮询提醒调度器，自动触发邮件并防止重复发送。
- 使用 SQLite（默认）或自定义 `DATABASE_URL` 持久化数据。

## 快速开始
1. 进入项目目录并创建虚拟环境（可选）：
   ```bash
   cd itinerary_app
   python3 -m venv .venv
   source .venv/bin/activate
   ```
2. 安装依赖：
   ```bash
   pip install -r requirements.txt
   ```
3. 根据 `.env.example` 创建 `.env` 并填写邮箱服务器等配置：
   ```bash
   cp .env.example .env
   # 编辑 .env，填写 SMTP_HOST、SMTP_USERNAME 等
   ```
4. 启动服务：
   ```bash
   uvicorn app.main:app --reload
   ```
   打开浏览器访问 `http://127.0.0.1:8000/` 体验日历界面；Swagger 文档位于 `http://127.0.0.1:8000/docs`。

## API 示例
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
> 注意：时间字段需带时区信息，服务端会统一换算为 UTC 存储。

### 查询行程
```bash
curl "http://127.0.0.1:8000/events?start_after=2024-03-01T00:00:00Z&category=meeting"
```

### 更新行程
```bash
curl -X PATCH http://127.0.0.1:8000/events/1 \
  -H "Content-Type: application/json" \
  -d '{"location": "会议室 A"}'
```

### 删除行程
```bash
curl -X DELETE http://127.0.0.1:8000/events/1
```

### 按分类批量删除
```bash
curl -X DELETE "http://127.0.0.1:8000/events/by-category?category=meeting"
```
> 响应示例：`{"deleted": 3}` 表示删除了 3 条指定分类的行程。

### 按标题批量删除
```bash
curl -X DELETE "http://127.0.0.1:8000/events/by-title?title=产品评审会议"
```

## Web 日历界面
- 首页提供基于 FullCalendar 的视图，可在月视图/周视图/日视图/List 视图间切换。
- 点击空白日期快速创建行程，或使用右上角按钮打开完整表单。
- 单击已存在的日程可查看并编辑详细信息，可在对话框中删除。
- 在 List 视图中每一行提供“删除”快捷按钮，无需打开表单即可移除行程。
- 支持拖拽日程调整时间或拉伸修改持续时长，所有更改都会同步到后端 API。
- 表单支持填写分类、地点、备注以及邮件提醒信息，提交后自动以 UTC 储存。


## 邮件提醒说明
- 需提供可用的 SMTP 服务器信息，默认使用 TLS (`SMTP_USE_TLS=true`)；如使用 SSL，可将 `SMTP_USE_SSL=true` 并调整端口。
- `EMAIL_SENDER` 将作为邮件的 From 字段。如果未设置，会回退到 `SMTP_USERNAME` 或默认的 `no-reply@example.com`。
- `REMINDER_POLL_INTERVAL`（秒）可调整轮询频率，默认 60 秒。
- 系统会在提醒成功后将该行程标记为已发送，避免重复提醒；若修改行程或提醒信息，发送标记会被重置。

## 开发提示
- 数据库表会在应用启动时自动创建。
- 若需扩展事件类型、引入队列或多用户支持，可在 `app/models.py` 中扩展模型并在 `app/crud.py` 中调整逻辑。
- 目前的邮件发送使用同步 `smtplib`，通过 `asyncio.to_thread` 放入线程池；若需要更高吞吐量，可替换为异步邮件库或接入外部任务队列。

## 部署到阿里云服务器（Nginx 反向代理）

1. **准备服务器环境**（以 Ubuntu 为例）
   ```bash
   sudo apt update
   sudo apt install -y python3 python3-venv python3-pip nginx git rsync
   sudo ufw allow OpenSSH
   sudo ufw allow 'Nginx Full'
   sudo ufw enable   # 若尚未启用防火墙
   ```

2. **上传代码并初始化运行目录**
   ```bash
   sudo mkdir -p /opt/itinerary_app
   sudo chown -R $USER:$USER /opt/itinerary_app
   git clone <your-repo-url> /opt/itinerary_app
   cd /opt/itinerary_app
   python3 -m venv .venv
   source .venv/bin/activate
   pip install --upgrade pip
   pip install -r requirements.txt
   cp .env.example .env  # 根据需要填写 SMTP、数据库等配置
   ```

3. **启动 Uvicorn 服务**
   ```bash
   cd /opt/itinerary_app
   source .venv/bin/activate
   uvicorn app.main:app --host 127.0.0.1 --port 8000
   ```
   - 为了让进程在退出 SSH 后继续运行，可使用 `tmux`/`screen` 或 `nohup`：
     ```bash
     nohup uvicorn app.main:app --host 127.0.0.1 --port 8000 >/var/log/itinerary.log 2>&1 &
     ```

4. **配置 Nginx**
   - 将最简配置拷贝到 Nginx：
     ```bash
     sudo cp deploy/nginx.conf.simple /etc/nginx/sites-available/itinerary_app
     sudo nano /etc/nginx/sites-available/itinerary_app  # 修改 server_name、静态目录等
     ```
   - 建立软链并重载 Nginx：
     ```bash
     sudo ln -s /etc/nginx/sites-available/itinerary_app /etc/nginx/sites-enabled/itinerary_app
     sudo nginx -t
     sudo systemctl reload nginx
     ```

5. **部署更新**
   - 代码更新后执行：
     ```bash
     cd /opt/itinerary_app
     git pull
     source .venv/bin/activate
     pip install -r requirements.txt
     rsync -a app/static/ static/
     sudo systemctl reload nginx  # 若修改了 Nginx 配置
     ```

完成上述步骤后，Nginx 会把公网 80 端口的请求转发到本机 8000 端口的 Uvicorn 服务，实现快速访问。
