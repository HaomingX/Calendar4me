#!/bin/bash

# Nginx部署脚本 - Calendar4me应用
# 使用方法: sudo bash setup-nginx.sh

echo "=== Calendar4me Nginx 部署脚本 ==="

# 检查是否以root权限运行
if [ "$EUID" -ne 0 ]; then
    echo "请使用sudo运行此脚本"
    exit 1
fi

# 检查nginx是否已安装
if ! command -v nginx &> /dev/null; then
    echo "正在安装nginx..."
    apt update
    apt install -y nginx
fi

# 备份现有配置
if [ -f /etc/nginx/sites-available/default ]; then
    echo "备份现有nginx配置..."
    cp /etc/nginx/sites-available/default /etc/nginx/sites-available/default.backup.$(date +%Y%m%d_%H%M%S)
fi

# 复制新的配置文件
echo "配置nginx..."
cp /root/Calendar4me/deploy/nginx-site.conf /etc/nginx/sites-available/calendar4me

# 创建软链接启用站点
ln -sf /etc/nginx/sites-available/calendar4me /etc/nginx/sites-enabled/

# 删除默认站点
rm -f /etc/nginx/sites-enabled/default

# 测试nginx配置
echo "测试nginx配置..."
nginx -t

if [ $? -eq 0 ]; then
    echo "配置测试成功！"
    
    # 重启nginx
    echo "重启nginx服务..."
    systemctl restart nginx
    systemctl enable nginx
    
    echo "=== 部署完成 ==="
    echo "Nginx已配置为监听80端口"
    echo "FastAPI应用需要运行在8000端口"
    echo ""
    echo "启动FastAPI应用:"
    echo "cd /root/Calendar4me"
    echo "source .venv/bin/activate"
    echo "uvicorn app.main:app --host 0.0.0.0 --port 8000"
    echo ""
    echo "检查服务状态:"
    echo "systemctl status nginx"
    echo "curl http://localhost/health"
    echo ""
    echo "查看nginx日志:"
    echo "tail -f /var/log/nginx/access.log"
    echo "tail -f /var/log/nginx/error.log"
else
    echo "配置测试失败，请检查配置文件"
    echo "错误详情请查看: nginx -t"
    exit 1
fi
