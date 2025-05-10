from src.app.automation import AutomationApp
import tkinter as tk

def main():
    root = tk.Tk()
    root.title("下单接口 v1.0")
    root.resizable(False, False)
    root.attributes('-topmost', True)
    root.attributes('-alpha', 0.8)
    app = AutomationApp(root)
    root.mainloop()

def dev():
    import hupper
    print('热加载')
    reloader = hupper.start_reloader('main.main')
    reloader.watch_files('**/*.py')

if __name__ == "__main__":
    main()