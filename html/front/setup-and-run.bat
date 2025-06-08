@echo off
echo ================================================
echo 自动化控制面板 - 安装和启动脚本
echo ================================================

echo 正在安装依赖包...
call npm install

if %errorlevel% neq 0 (
    echo 安装失败，请检查网络连接和Node.js版本
    pause
    exit /b 1
)

echo.
echo 依赖安装完成！
echo 正在启动开发服务器...
echo 浏览器将自动打开 http://localhost:3000
echo.
echo 按 Ctrl+C 停止服务器
echo ================================================

call npm run dev

pause 