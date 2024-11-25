import os
import json
import shutil
import time
from datetime import datetime
from tkinter import (
    Tk, Label, Button, Entry, filedialog, StringVar, IntVar, messagebox, Radiobutton, Toplevel, BooleanVar, Checkbutton, colorchooser, font, Scale, HORIZONTAL
)
import threading
import colorsys

# 配置文件路径
CONFIG_FILE = "config.json"

# 加载配置
def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    else:
        return {"dont_show_exit_popup": False, "background_color": "#ffffff", "window_alpha": 1.0}

# 保存配置
def save_config(config):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=4)

# 全局变量
last_backup_time = {"full": None, "incremental": None}
config = load_config()

# 彩色渐变文字动态更新
def update_gradient_label(label, hue=0):
    r, g, b = colorsys.hsv_to_rgb(hue, 1, 1)
    color = f"#{int(r * 255):02x}{int(g * 255):02x}{int(b * 255):02x}"
    label.config(fg=color)
    hue = (hue + 0.01) % 1
    label.after(100, update_gradient_label, label, hue)

# 选择背景颜色
def choose_background_color():
    color_code = colorchooser.askcolor(title="选择背景颜色")[1]
    if color_code:
        app.config(bg=color_code)
        config["background_color"] = color_code  # 保存背景颜色到配置

# 调整字体颜色
def choose_font_color():
    color_code = colorchooser.askcolor(title="选择字体颜色")[1]
    if color_code:
        for widget in [source_label, dest_label, interval_label, mode_label]:
            widget.config(fg=color_code)

# 调整窗口透明度

def set_window_alpha(alpha):
    app.attributes("-alpha", alpha)
    config["window_alpha"] = alpha  # 保存透明度到配置

# 完整备份函数
def backup_full(source_folder, destination_folder):
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    backup_dir = os.path.join(destination_folder, f"full_backup_{timestamp}")
    shutil.copytree(source_folder, backup_dir)
    print(f"完成完整备份: {backup_dir}")
    last_backup_time["full"] = time.time()

# 差异备份函数
def backup_differential(source_folder, destination_folder):
    if not last_backup_time["full"]:
        backup_full(source_folder, destination_folder)
        return
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    backup_dir = os.path.join(destination_folder, f"differential_backup_{timestamp}")
    os.makedirs(backup_dir, exist_ok=True)

    for root, _, files in os.walk(source_folder):
        for file in files:
            source_file = os.path.join(root, file)
            relative_path = os.path.relpath(root, source_folder)
            dest_dir = os.path.join(backup_dir, relative_path)
            os.makedirs(dest_dir, exist_ok=True)
            if os.path.getmtime(source_file) > last_backup_time["full"]:
                shutil.copy2(source_file, os.path.join(dest_dir, file))
    print(f"完成差异备份: {backup_dir}")

# 增量备份函数
def backup_incremental(source_folder, destination_folder):
    last_backup = last_backup_time["incremental"] or last_backup_time["full"]
    if not last_backup:
        backup_full(source_folder, destination_folder)
        return
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    backup_dir = os.path.join(destination_folder, f"incremental_backup_{timestamp}")
    os.makedirs(backup_dir, exist_ok=True)

    for root, _, files in os.walk(source_folder):
        for file in files:
            source_file = os.path.join(root, file)
            relative_path = os.path.relpath(root, source_folder)
            dest_dir = os.path.join(backup_dir, relative_path)
            os.makedirs(dest_dir, exist_ok=True)
            if os.path.getmtime(source_file) > last_backup:
                shutil.copy2(source_file, os.path.join(dest_dir, file))
    print(f"完成增量备份: {backup_dir}")
    last_backup_time["incremental"] = time.time()

# 全局变量，用于控制备份任务的运行状态
backup_running = False

# 全局变量，用于控制备份任务的运行状态
backup_running = False

# 停止备份函数
def stop_backup():
    global backup_running
    backup_running = False
    status_label.config(text="停止备份", fg="red")  # 更新状态为“停止备份”
    print("备份已停止！")

# 备份任务函数（更新后的）
def backup_task():
    global backup_running
    source = source_var.get()
    destination = destination_var.get()
    interval = interval_var.get()
    mode = backup_mode.get()

    if not source or not destination or interval <= 0:
        messagebox.showerror("错误", "请正确填写所有字段！")
        return

    if not os.path.exists(source):
        messagebox.showerror("错误", f"源文件夹 '{source}' 不存在！")
        return

    if not os.path.exists(destination):
        os.makedirs(destination)

    backup_running = True  # 启动备份时设置为运行状态
    status_label.config(text="正在备份中", fg="green")  # 更新状态为“正在备份中”

    while backup_running:  # 只在运行状态下继续循环
        if mode == 1:
            backup_full(source, destination)
        elif mode == 2:
            backup_differential(source, destination)
        elif mode == 3:
            backup_incremental(source, destination)
        print("等待下一个备份周期...")
        time.sleep(interval)

    if not backup_running:  # 如果退出循环，更新状态
        status_label.config(text="停止备份", fg="red")
        print("备份任务已退出。")


# 确认关闭函数
def on_closing():
    if config["dont_show_exit_popup"]:
        save_config(config)
        app.destroy()
    else:
        popup = Toplevel(app)
        popup.title("退出程序")
        popup.geometry("300x150")
        Label(popup, text="是否关闭程序？").pack(pady=10)
        Checkbutton(popup, text="下次不再提示", variable=dont_show_exit_popup, command=lambda: config.update({"dont_show_exit_popup": dont_show_exit_popup.get()})).pack(pady=5)
        Button(popup, text="最小化", command=lambda: [popup.destroy(), app.iconify()]).pack(side="left", padx=20)
        Button(popup, text="关闭程序", command=lambda: [save_config(config), popup.destroy(), app.destroy()]).pack(side="right", padx=20)



# 主窗口
app = Tk()
app.title("文件夹备份工具")
app.geometry("500x710")

# 定义字体
custom_font = font.Font(family="Arial", size=12)

# 状态显示标签
status_label = Label(app, text="未开始备份", font=custom_font, fg="blue")
status_label.pack(pady=10)

# 设置窗口透明度和背景颜色
app.attributes("-alpha", config.get("window_alpha", 1.0))
app.config(bg=config.get("background_color", "#ffffff"))

dont_show_exit_popup = BooleanVar(value=config.get("dont_show_exit_popup", False))  # 从配置中读取值

custom_font = font.Font(family="Arial", size=12)

# 字段输入
source_var = StringVar()
destination_var = StringVar()
interval_var = IntVar(value=300)
backup_mode = IntVar(value=1)

source_label = Label(app, text="源文件夹:", font=custom_font)
source_label.pack(pady=5)
Entry(app, textvariable=source_var, width=40).pack(pady=5)
Button(app, text="选择文件夹", command=lambda: source_var.set(filedialog.askdirectory())).pack()

dest_label = Label(app, text="目标文件夹:", font=custom_font)
dest_label.pack(pady=5)
Entry(app, textvariable=destination_var, width=40).pack(pady=5)
Button(app, text="选择文件夹", command=lambda: destination_var.set(filedialog.askdirectory())).pack()

interval_label = Label(app, text="备份间隔（秒）:", font=custom_font)
interval_label.pack(pady=5)
Entry(app, textvariable=interval_var, width=10).pack()

mode_label = Label(app, text="选择备份模式:", font=custom_font)
mode_label.pack(pady=6)
Radiobutton(app, text="完全备份", variable=backup_mode, value=1).pack()
Radiobutton(app, text="差异备份", variable=backup_mode, value=2).pack()
Radiobutton(app, text="增量备份", variable=backup_mode, value=3).pack()

Button(app, text="启动备份", command=lambda: threading.Thread(target=backup_task, daemon=True).start()).pack(pady=10)
Button(app, text="停止备份", command=stop_backup).pack(pady=5)
Button(app, text="选择背景颜色", command=choose_background_color).pack(pady=6)
Button(app, text="选择字体颜色", command=choose_font_color).pack(pady=6)


# 窗口透明度调节
Label(app, text="调整透明度:", font=custom_font).pack(pady=5)
alpha_scale = Scale(app, from_=0, to=1.0, resolution=0.05, orient=HORIZONTAL, command=lambda v: set_window_alpha(float(v)))
alpha_scale.set(1.0)  # 确保滑动条初始值为 1.0
alpha_scale.pack()

# 动态标注
gradient_label = Label(app, text="此程序由@zudewang免费提供，禁止商用。", font=("黑体", 12))
gradient_label.pack(side="bottom", pady=12)

# 开始动态颜色更新
update_gradient_label(gradient_label)

app.protocol("WM_DELETE_WINDOW", on_closing)

app.mainloop()

