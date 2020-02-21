import os, shutil, inspect
import json
import threading
import traceback
from tkinter import *
from tkinter.scrolledtext import *
from tkinter.messagebox import showinfo
from bot import *

class GUI:

    def __init__(self, master):
        # 设置工作目录, 读取配置文件
        self.work_dir = os.path.realpath(os.path.abspath(
            os.path.split(inspect.getfile(inspect.currentframe()))[0]
        ))
        self.read_config()

        # 新建master窗口
        self.master = master
        self.master.title("EPC-BOT for USTC")
        self.master.resizable(False, False)
        self.master.protocol('WM_DELETE_WINDOW', self.on_gui_destroy)

        # 新建frame布局, 用于设置参数
        self.settings_frame = Frame(self.master)
        self.settings_frame.grid(row=0, column=0, padx=20, pady=10)

        # 新建frame子布局, 用于填写用户的基本信息
        self.basic_frame = Frame(self.settings_frame)
        self.basic_frame.grid(row=0, pady=10)
        Label(self.basic_frame, text="--- Basic Settings ---").grid(row=0, columnspan=4)
        self.ustc_id_label = Label(self.basic_frame, text="USTC Student ID")
        self.ustc_id_label.grid(row=1, column=0, padx=5, pady=2)
        self.ustc_id_entry = Entry(self.basic_frame, width=30)
        self.ustc_id_entry.grid(row=1, column=1, padx=5, pady=2)
        self.ustc_pwd_label = Label(self.basic_frame, text="USTC Password")
        self.ustc_pwd_label.grid(row=2, column=0, padx=10, pady=2)
        self.ustc_pwd_entry = Entry(self.basic_frame, width=30, show="*")
        self.ustc_pwd_entry.grid(row=2, column=1, padx=5, pady=2)
        self.email_addr_label = Label(self.basic_frame, text="Email Addrress")
        self.email_addr_label.grid(row=3, column=0, padx=5, pady=2)
        self.email_addr_entry = Entry(self.basic_frame, width=30)
        self.email_addr_entry.grid(row=3, column=1, padx=5, pady=2)
        self.email_pwd_label = Label(self.basic_frame, text="Email Password")
        self.email_pwd_label.grid(row=4, column=0, padx=10, pady=2)
        self.email_pwd_entry = Entry(self.basic_frame, width=30, show="*")
        self.email_pwd_entry.grid(row=4, column=1, padx=5, pady=2)

        # 新建frame子布局, 用于勾选所有允许选课的课程种类
        self.type_filter_frame = Frame(self.settings_frame)
        self.type_filter_frame.grid(row=1, pady=10)
        Label(self.type_filter_frame, text="--- EPC Type Settings ---") \
            .grid(row=0, columnspan=5)

        # 遍历配置模板文件中的全部课程种类, 新建同名checkbutton元素
        self.type_filter_checked = list()
        self.type_filter_elements = list()
        row, col = 1, 0
        for i in range(len(self.type_filter)):
            # 每行排列三个checkbutton元素, 计算行列坐标
            if (i%3 == 0):
                row = row + 1
                col = -1
            col = col + 1

            # 新建checkbutton元素
            self.type_filter_checked.append(IntVar())
            element_name = self.type_filter[i]["type"]
            element = Checkbutton(self.type_filter_frame, text=element_name, \
                variable=self.type_filter_checked[i])
            element.grid(row=row, column=col, padx=5, pady=2, sticky=W)
            self.type_filter_elements.append(element)

        # 新建frame子布局, 用于勾选所有允许选课的时间段
        self.wday_filter_frame = Frame(self.settings_frame)
        self.wday_filter_frame.grid(row=2, pady=10)
        Label(self.wday_filter_frame, text="--- Time Settings ---") \
            .grid(row=0, columnspan=5)

        # 遍历配置模板文件中的全部时间段, 新建同名checkbutton元素
        self.wday_filter_checked = list()
        self.wday_filter_elements = list()
        row, col = 1, 0
        for i in range(len(self.wday_filter)):
            # 每行排列三个checkbutton元素, 计算行列坐标
            if (i%3 == 0):
                row = row + 1
                col = -1
            col = col + 1

            # 新建checkbutton元素
            self.wday_filter_checked.append(IntVar())
            element_name = "%s.\t%s" % \
                (self.wday_filter[i]["wday"][0:3], self.wday_filter[i]["time"])
            element = Checkbutton(self.wday_filter_frame, text=element_name, \
                variable=self.wday_filter_checked[i])
            element.grid(row=row, column=col, padx=5, pady=2)
            self.wday_filter_elements.append(element)
            
        # 新建frame子布局, 用于放置button元素
        self.buttons_frame = Frame(self.settings_frame)
        self.buttons_frame.grid(row=3, pady=10)

        # 新建button元素, 用于启动或停止bot
        self.start_button = Button(self.buttons_frame, text="Start", 
            width=10, command=self.start_bot)
        self.start_button.grid(row=0, column=0, padx=10)
        self.stop_button  = Button(self.buttons_frame, text="Stop", 
            width=10, command=self.stop_bot)
        self.stop_button.grid(row=0, column=1, padx=10)

        # 新建scrolledtext元素, 用于输出日志
        self.console = ScrolledText(self.master, width=60, padx=20, pady=10)
        self.console.grid(row=0, column=1, sticky=S+N)
        self.print_log("EPC-BOT v1.1")
        self.print_log("Developer: @Arsennnic")
        self.print_log("")

        # 应用配置文件中的设置
        self.apply_config()


    # ================================================================
    # 读取工作目录下存储的配置文件
    # ================================================================
    def read_config(self):
        config_dir = os.path.join(self.work_dir, "config.json")
        if not os.path.exists(config_dir):
            shutil.copy("config.template.json", "config.json")
        with open(config_dir, "r", encoding="utf-8") as config:
            config = json.load(config)
        self.ustc_id     = config["ustc_id"]
        self.ustc_pwd    = config["ustc_pwd"]
        self.email_addr  = config["email_addr"]
        self.email_pwd   = config["email_pwd"]
        self.type_filter = config["type_filter"]
        self.wday_filter = config["wday_filter"]


    # ================================================================
    # 应用配置文件中的设置
    # ================================================================
    def apply_config(self):
        self.ustc_id_entry.insert(0, self.ustc_id)
        self.ustc_pwd_entry.insert(0, self.ustc_pwd)
        self.email_addr_entry.insert(0, self.email_addr)
        self.email_pwd_entry.insert(0, self.email_pwd)
        for i in range(len(self.type_filter)):
            if self.type_filter[i]["enable"]:
                self.type_filter_elements[i].select()
            else:
                self.type_filter_elements[i].deselect()
        for i in range(len(self.wday_filter)):
            if self.wday_filter[i]["enable"]:
                self.wday_filter_elements[i].select()
            else:
                self.wday_filter_elements[i].deselect()


    # ================================================================
    # 写入最新的配置文件
    # ================================================================
    def write_config(self):
        config = dict()
        config["ustc_id"]     = self.ustc_id
        config["ustc_pwd"]    = self.ustc_pwd
        config["email_addr"]  = self.email_addr
        config["email_pwd"]   = self.email_pwd
        config["type_filter"] = self.type_filter
        config["wday_filter"] = self.wday_filter
        with open("config.json", "w", encoding="utf-8") as f:
            json.dump(config, f, ensure_ascii=False, indent=4)
        return config
    

    # ================================================================
    # 从设置面板中获取最新的设置
    # ================================================================
    def sync_config(self):
        self.ustc_id    = self.ustc_id_entry.get()
        self.ustc_pwd   = self.ustc_pwd_entry.get()
        self.email_addr = self.email_addr_entry.get()
        self.email_pwd  = self.email_pwd_entry.get()
        for i in range(len(self.type_filter_elements)):
            self.type_filter[i]["enable"] = bool(self.type_filter_checked[i].get())
        for i in range(len(self.wday_filter_elements)):
            self.wday_filter[i]["enable"] = bool(self.wday_filter_checked[i].get())
        

    # ================================================================
    # 启动EPC-BOT
    # ================================================================
    def start_bot(self):
        # 获取设置面板中最新配置信息, 储存到变量
        self.sync_config()
        
        # 若基本信息的输入框非空, 则写入配置文件
        if (not len(self.ustc_id)):    return
        if (not len(self.ustc_pwd)):   return
        if (not len(self.email_addr)): return
        if (not len(self.email_pwd)):  return
        config = self.write_config()
        
        # 启动bot
        self.bot = EPCBot(config, ui=self)
        self.bot.start()
        self.print_log("EPC-Bot is running...")
        self.print_log("")


    # ================================================================
    # 停止EPC-BOT
    # ================================================================
    def stop_bot(self):
        self.bot.stop()
        self.print_log("EPC-Bot is stopped.")
        self.print_log("")
    
    
    # ================================================================
    # 更新EPC-BOT日志到GUI
    # ================================================================
    def print_log(self, text:str):
        self.console.configure(state="normal")
        self.console.insert(END, text + "\n")
        self.console.configure(state="disabled")
        self.console.see(END)


    # ================================================================
    # 关闭GUI时杀死子线程
    # ================================================================
    def on_gui_destroy(self):
        self.stop_bot()
        self.master.destroy()
        