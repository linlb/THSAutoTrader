@echo off
echo ================================================
echo 自动化控制面板 - 构建脚本
echo ================================================

echo 正在构建生产版本...
call npm run build

if %errorlevel% neq 0 (
    echo 构建失败，请检查代码和依赖
    pause
    exit /b 1
)

echo.
echo ================================================
echo 构建完成！
echo.
echo 文件输出位置：
echo   - HTML: ../index.html
echo   - JS:   ../js/
echo   - CSS:  ../css/
echo   - 其他: ../assets/
echo.
echo 可以直接在浏览器中打开 ../index.html 运行
echo ================================================

pause 