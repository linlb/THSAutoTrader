# Repository Guidelines

## 项目结构与模块职责

- `main.py`：Windows 桌面入口，负责单实例控制和 Tkinter 启动。
- `src/app/` 组织应用；`src/controller/` 协调业务；`src/service/` 实现 Flask API、窗口控制、交易和持仓服务。
- `src/models/` 保存模型，`src/view/` 提供桌面界面，`src/util/` 提供日志工具。
- `config/` 保存配置，`static/` 保存图标，`Tesseract-OCR/` 提供 OCR 运行资源。
- `tests/` 当前仅有 `__init__.py`；`build/`、`dist/` 为构建及分发目录。`vue-app/` 当前为空且被忽略，不要依据旧文档假设存在可运行的前端工程。

## 安装、开发与构建

在 Windows 上使用 Python 3.11 和 Poetry；桌面入口依赖 Win32，不能直接在 Linux/WSL 中运行。

- `poetry install`：安装项目依赖。
- `poetry run start`：启动桌面应用及其集成服务。
- `poetry run dev`：使用 hupper 启动热加载开发模式。
- `poetry run build`：执行 `scripts.py` 中的 PyInstaller 打包流程，生成 `dist/下单辅助程序.exe` 并复制 OCR 资源；需保留图标与 `Tesseract-OCR/`。

## 代码风格与命名

Python 使用四空格缩进；模块、函数和变量使用 `snake_case`，类使用 `PascalCase`，常量使用 `UPPER_SNAKE_CASE`。保持现有中文说明与相邻代码风格，复用 `src/util/logger.py` 的日志设施。当前未配置格式化或 lint 工具，不要顺带批量重排代码。保持控制器、服务与视图职责分离；修改 API 时同步检查调用链和 README 示例。

## 测试约定

当前没有实质自动化测试或覆盖率门槛。`pyproject.toml` 中 pytest 使用条件依赖声明，不应假定普通安装后可用；补充测试前先确认测试依赖安装方式。采用 `tests/test_<module>.py` 与 `test_<behavior>` 命名，安装 pytest 后可用 `poetry run pytest tests/` 运行。

验证交易逻辑时 mock 窗口、键盘、OCR 和网络服务，覆盖参数校验、失败路径与并发操作。桌面集成验证需 Windows 隔离环境；禁止将真实下单或撤单作为自动化冒烟测试。

## 提交与 Pull Request

历史提交使用简短中文动作描述，也有 `Update README.md`、`build exe`，未形成严格 Conventional Commits 约定。提交应聚焦单一变更并说明行为，例如 `修复持仓读取失败处理`。

PR 应说明目的、影响模块、验证步骤与结果，并关联已有任务；界面变更附截图，API 变更附请求和响应示例。不要无意提交日志、缓存、账户信息或构建产物；发布二进制需明确说明。

## 安全与协作

Flask 服务默认监听 `0.0.0.0:5000`，部分 GET 接口会触发交易或键盘操作；开发时限制网络访问，不要直接暴露公网，也不要随意探测写操作接口。

使用中文沟通，指出需求假设与潜在风险。讨论技术方案时先取得认可再改代码；修改前阅读上下文及完整调用链，避免只修局部而破坏 GUI 操作同步或业务流程。
