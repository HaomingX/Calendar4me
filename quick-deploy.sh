#!/bin/bash

set -e

echo "🚀 开始快速部署 Itinerary Planner..."

# 1. 停止可能运行的应用
echo "📋 停止现有应用..."
pkill -f uvicorn || true

# 2. 禁用nginx默认站点
echo "📋 配置nginx..."
sudo rm -f /etc/nginx/sites-enabled/default

# 3. 创建nginx配置
echo "📋 创建nginx配置..."
sudo tee /etc/nginx/sites-available/itinerary_app > /dev/null << 'NGINX_EOF'
server {
    listen 80;
    server_name _;
    
    client_max_body_size 10M;
    
    # 静态文件
    location /static/ {
        alias /var/www/html/static/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
    
    # 主应用代理
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
}
NGINX_EOF

# 4. 启用站点配置
sudo ln -sf /etc/nginx/sites-available/itinerary_app /etc/nginx/sites-enabled/itinerary_app

# 5. 复制静态文件
echo "📋 复制静态文件..."
sudo mkdir -p /var/www/html/static
sudo cp -r app/static/* /var/www/html/static/

# 6. 测试并重载nginx
echo "📋 重载nginx..."
sudo nginx -t
sudo systemctl reload nginx

# 7. 启动应用
echo "📋 启动应用..."
source .venv/bin/activate
nohup uvicorn app.main:app --host 0.0.0.0 --port 8000 > /var/log/itinerary.log 2>&1 &

# 8. 等待启动
sleep 3

# 9. 验证部署
echo "📋 验证部署..."
if curl -s http://localhost/ > /dev/null; then
    echo "✅ 部署成功！"
    echo "🌐 访问地址: http://$(curl -s ifconfig.me)/"
else
    echo "❌ 部署失败，请检查日志"
    echo "📋 应用日志: tail -f /var/log/itinerary.log"
    echo "📋 nginx日志: sudo tail -f /var/log/nginx/error.log"
fi
