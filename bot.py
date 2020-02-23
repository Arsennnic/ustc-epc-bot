import os, inspect
import time, random
import requests
import json
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
    
    # 允许预约课程总学时上限
    booked_hours_max = 4

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
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) \
                AppleWebKit/537.36 (KHTML, like Gecko) Chrome/77.0.3865.75 Safari/537.36"
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
        self.print_log(time.localtime(time.time()))
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
        form = html.find_all("form")

        # 抓取各列中有用的信息
        for i in range(1, len(tr)):
            td = tr[i].find_all("td")
            booked_epc.append({
                "unit": td[1].get_text(separator=" "),   # 预约单元
                "prof": td[2].get_text(separator=" "),   # 教师
                "hour": td[3].get_text(separator=" "),   # 学时
                "week": td[5].get_text(separator=" "),   # 教学周
                "wday": td[6].get_text(separator=" "),   # 星期
                "date": td[7].get_text(separator=" "),   # 上课时间
                "room": td[8].get_text(separator=" "),   # 上课教室
                "_url": form[i-1].get("action")          # 表单链接
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
            form = html.find_all("form")

            # 抓取各列中有用的信息
            for i in range(1, len(tr)):
                td = tr[i].find_all("td")
                bookable_epc.append({
                    "unit": td[0].get_text(separator=" "),   # 预约单元
                    "prof": td[3].get_text(separator=" "),   # 教师
                    "hour": td[4].get_text(separator=" "),   # 学时
                    "week": td[1].get_text(separator=" "),   # 教学周
                    "wday": td[2].get_text(separator=" "),   # 星期
                    "date": td[5].get_text(separator=" "),   # 上课时间
                    "room": td[6].get_text(separator=" "),   # 上课教室
                    "_url": form[i-1].get("action")          # 表单链接
                })
        
        return bookable_epc, success
        
        
    # ================================================================
    # 预约EPC课程
    # ================================================================ 
    def book_epc(self, epc:dict):
        data = {"submit_type": "book_submit"}
        resp = self.session.post(url=self.URL_ROOT + epc["_url"], data=data)
        return not "操作失败" in resp.text


    # ================================================================
    # 取消预约EPC课程
    # ================================================================ 
    def cancel_epc(self, epc:dict):
        data = {"submit_type": "book_cancel"}
        resp = self.session.post(url=self.URL_ROOT + epc["_url"], data=data)
        return not "操作失败" in resp.text


    # ================================================================
    # 根据上课时间和学时排序: 上课时间从小到大, 学时从大到小
    # ================================================================ 
    def sort_epc(self, epc_list:list):
        return sorted(epc_list, key=lambda epc: (
            time.mktime(time.strptime(epc["date"].split("-")[0], "%Y/%m/%d %H:%M")), 
            -int(epc["hour"])
        ))


    # ================================================================
    # 求两个dict数组的并集
    # ================================================================ 
    def union_epc(self, epc_list_1:list, epc_list_2:list):
        epc_set_1 = set([str(epc) for epc in epc_list_1])
        epc_set_2 = set([str(epc) for epc in epc_list_2])
        return [eval(epc) for epc in list(epc_set_1 | epc_set_2)]


    # ================================================================
    # 求两个dict数组的交集
    # ================================================================ 
    def intersect_epc(self, epc_list_1:list, epc_list_2:list):
        epc_set_1 = set([str(epc) for epc in epc_list_1])
        epc_set_2 = set([str(epc) for epc in epc_list_2])
        return [eval(epc) for epc in list(epc_set_1 & epc_set_2)]


    # ================================================================
    # 求两个dict数组的差集
    # ================================================================ 
    def differ_epc(self, epc_list_1:list, epc_list_2:list):
        epc_set_1 = set([str(epc) for epc in epc_list_1])
        epc_set_2 = set([str(epc) for epc in epc_list_2])
        return [eval(epc) for epc in list(epc_set_1 - epc_set_2)]


    # ================================================================
    # 优化课程安排: 当sum{hour}<=hours_max时, 使max{time}趋于最小 
    # ================================================================ 
    def optimize_epc(self, booked_epc:list, bookable_epc:list): 
        # 取已预约课程和可预约课程列表的并集, 并根据上课时间和学时排序
        all_epc = self.sort_epc(self.union_epc(booked_epc, bookable_epc))

        # 循环检查sum{hour}<=hours_max的边界条件, 将课程填入空数组
        hours = 0
        optimal_epc = list()
        for epc in all_epc:
            if hours >= self.booked_hours_max: break
            hours_tmp = hours + int(epc["hour"])
            if hours_tmp > self.booked_hours_max: continue
            hours = hours_tmp
            optimal_epc.append(epc)
            
        # 确定应该保留/预约/取消预约的课程列表
        reserved_epc  = self.intersect_epc(optimal_epc, booked_epc)
        booking_epc   = self.intersect_epc(optimal_epc, bookable_epc)
        canceling_epc = self.differ_epc(booked_epc, reserved_epc)
        return optimal_epc, self.sort_epc(booking_epc), self.sort_epc(canceling_epc)

    
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
        keys.remove("_url")
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
        if   (type(log) == str): 
            log_str = log
        elif (type(log) == list):
            if len(log) == 0:
                log_str = "  Null"
            else:
                log_str_list = list()
                for i in range(len(log)):
                    unit = log[i]["unit"]
                    date = log[i]["date"].split(" ")
                    log_str_list.append("  (%d) %-10s %s  %s" \
                        % (i + 1, date[0], date[1], unit))
                log_str = "\n".join(log_str_list)
        elif (type(log) == time.struct_time):
            log_str = time.strftime('%Y-%m-%d %H:%M:%S', log)
        else: return
        print(log_str)

        # 若开启了GUI, 则同时打印到GUI的控制台
        if self.ui == None: return
        self.ui.print_log(log_str)


    # ================================================================
    # 启动EPC-BOT
    # ================================================================
    def run(self):
        self.print_log(time.localtime(time.time()))
        self.print_log("EPC-Bot is running...\n")

        # 登录
        self.is_stopped.clear()
        self.login()

        # 获取已预约的EPC课程记录
        booked_epc, success = self.get_booked_epc()
        self.print_log(time.localtime(time.time()))
        if success:
            self.print_log("Your latest schedule:")
            self.print_log(booked_epc)
            self.print_log("")
        else:
            self.print_log("Failed to fetch your latest schedule.")
            self.print_log("Check the network and your basic settings.\n")
            self.is_stopped.set()
            
        while not self.is_stopped.is_set():

            # 获取可预约的EPC课程列表
            bookable_epc, success = self.get_bookable_epc()
            if not success:
                self.print_log(time.localtime(time.time()))
                self.print_log("Failed to fetch latest bookable classes.\n")
                continue

            # 优化EPC课程列表
            optimal_epc, booking_epc, canceling_epc = self.optimize_epc(booked_epc, bookable_epc)
            
            # 若课表无需优化, 则加入最大为1s的随机延迟并进行下一轮循环
            if len(booking_epc) == 0: 
                time.sleep(self.refresh + random.random())
                continue

            # 优化过程, 失败则进行下一轮循环
            self.print_log(time.localtime(time.time()))
            self.print_log("Trying to optimize your schedule...")
            self.print_log("Optimal schedule:")
            self.print_log(optimal_epc)
            success = True
            for epc in canceling_epc:
                success = self.cancel_epc(epc) and success
                if success: 
                    self.print_log("Succeed to cancel <%s>." % epc["unit"])
                else:
                    self.print_log("Failed to cancel <%s>.\n" % epc["unit"])
                    break
            if not success: continue
            for epc in booking_epc:
                success = self.book_epc(epc) and success
                if success: 
                    self.print_log("Succeed to book <%s>." % epc["unit"])
                else:
                    self.print_log("Failed to book <%s>.\n" % epc["unit"])
                    break
            if not success: continue

            # 优化成功, 打印日志, 发送通知
            booked_epc, success = self.get_booked_epc()
            if success:
                self.print_log("Your latest schedule:")
                self.print_log(booked_epc)
                self.print_log("")
                subject = "EPC Schedule Updated"
                brief   = "EPC-Bot has optimized your schedule. Check your mailbox for more infomation."
                detail  = self.list2html(booked_epc)
                self.desktop_toaster.toast(subject, brief)
                self.email_sender.send(subject, detail)
            else:
                self.print_log("Failed to fetch your latest schedule.\n")

        self.print_log(time.localtime(time.time()))
        self.print_log("EPC-Bot is stopped.\n")


    # ================================================================
    # 停止EPC-BOT
    # ================================================================
    def stop(self):
        self.is_stopped.set()
