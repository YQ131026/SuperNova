# SuperNova

> 一个强大的多主机 Supervisor 服务管理平台

[![Python](https://img.shields.io/badge/Python-3.12-blue.svg)](https://www.python.org)
[![Flask](https://img.shields.io/badge/Flask-2.0+-green.svg)](https://flask.palletsprojects.com)
[![Bootstrap](https://img.shields.io/badge/Bootstrap-5.0+-purple.svg)](https://getbootstrap.com)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## 简介

SuperNova 是一个基于 Flask 的 Web 应用，用于集中管理多台主机上的 Supervisor 服务。它提供了直观的界面和强大的功能，帮助您轻松管理和监控所有 Supervisor 服务。

### 主要特性

- 多主机管理 - 集中管理多台服务器
- 实时监控 - 实时监控服务状态
- 批量操作 - 支持批量服务控制
- 数据统计 - 直观的数据统计展示
- 日志管理 - 完整的日志记录系统
- 配置备份 - 自动的配置文件备份
- 快速响应 - 高效的异步处理机制

## 快速开始

### 环境要求

- Python 3.12+
- Supervisor 4.0+
- 现代浏览器

### 安装步骤

1. 克隆仓库
```bash
git clone https://github.com/yourusername/SuperNova.git
cd SuperNova
```

2. 创建虚拟环境
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
.\venv\Scripts\activate   # Windows
```

3. 安装依赖
```bash
pip install -r requirements.txt
```

4. 配置主机信息
```yaml
# config/hosts.yaml
hosts:
  - id: "host1"
    name: "生产服务器1"
    ip: "192.168.1.100"
    port: 9001
```

5. 启动应用
```bash
python run.py
```

访问 http://localhost:5000 开始使用！

## 核心功能

### 仪表盘
- 系统状态概览
- 主机状态监控
- 服务运行统计

### 服务管理
- 服务状态查看
- 启动/停止/重启
- 批量操作控制
- 日志实时查看

### 系统监控
- 主机状态检测
- 服务健康检查
- 异常自动告警

### 配置管理
- 配置文件管理
- 自动备份还原
- 版本控制追踪

## 开发指南

### 项目结构
```
SuperNova/
├── app/                 # 应用核心
│   ├── templates/       # 页面模板
│   ├── static/         # 静态资源
│   ├── routes/         # 路由控制
│   ├── services/       # 业务逻辑
│   └── utils/          # 工具函数
├── config/             # 配置文件
├── logs/              # 日志文件
└── tests/             # 测试用例
```

### 开发规范
- 遵循 PEP 8 编码规范
- 使用 Type Hints 类型提示
- 编写单元测试用例
- 提供详细的注释文档

## 待办事项

- 用户认证系统
- 权限管理模块
- WebSocket 实时通信
- 告警通知系统
- 性能监控优化
- 容器化部署支持

## 贡献指南

1. Fork 本仓库
2. 创建特性分支
3. 提交您的更改
4. 推送到分支
5. 创建 Pull Request

## 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

## 联系方式

- 项目问题: [GitHub Issues](https://github.com/yourusername/SuperNova/issues)
- 邮件联系: your.email@example.com

## 致谢

感谢所有为这个项目做出贡献的开发者！