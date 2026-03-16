# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

THSAutoTrader is an automated trading tool for THS (同花顺) client that provides a web API for programmatic trading operations. It uses GUI automation to interact with the THS trading interface and provides both a Tkinter desktop interface and a Vue.js web frontend.

## Development Commands

### Python Backend
```bash
# Install dependencies
poetry install

# Run in development mode (with hot reload)
poetry run dev

# Run normally
poetry run start

# Build executable
poetry run build
```

### Vue Frontend
```bash
# Navigate to frontend directory
cd front

# Install dependencies
npm install

# Run development server
npm run dev

# Build for production
npm run build
```

## Architecture Overview

### Backend Structure (Python)
- **MVC Pattern**: Uses Model-View-Controller architecture
- **Entry Point**: `main.py` - Creates Tkinter GUI and starts AutomationApp
- **Core App**: `src/app/automation.py` - Main application orchestrator
- **Controller**: `src/controller/automation_controller.py` - Business logic for trading operations
- **Services**:
  - `flask_service.py` - HTTP API server (runs on port 5000)
  - `window_service.py` - Windows automation and GUI control
  - `trading_service.py` - Trading-specific operations
  - `position_service.py` - Position and balance management
- **View**: `src/view/automation_view.py` - Tkinter GUI interface
- **Models**: `src/models/app_model.py` - Data models
- **Utils**: `src/util/logger.py` - Logging utilities

### Frontend Structure (Vue.js)
- **Framework**: Vue 3 with Vite
- **Components**:
  - `StockPool.vue` - Stock selection interface
  - `TradingService.vue` - Trading controls
  - `ResultDisplay.vue` - Results and logs display
  - `WindowControl.vue` - Window management controls
- **Build Output**: Builds to `../html/` directory for integration with Python backend

### Key Dependencies
- **GUI Automation**: pyautogui, pywinauto, pywin32
- **OCR**: pytesseract (with bundled Tesseract-OCR)
- **Web Server**: Flask with CORS support
- **Frontend**: Vue 3, Bootstrap 5, Axios

## API Endpoints

The Flask service provides these main endpoints:
- `GET /xiadan?code=STOCK_CODE&status=1|2&amount=OPTIONAL&price=OPTIONAL` - Buy/sell orders
- `GET /position` - Get current positions
- `GET /balance` - Get account balance
- `GET /cancel_all_orders` - Cancel all pending orders
- `GET /send_key?key=KEYS` - Send keyboard input to THS client

## Build and Deployment

### Executable Build Process
1. PyInstaller creates standalone executable
2. Copies `html/` directory for web interface
3. Bundles `Tesseract-OCR/` directory for OCR functionality
4. Output: `dist/下单辅助程序.exe`

### File Structure Requirements
- `static/icon.ico` - Application icon
- `html/` - Web interface files (built from Vue frontend)
- `Tesseract-OCR/` - OCR engine and language data
- `config/` - Configuration files

## Windows-Specific Considerations

This application is Windows-only due to:
- Windows-specific GUI automation libraries (pywin32, pywinauto)
- Integration with THS Windows client
- Windows-specific window management and keyboard simulation

## Development Notes

- The application runs a dual interface: Tkinter desktop app + embedded web server
- Hot reload available in development mode using hupper
- Frontend builds are integrated into the Python package structure
- OCR is used for reading trading interface elements when needed
- All GUI automation is based on window class names and control IDs specific to THS client
