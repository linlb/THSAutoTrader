# 自动化控制面板 - Vite + Vue 3 版本

这是一个基于 Vue 3 和 Vite 构建工具的现代化自动化控制面板，用于管理交易系统的各种操作。

## 项目结构

```
html/front/
├── index.html              # 主HTML文件
├── package.json            # 项目配置和依赖
├── vite.config.js          # Vite配置文件
├── src/
│   ├── main.js            # 应用入口文件
│   ├── App.vue            # 根组件
│   └── components/        # 组件目录
│       ├── WindowControl.vue    # Window控制组件
│       ├── TradingService.vue   # 交易服务组件
│       └── ResultDisplay.vue   # 结果显示组件
└── README.md              # 说明文档
```

## 功能特性

1. **Window 控制**

   - 获取持仓信息
   - 获取资金信息
   - 实时显示 API 调用结果

2. **交易服务**

   - 执行交易操作
   - 支持异步操作状态显示

3. **响应式设计**

   - 基于 Bootstrap 5 的现代 UI
   - 移动端友好的响应式布局

4. **现代化开发体验**
   - 热重载开发服务器
   - 组件化开发
   - ES6+ 语法支持
   - 单文件组件(.vue)

## 技术栈

- **Vue 3** - 渐进式 JavaScript 框架
- **Vite** - 现代化构建工具
- **Axios** - HTTP 请求库
- **Bootstrap 5** - CSS 框架
- **Composition API** - Vue 3 响应式 API

## 安装和使用

### 安装依赖

```bash
npm install
```

### 开发模式运行

```bash
npm run dev
```

开发服务器将在 `http://localhost:3000` 启动

### 构建生产版本

```bash
npm run build
```

### 预览生产构建

```bash
npm run preview
```

## API 接口

- `GET /position` - 获取持仓信息
- `GET /balance` - 获取资金信息
- `POST /trade` - 执行交易操作

## 组件说明

### WindowControl.vue

负责显示和管理 API 调用按钮，使用 Composition API 和响应式数据。

### TradingService.vue

提供交易操作的用户界面，支持 loading 状态管理。

### ResultDisplay.vue

统一显示所有 API 调用的返回结果，支持格式化 JSON 输出。

### App.vue

根组件，管理全局状态和组件通信。

## 开发说明

### 添加新组件

1. 在 `src/components/` 目录创建新的 `.vue` 文件
2. 在需要的组件中导入并注册
3. 使用 `<template>`, `<script>`, `<style>` 标签组织代码

### 环境要求

- Node.js 14+
- npm 或 yarn

### 故障排除

如果遇到启动错误：

1. 删除 `node_modules` 和 `package-lock.json`
2. 重新运行 `npm install`
3. 确保 Node.js 版本兼容

### 热重载

开发模式下修改代码会自动刷新浏览器，无需手动刷新。
