import os, inspect
import time, random
import requests
import json, re
import threading
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from notify import *
from gui import *


class EPCBot(threading.Thread):

    # EPC网站相关url
    URL_ROOT     = "http://epc.ustc.edu.cn/"
    URL_LOGIN    = URL_ROOT + "n_left.asp"
    URL_BOOKED   = URL_ROOT + "record_book.asp"
    URL_BOOKABLE = [
        {"type": "Situational Dialogue",   "url": URL_ROOT + "m_practice.asp?second_id=2001"},
        {"type": "Topical Discussion",     "url": URL_ROOT + "m_practice.asp?second_id=2002"},
        {"type": "Debate",                 "url": URL_ROOT + "m_practice.asp?second_id=2003"},
        {"type": "Drama",                  "url": URL_ROOT + "m_practice.asp?second_id=2004"},
        {"type": "Pronunciation Practice", "url": URL_ROOT + "m_practice.asp?second_id=2007"}
    ]
    
    # 已预约课程总学时
    booked_hours = 0

    # 刷新间隔(s)
    refresh = 2


    def __init__(self, config:dict, ui=None):

        # 设置监听
        super(EPCBot, self).__init__(daemon=True)
        self.is_stopped = threading.Event()
        
        # 初始化相关参数
        self.ustc_id     = config["ustc_id"]
        self.ustc_pwd    = config["ustc_pwd"]
        self.email_addr  = config["email_addr"]
        self.email_pwd   = config["email_pwd"]
        self.type_filter = config["type_filter"]
        self.wday_filter = config["wday_filter"]

        # 初始化GUI(可选)
        self.ui = ui

        # 初始化邮件通知类
        self.email_sender = EmailSender(self.email_addr, self.email_pwd)

        # 初始化桌面通知类
        self.desktop_toaster = DesktopToaster()

        # 开启session会话
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) " 
                + "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/77.0.3865.75 Safari/537.36"
        })


    # ================================================================
    # 绕过验证码登录, 获取Cookies
    # ================================================================  
    def login(self):
        data = {
            "submit_type": "user_login",
            "name": self.ustc_id,
            "pass": self.ustc_pwd,
            "user_type": "2",
            "Submit": "LOG IN"
        }
        self.session.post(url=self.URL_LOGIN, data=data)
        self.cookie = self.session.cookies.get_dict()
        self.print_log(time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time())))
        self.print_log("Login!")
        self.print_log("")


    # ================================================================
    # 获取已预约的课程列表
    # ================================================================  
    def get_booked_epc(self):
        booked_epc = list()
        
        # 发送请求, 失败则立刻返回
        resp = self.session.get(self.URL_BOOKED)
        if (resp.status_code != 200): 
            self.print_log("Failed to fetch booked records.")
            return booked_epc, False

        # 解析获取到的网页源码, 获取表格中每行对应的数据
        html = BeautifulSoup(resp.text, "html.parser")
        table = html.find_all("table")[2]
        tr = table.find_all("tr")

        # 抓取各列中有用的信息
        for i in range(len(tr) - 1):
            td = tr[i].find_all("td")
            booked_epc.append({
                "unit": td[1].text,   # 预约单元
                "prof": td[2].text,   # 教师
                "hour": td[3].text,   # 学时
                "week": td[5].text,   # 教学周
                "wday": td[6].text,   # 星期
                "time": td[7].text,   # 上课时间
                "room": td[8].text    # 上课教室
            })
        return booked_epc, True


    # ================================================================
    # 获取可预约的课程列表
    # ================================================================  
    def get_bookable_epc(self):
        bookable_epc = list()
        success = True

        # 遍历EPC种类, 判断是否允许预约
        for epc in self.type_filter:
            epc_name   = epc["type"]
            epc_enable = epc["enable"]

            # 若不允许预约, 则结束本次循环
            if not epc_enable: continue
            
            # 若允许预约, 则发送请求; 请求失败则结束本次循环
            epc_url = next(item["url"] for item in self.URL_BOOKABLE \
                if item["type"] == epc_name)
            resp = self.session.get(epc_url)
            if (resp.status_code != 200): 
                self.print_log("Failed to fetch bookable classes of %s." % epc_name)
                success = False
                continue

            # 解析获取到的网页源码, 获取表格中每行对应的数据
            html = BeautifulSoup(resp.text, "html.parser")
            table = html.find_all("table")[4]
            tr = table.find_all("tr")

            # 抓取各列中有用的信息
            for i in range(len(tr) - 1):
                td = tr[i].find_all("td")
                bookable_epc.append({
                    "unit": td[0].text,   # 预约单元
                    "prof": td[3].text,   # 教师
                    "hour": td[4].text,   # 学时
                    "week": td[1].text,   # 教学周
                    "wday": td[2].text,   # 星期
                    "time": td[5].text,   # 上课时间
                    "room": td[6].text    # 上课教室
                })
        
        return bookable_epc, success
        
        
    # ================================================================
    # 预约EPC课程
    # ================================================================ 
    def book_epc(self, epc:dict):
        pass


    # ================================================================
    # 取消预约EPC课程
    # ================================================================ 
    def cancel_epc(self, epc:dict):
        pass


    # ================================================================
    # 根据课程时间和学时排序
    # ================================================================ 
    # def sort_info(self, lst):
    #     return sorted(lst, key=lambda item: (
    #         time.mktime(time.strptime(item["date"], "%Y/%m/%d")),
    #         -int(item["credit"])
    #     ))


    # ================================================================
    # 优化课程安排
    # ================================================================ 
    # def optimize_class(self): 
    #     self.get_bookable_epc(self.URL_BOOKABLE)
    #     if len(self.INFO_BOOKABLE) == 0:
    #         return False
    #     success = True
    #     info = self.INFO_BOOKABLE[0]
    #     credit = int(info["credit"])
    #     date = time.mktime(
    #         time.strptime(info["date"], "%Y/%m/%d")
    #     )
    #     if self.CREDIT_BOOKED == [1, 1, 1, 1]:
    #         if credit == 2:
    #             if date < self.DATE_BOOKED[-2]:
    #                 success = self.cancel_class(self.INFO_BOOKED[-1]) and success
    #                 success = self.cancel_class(self.INFO_BOOKED[-1]) and success
    #         else:
    #             success = self.cancel_class(self.INFO_BOOKED[-1]) and success
    #     elif self.CREDIT_BOOKED == [1, 1, 2]:
    #         if credit == 2:
    #             success = self.cancel_class(self.INFO_BOOKED[-1]) and success
    #         else:
    #             if date < self.DATE_BOOKED[-2]:
    #                 success = self.cancel_class(self.INFO_BOOKED[-1]) and success
    #                 success = self.cancel_class(self.INFO_BOOKED[-1]) and success
    #     elif self.CREDIT_BOOKED == [1, 2, 1]:
    #         if credit == 2:
    #             if date < self.DATE_BOOKED[-2]:
    #                 success = self.cancel_class(self.INFO_BOOKED[-2]) and success
    #         else:
    #             success = self.cancel_class(self.INFO_BOOKED[-1]) and success
    #     elif self.CREDIT_BOOKED == [2, 1, 1]:
    #         if credit == 2:
    #             if date < self.DATE_BOOKED[-2]:
    #                 success = self.cancel_class(self.INFO_BOOKED[-1]) and success
    #                 success = self.cancel_class(self.INFO_BOOKED[-1]) and success
    #         else:
    #             success = self.cancel_class(self.INFO_BOOKED[-1]) and success
    #     else:
    #         if credit == 2:
    #             success = self.cancel_class(self.INFO_BOOKED[-1]) and success
    #         else:
    #             if date < self.DATE_BOOKED[-2]:
    #                 success = self.cancel_class(self.INFO_BOOKED[-1]) and success
    #     return success

    
    # ================================================================
    # 将EPC课程列表转化为HTML表格
    # ================================================================ 
    def list2html(self, epc_list:list):
        # 若数组为空, 则返回空字符串
        if len(info_lst) == 0: return ""
        
        # 新建表格
        html_str = "<table></table>"
        html = BeautifulSoup(html_str, "html.parser")
        table = bs_obj.find("table")
        table.attrs = {
            "cellspacing": 0,
            "cellpadding": "4px",
            "border":1
        }

        # 新建表头
        tr = html.new_tag("tr")
        keys = epc_list[0].keys()
        for key in keys:
            th = html.new_tag("th")
            th.string = key.upper()
            tr.append(th)
        table.append(tr)

        # 循环插入EPC课程列表中的数据
        for epc in epc_list:
            tr = html.new_tag("tr")
            for key in keys:
                td = html.new_tag("td")
                td.string = epc[key]
                td.attrs = {"align": "center"}
                tr.append(td)
            table.append(tr)
        
        return bs_obj.prettify()


    # ================================================================
    # 输出日志
    # ================================================================ 
    def print_log(self, log):
        # 日志类型判断, 只接受str或list
        if (type(log) == str): 
            log_str = log
        elif (type(log) == list):
            log_str = json.dumps(log, ensure_ascii=False, indent=4)
        else: return
        print(log_str)

        # 若开启了GUI, 则同时打印到GUI的控制台
        if self.ui == None: return
        self.ui.print_log(log_str)


    # ================================================================
    # 启动EPC-BOT
    # ================================================================
    def run(self):
        self.print_log("EPC-Bot is running...")
        self.print_log("")

        # 登录
        self.is_stopped.clear()
        self.login()

        # 获取EPC预约记录
        booked_epc_old, success = self.get_booked_epc()
        booked_epc_new = booked_epc_old
        self.print_log(time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time())))
        print("Booked classes:")
        self.print_log("Booked classes:")
        self.print_log(booked_epc_new)
        self.print_log("")

        self.desktop_toaster.toast("test", "hello world")

        # 循环获取可预约的EPC课程列表
        bookable_epc_old = None
        while not self.is_stopped.is_set():

            # 重新获取可预约的EPC课程列表
            bookable_epc_new, success = self.get_bookable_epc()
            
            # 若可预约的EPC课程列表发生变动, 输出日志
            if bookable_epc_new != bookable_epc_old:
                self.print_log(time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time())))
                self.print_log("Bookable classes:")
                self.print_log(bookable_epc_new)
                self.print_log("")
                bookable_epc_old = bookable_epc_new

            # 延迟, 加入最大为1s的随机浮动
            time.sleep(self.refresh + random.random())

        self.print_log("EPC-Bot is stopped.")
        self.print_log("")


    # ================================================================
    # 停止EPC-BOT
    # ================================================================
    def stop(self):
        self.is_stopped.set()
