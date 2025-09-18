# Nginx配置说明 - Calendar4me应用

## 配置文件说明

### 1. nginx-simple.conf
- **用途**: 简化版配置，仅支持HTTP(80端口)
- **适用场景**: 快速部署，不需要HTTPS
- **特点**: 配置简单，易于理解和修改

### 2. nginx.conf
- **用途**: 完整版配置，支持HTTP和HTTPS
- **适用场景**: 生产环境，需要SSL证书
- **特点**: 包含上游服务器配置，性能优化

### 3. nginx-https.conf
- **用途**: HTTPS专用配置
- **适用场景**: 需要强制HTTPS的生产环境
- **特点**: 自动重定向HTTP到HTTPS

## 快速部署步骤

### 方法1: 使用自动部署脚本 (推荐)
```bash
# 进入项目目录
cd /root/Calendar4me

# 运行部署脚本
sudo bash deploy/setup-nginx.sh
```

### 方法2: 手动部署
```bash
# 1. 安装nginx (如果未安装)
sudo apt update
sudo apt install -y nginx

# 2. 备份现有配置
sudo cp /etc/nginx/sites-available/default /etc/nginx/sites-available/default.backup

# 3. 复制新配置
sudo cp /root/Calendar4me/deploy/nginx-simple.conf /etc/nginx/sites-available/calendar4me

# 4. 启用站点
sudo ln -sf /etc/nginx/sites-available/calendar4me /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default

# 5. 测试配置
sudo nginx -t

# 6. 重启nginx
sudo systemctl restart nginx
sudo systemctl enable nginx
```

## 启动FastAPI应用

```bash
# 进入项目目录
cd /root/Calendar4me

# 激活虚拟环境
source .venv/bin/activate

# 启动应用 (确保运行在8000端口)
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## 验证部署

```bash
# 检查nginx状态
sudo systemctl status nginx

# 检查端口监听
sudo netstat -tlnp | grep :80

# 测试健康检查
curl http://localhost/health

# 测试静态文件
curl http://localhost/static/styles.css
```

## HTTPS配置 (可选)

如果需要HTTPS支持：

1. **获取SSL证书**:
   - 使用Let's Encrypt免费证书
   - 或使用阿里云SSL证书

2. **使用Let's Encrypt**:
```bash
# 安装certbot
sudo apt install -y certbot python3-certbot-nginx

# 获取证书 (替换your-domain.com为你的域名)
sudo certbot --nginx -d your-domain.com

# 自动续期
sudo crontab -e
# 添加: 0 12 * * * /usr/bin/certbot renew --quiet
```

3. **使用HTTPS配置**:
```bash
# 复制HTTPS配置
sudo cp /root/Calendar4me/deploy/nginx-https.conf /etc/nginx/sites-available/calendar4me-https

# 修改证书路径
sudo nano /etc/nginx/sites-available/calendar4me-https

# 启用HTTPS站点
sudo ln -sf /etc/nginx/sites-available/calendar4me-https /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/calendar4me

# 测试并重启
sudo nginx -t
sudo systemctl restart nginx
```

## 常见问题

### 1. 502 Bad Gateway
- 检查FastAPI应用是否运行在8000端口
- 检查防火墙设置
- 查看nginx错误日志: `sudo tail -f /var/log/nginx/error.log`

### 2. 静态文件404
- 检查静态文件路径: `/root/Calendar4me/app/static/`
- 确保nginx有读取权限: `sudo chown -R www-data:www-data /root/Calendar4me/app/static/`

### 3. 端口冲突
- 检查80端口是否被占用: `sudo netstat -tlnp | grep :80`
- 停止其他web服务: `sudo systemctl stop apache2` (如果安装了apache)

### 4. 权限问题
- 确保nginx用户有权限访问项目目录
- 检查SELinux设置 (如果启用)

## 性能优化

### 1. 启用gzip压缩
在nginx配置中添加:
```nginx
gzip on;
gzip_vary on;
gzip_min_length 1024;
gzip_types text/plain text/css application/json application/javascript text/xml application/xml;
```

### 2. 调整worker进程
在nginx主配置中:
```nginx
worker_processes auto;
worker_connections 1024;
```

### 3. 启用缓存
```nginx
location ~* \.(jpg|jpeg|png|gif|ico|css|js)$ {
    expires 1y;
    add_header Cache-Control "public, immutable";
}
```

## 监控和日志

```bash
# 查看访问日志
sudo tail -f /var/log/nginx/access.log

# 查看错误日志
sudo tail -f /var/log/nginx/error.log

# 查看nginx状态
sudo systemctl status nginx

# 重新加载配置 (不重启)
sudo nginx -s reload
```
