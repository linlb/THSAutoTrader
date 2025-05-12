# THSAutoTrader

基于同花顺（THS）客户端的自动化交易工具，采用闪电下单模式，并提供可视化交互界面与 API 接口

## 功能特性

- 🚀 支持市价买入、市价卖出操作
- 🔌 提供标准化 REST API 接口，便于实现自动化交易
- ⚖️ 完全基于用户操作模拟，无需修改或破解同花顺客户端，确保合法合规
- 🖥️ 提供友好的交互界面，支持多种编程语言调用
- ⌨️ 通过键盘模拟输入，实现自动化交易流程

## 打包后文件（可直接运行）

- dist/下单辅助程序.exe

## 技术栈

- Python 3.11
- Poetry（依赖管理）
- Flask（Web 服务）
- PyWin32（Windows 窗口控制）

## 快速开始

### 环境准备

1. 安装 Python 3.11
2. 安装 Poetry

### 安装依赖

```bash
poetry install
```

### 运行项目

#### 开发模式（热加载）

```bash
poetry run dev
```

```

### 项目打包

```bash
poetry run scripts:build
```

### 运行打包后的文件

```bash
./dist/main
```

## 使用指南

### 前置准备

1. 打开同花顺客户端
2. 登录交易账户
3. 进入目标个股页面
4. 配置快捷下单：
   - 买入金额锁定
   - 设置为一键买入（买入时不需要确认）

### API 调用示例

#### 闪电买入

```bash
http://localhost:5000/xiadan?key=600000+ENTER++21+ENTER
```

#### 闪电卖出

```bash
http://localhost:5000/xiadan?key=600000+ENTER++23+ENTER
```

> 说明：
>
> - URL 中的 `+` 号会被自动转换为空格
> - 每多一个空格，代表操作间隔增加 500ms
> - `21` 为同花顺键盘精灵的闪电买入快捷键
> - `23` 为闪电卖出快捷键
> - 支持其他键盘精灵的输入操作

## 项目结构

```
src/
    controller/          # 控制器层
    model/               # 数据模型
    service/             # 服务层
        window_service.py    # 窗口控制服务
        deepseek_service.py  # 大模型调用
        trading_service.py   # 交易服务
        flash_service.py     # HTTP 服务管理
    view/                # 视图层
        automation_view.py   # 应用界面
    main.py              # 程序入口
    config.py            # 配置文件
    utils.py             # 工具函数
```

## 注意事项

1. 请确保同花顺客户端已正确配置快捷下单
2. 交易前请仔细核对同花顺交易设置
3. 建议在模拟交易环境中充分测试后再进行实盘操作
