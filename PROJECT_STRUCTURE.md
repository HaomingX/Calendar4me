# 项目结构说明

## 📁 目录结构

```
Calendar4me/
├── app/                          # 主应用目录
│   ├── __init__.py              # 应用初始化
│   ├── main.py                  # FastAPI主应用
│   ├── models.py                # 数据模型（支持周期性事件）
│   ├── schemas.py               # API模式（支持周期性事件）
│   ├── crud.py                  # 数据库操作（支持周期性事件）
│   ├── database.py              # 数据库配置
│   ├── emailer.py               # 邮件发送
│   ├── scheduler.py             # 提醒调度器
│   ├── utils.py                 # 周期性事件工具
│   ├── models_original.py       # 原始模型备份
│   ├── schemas_original.py      # 原始模式备份
│   ├── crud_original.py         # 原始CRUD备份
│   ├── static/                  # 静态文件
│   └── templates/               # 模板文件
├── scripts/                      # 脚本目录
│   └── parse_ical_courses.py    # iCal课程解析脚本
├── data/                         # 数据目录
│   └── courses_recurring.json   # 周期性课程数据
├── deploy/                       # 部署配置
├── .venv/                        # 虚拟环境
├── quick-deploy.sh              # 快速部署脚本
├── README.md                    # 项目说明
├── requirements.txt             # 依赖包
├── .env                         # 环境配置
└── itinerary.db                # SQLite数据库
```

## 🔧 核心功能

### 周期性事件支持
- **models.py**: 包含周期性事件字段的数据模型
- **schemas.py**: 支持周期性事件的API模式
- **crud.py**: 周期性事件的CRUD操作
- **utils.py**: 周期性事件处理工具

### 课程管理
- **scripts/parse_ical_courses.py**: 解析iCal格式的课程数据
- **data/courses_recurring.json**: 解析后的周期性课程数据

### 部署
- **quick-deploy.sh**: 一键部署脚本
- **deploy/**: 部署配置文件

## 📝 使用说明

### 解析iCal课程
```bash
python3 scripts/parse_ical_courses.py
```

### 快速部署
```bash
./quick-deploy.sh
```

### 查看课程数据
```bash
cat data/courses_recurring.json
```
