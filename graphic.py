from tkinter import *
from tkinter.scrolledtext import *
from tkinter.messagebox import showinfo
import json, threading
from epc_bot import *

class GUI:

    def __init__(self, master):
        self.master = master
        self.master.title("EPC-BOT for USTC")
        self.master.protocol('WM_DELETE_WINDOW', self.on_gui_destroy)

        self.frame_basic = Frame(master)
        self.frame_basic.grid(row=0, pady=10)
        Label(self.frame_basic, text="--- Basic Settings ---").grid(row=0, columnspan=4)
        self.label_userid = Label(self.frame_basic, text="Student ID")
        self.label_userid.grid(row=1, column=0, padx=5, pady=2)
        self.text_userid = Entry(self.frame_basic)
        self.text_userid.grid(row=1, column=1, padx=5, pady=2)
        self.label_passwd1 = Label(self.frame_basic, text="Password")
        self.label_passwd1.grid(row=1, column=2, padx=10, pady=2)
        self.text_passwd1 = Entry(self.frame_basic)
        self.text_passwd1.grid(row=1, column=3, padx=5, pady=2)
        self.label_email = Label(self.frame_basic, text="Email Addr.")
        self.label_email.grid(row=2, column=0, padx=5, pady=2)
        self.text_email = Entry(self.frame_basic)
        self.text_email.grid(row=2, column=1, padx=5, pady=2)
        self.label_passwd2 = Label(self.frame_basic, text="Password")
        self.label_passwd2.grid(row=2, column=2, padx=10, pady=2)
        self.text_passwd2 = Entry(self.frame_basic)
        self.text_passwd2.grid(row=2, column=3, padx=5, pady=2)

        self.frame_filter = Frame(master)
        self.frame_filter.grid(row=1, pady=10)
        Label(self.frame_filter, text="--- Filter Settings ---").grid(row=0, columnspan=5)
        with open("config.template.json", "r", encoding="utf-8") as template_file:
            self.filters_all = json.load(template_file)["filter"]
            self.filters_var = list()
            self.cbtn_filters = list()
            row, col = 1, 0
            for i in range(len(self.filters_all)):
                if (i%5 == 0):
                    row = row + 1
                    col = -1
                col = col + 1
                filter_str = self.filters_all[i]["wday"][0:3] + ".\t" + self.filters_all[i]["time"]
                self.filters_var.append(IntVar())
                cbtn_filter = Checkbutton(self.frame_filter, text=filter_str, variable=self.filters_var[i])
                cbtn_filter.grid(row=row, column=col, padx=5, pady=2)
                cbtn_filter.deselect()
                self.cbtn_filters.append(cbtn_filter)

        self.btn_start = Button(master, text="Start", command=self.start_bot)
        self.btn_start.grid(row=2, ipadx=self.btn_start.winfo_width()*5, pady=10)

        self.read_config()

    ## 读取工作目录下存储的配置文件
    def read_config(self):
        try:
            with open("config.json", "r", encoding="utf-8") as config:
                config = json.load(config)
            self.sid = config["sid"]
            self.passwd = config["passwd"]
            self.filters_json = config["filter"]
            self.email_addr = config["email_addr"]
            self.email_pwd = config["email_pwd"]
            self.text_userid.insert(0, self.sid)
            self.text_passwd1.insert(0, self.passwd)
            self.text_email.insert(0, self.email_addr)
            self.text_passwd2.insert(0, self.email_pwd)
            for filter_json in self.filters_json:
                ind = self.filters_all.index(filter_json)
                self.cbtn_filters[ind].select()
            print("Config Load Successfully")
        except:
            for cbtn_filter in self.cbtn_filters:
                cbtn_filter.select()
            print("Config Load Failed")

    ## 写入最新的配置文件
    def write_config(self):
        config = {}
        config["sid"] = self.sid
        config["passwd"] = self.passwd
        config["filter"] = self.filters_json
        config["email_addr"] = self.email_addr
        config["email_pwd"] = self.email_pwd
        with open("config.json", "w", encoding="utf-8") as f:
            json.dump(config, f, ensure_ascii=False, indent=4)
        
    ## 启动EPC-BOT
    def start_bot(self):
        self.sid = self.text_userid.get()
        self.passwd = self.text_passwd1.get()
        self.email_addr = self.text_email.get()
        self.email_pwd = self.text_passwd2.get()
        self.filters_json = list()
        for ind in range(len(self.filters_all)):
            if (self.filters_var[ind].get()):
                self.filters_json.append(self.filters_all[ind])
        if (len(self.sid) and len(self.passwd) \
            and len(self.email_addr) and len(self.email_pwd)):
            self.write_config()
        else:
            showinfo(title="Alert", message="Please fill the blanks in basic settings module!")
            
        self.master.resizable(False, False)
        self.frame_basic.grid_forget()
        self.frame_filter.grid_forget()
        self.btn_start.grid_forget()
        self.console = ScrolledText(self.master)
        self.console.pack()

        self.bot = EPCBot(self.sid, self.passwd, self.filters_json, \
            self.email_addr, self.email_pwd, self)
        self.bot.start()
        
    ## 更新EPC-BOT日志到GUI
    def update_log(self, text):
        self.console.configure(state="normal")
        self.console.insert(END, text + "\n")
        self.console.configure(state="disabled")
        self.console.see(END)

    ## 关闭GUI时杀死子线程
    def on_gui_destroy(self):
        self.master.destroy()
        if self.bot:
            self.bot.stop()
        