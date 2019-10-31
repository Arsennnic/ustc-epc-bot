import requests, time, re, json
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from email_sender import EmailSender


class EPCBot:
    WEBDRIVER = None
    EMAILSENDER = None
    COOKIE = None
    URL_LOGIN = 'http://epc.ustc.edu.cn/n_left.asp'
    URL_BOOKED = 'http://epc.ustc.edu.cn/record_book.asp'
    URL_BOOKABLE = [
        'http://epc.ustc.edu.cn/m_practice.asp?second_id=2001',  # Situational Dialogue
        'http://epc.ustc.edu.cn/m_practice.asp?second_id=2002',  # Topical Discussion
        'http://epc.ustc.edu.cn/m_practice.asp?second_id=2003',  # Debate
        'http://epc.ustc.edu.cn/m_practice.asp?second_id=2004',  # Drama
        'http://epc.ustc.edu.cn/m_practice.asp?second_id=2007',  # Pronunciation Practice
    ]
    TYPE_BOOKABLE = ['Situational Dialogue', 'Topical Discussion', 
        'Debate', 'Drama', 'Pronunciation Practice'
    ]
    SID = None
    PASSWD = None
    FILTER = [
        # Avaliable time for one-credit classes
        {'wday': 'Monday', 'time': '08:25-09:15'},
        {'wday': 'Monday', 'time': '16:40-17:30'},
        {'wday': 'Tuesday', 'time': '08:25-09:15'},
        {'wday': 'Tuesday', 'time': '16:40-17:30'},
        {'wday': 'Wednesday', 'time': '08:25-09:15'},
        {'wday': 'Wednesday', 'time': '16:40-17:30'},
        {'wday': 'Thursday', 'time': '08:25-09:15'},
        {'wday': 'Thursday', 'time': '16:40-17:30'},
        {'wday': 'Friday', 'time': '08:25-09:15'},
        {'wday': 'Friday', 'time': '16:40-17:30'},
        # Avaliable time for two-credit classes
        {'wday': 'Monday', 'time': '09:45-11:25'},
        {'wday': 'Monday', 'time': '14:30-16:10'},
        {'wday': 'Monday', 'time': '19:00-20:40'},
        {'wday': 'Tuesday', 'time': '09:45-11:25'},
        {'wday': 'Tuesday', 'time': '14:30-16:10'},
        {'wday': 'Tuesday', 'time': '19:00-20:40'},
        {'wday': 'Wednesday', 'time': '09:45-11:25'},
        {'wday': 'Wednesday', 'time': '14:30-16:10'},
        {'wday': 'Wednesday', 'time': '19:00-20:40'},
        {'wday': 'Thursday', 'time': '09:45-11:25'},
        {'wday': 'Thursday', 'time': '14:30-16:10'},
        {'wday': 'Thursday', 'time': '19:00-20:40'},
        {'wday': 'Friday', 'time': '09:45-11:25'},
        {'wday': 'Friday', 'time': '14:30-16:10'},
        {'wday': 'Friday', 'time': '19:00-20:40'},
    ]
    INFO_BOOKABLE = []
    INFO_BOOKED = []
    UNIT_BOOKED = []
    DATE_BOOKED = []
    CREDIT_BOOKED = []
    CREDITS = 0     # Credits of booked classes


    def __init__(self, sid, passwd, filtr, email_addr, email_pwd):
        self.SID = sid
        self.PASSWD = passwd
        self.FILTER = filtr
        self.EMAILSENDER = EmailSender(email_addr, email_pwd)
        options = Options()
        options.add_argument("--no-sandbox")
        options.add_argument("--headless")
        options.add_argument("--disable-gpu")
        self.WEBDRIVER = webdriver.Chrome(chrome_options=options, 
            executable_path="./selenium/chromedriver.exe"
        )
        
    ## 绕过验证码, 获取Cookies
    def get_cookies(self):
        session = requests.Session()
        data = {
            'submit_type': 'user_login',
            'name': self.SID,
            'pass': self.PASSWD,
            'user_type': '2',
            'Submit': 'LOG IN'
        }
        session.post(url=self.URL_LOGIN, data=data)
        self.COOKIE = session.cookies.get_dict()

    ## 将Cookies赋给headless浏览器
    def set_cookies(self):
        for key, value in self.COOKIE.items():
            self.WEBDRIVER.add_cookie({'name': key, 'value': value})
        self.WEBDRIVER.refresh()

    ## 登录
    def login(self):
        self.get_cookies()
        self.WEBDRIVER.get(self.URL_LOGIN)
        self.set_cookies()
        print(time.strftime("%Y/%m/%d %H:%M:%S", time.localtime()))
        print('Login!\n')

    ## 获取已预约的课程列表
    def get_booked_classes(self):
        info_booked_backup = self.INFO_BOOKED
        self.INFO_BOOKED = list()
        self.UNIT_BOOKED = list()
        self.DATE_BOOKED = list()
        self.CREDIT_BOOKED = list()
        self.CREDITS = 0
        self.WEBDRIVER.get(self.URL_BOOKED)
        WebDriverWait(self.WEBDRIVER, 20).until(
            EC.visibility_of_element_located((By.TAG_NAME, 'tbody'))
        )
        table = self.WEBDRIVER.find_elements_by_tag_name('tbody')[2]
        items = table.find_elements_by_tag_name('tr')
        for i in range(1, len(items)):
            info = items[i].find_elements_by_tag_name('td')
            date = info[6].text.split('\n')[0]
            self.INFO_BOOKED.append({
                'unit': info[0].text,
                'type': 'Unknown',
                'week': re.compile(r'\d+').findall(info[4].text)[0],
                'wday': time.strftime('%A', time.strptime(date, '%Y/%m/%d')),
                'date': date,
                'time': info[6].text.split('\n')[1],
                'teacher': info[1].text,
                'credit': info[2].text,
                'room': info[7].text
            })
            self.CREDITS = self.CREDITS + int(info[2].text)
            self.CREDIT_BOOKED.append(int(info[2].text))
            self.UNIT_BOOKED.append(info[0].text)
            self.DATE_BOOKED.append(
                time.mktime(time.strptime(date, '%Y/%m/%d')
            ))
        if not (self.INFO_BOOKED == info_booked_backup):
            if len(info_booked_backup) > 0:
                text = '''
                    <b>NEW CLASS BOOKED!</b>
                    <p>Previous class schedule:</p>
                '''
                text = text + self.trans_html(info_booked_backup)
                text = text + '''
                    <p>Current class schedule:</p>
                '''
                text = text + self.trans_html(self.INFO_BOOKED)
                self.EMAILSENDER.send(text)
            print(time.strftime("%Y/%m/%d %H:%M:%S", time.localtime()))
            print('Booked classes (%d):' % len(self.INFO_BOOKED))
            print(json.dumps(self.INFO_BOOKED, ensure_ascii=False, indent=4))
            print('')
        if self.CREDITS < 4:
            self.fill_class()

    ## 获取可预约的课程列表
    def get_bookable_class(self, urls):
        self.INFO_BOOKABLE = list()
        for url in urls:
            self.WEBDRIVER.get(url)
            WebDriverWait(self.WEBDRIVER, 20).until(
                EC.visibility_of_element_located((By.TAG_NAME, 'tbody'))
            )
            table = self.WEBDRIVER.find_elements_by_tag_name('tbody')[4]
            items = table.find_elements_by_tag_name('tr')
            for i in range(1, len(items)):
                info = items[i].find_elements_by_tag_name('td')
                unit = info[0].text
                date = info[5].text.split('\n')[0]
                strp = time.strptime(date, '%Y/%m/%d')
                stamp = time.mktime(strp)
                wday = time.strftime('%A', strp)
                filtr = {
                    'wday': wday,
                    'time': info[5].text.split('\n')[1]
                }
                # 条件: 课程时间符合筛选条件/课程时间未选其它课程/相同课程未预约过
                if filtr in self.FILTER and not (stamp in self.DATE_BOOKED) \
                    and not (unit in self.UNIT_BOOKED):
                    if not (self.CREDITS == 4 and stamp >= self.DATE_BOOKED[-1]):
                        self.INFO_BOOKABLE.append({
                            'unit': unit,
                            'type': self.TYPE_BOOKABLE[self.URL_BOOKABLE.index(url)],
                            'week': re.compile(r'\d+').findall(info[1].text)[0],
                            'wday': wday,
                            'date': date,
                            'time': info[5].text.split('\n')[1],
                            'teacher': info[3].text,
                            'credit': info[4].text,
                            'room': info[6].text
                        })
        self.INFO_BOOKABLE = self.sort_info(self.INFO_BOOKABLE)
        print(time.strftime("%Y/%m/%d %H:%M:%S", time.localtime()))
        print('Bookable classes (%d):' % len(self.INFO_BOOKABLE))
        print(json.dumps(self.INFO_BOOKABLE, ensure_ascii=False, indent=4))
        print('')

    ## 根据课程时间和学时排序
    def sort_info(self, lst):
        return sorted(lst, key=lambda item: (
            time.mktime(time.strptime(item['date'], '%Y/%m/%d')),
            -int(item['credit'])
        ))

    ## 将课程信息转化为HTML表格
    def trans_html(self, info_lst):
        if len(info_lst) == 0:
            return ''
        keys = info_lst[0].keys()
        html = '<table></table>'
        bs_obj = BeautifulSoup(html, 'lxml')
        table = bs_obj.find('table')
        table.attrs = {
            'cellspacing': 0,
            'cellpadding': '4px',
            'border':1
        }
        tr = bs_obj.new_tag('tr')
        for key in keys:
            th = bs_obj.new_tag('th')
            th.string = '%s' % key.upper()
            tr.append(th)
        table.append(tr)
        for info in info_lst:
            tr = bs_obj.new_tag('tr')
            for key in keys:
                td = bs_obj.new_tag('td')
                td.string = '%s' % info[key]
                td.attrs = {'align': 'center'}
                tr.append(td)
            table.append(tr)
        return bs_obj.prettify()

    ## 择优预约课程至学时上限
    def fill_class(self):
        if self.CREDITS == 4:
            return
        elif self.CREDITS == 3:
            self.get_bookable_class([self.URL_BOOKABLE[0]])
        else:
            self.get_bookable_class(self.URL_BOOKABLE)
        success = self.book_class(self.INFO_BOOKABLE[0])
        self.get_booked_classes()

    ## 预约课程 
    def book_class(self, info_bookable):
        type_id = self.TYPE_BOOKABLE.index(info_bookable['type'])
        self.WEBDRIVER.get(self.URL_BOOKABLE[type_id])
        WebDriverWait(self.WEBDRIVER, 20).until(
            EC.visibility_of_element_located((By.TAG_NAME, 'tbody'))
        )
        table = self.WEBDRIVER.find_elements_by_tag_name('tbody')[4]
        items = table.find_elements_by_tag_name('tr')
        for i in range(1, len(items)):
            info = items[i].find_elements_by_tag_name('td')
            unit0 = info_bookable['unit']
            date0 = info_bookable['date']
            time0 = info_bookable['time']
            unit1 = info[0].text
            date1 = info[5].text.split('\n')[0]
            time1 = info[5].text.split('\n')[1]
            if unit0 == unit1 and date0 == date1 and time0 == time1:
                print(time.strftime("%Y/%m/%d %H:%M:%S", time.localtime()))
                print('Trying to book \'%s\'...' % unit0)
                try:
                    button = items[i].find_elements_by_tag_name('input')[1]
                    button.click()
                    WebDriverWait(self.WEBDRIVER, 10).until(EC.alert_is_present())
                    self.WEBDRIVER.switch_to.alert.accept()
                    success = True
                    print('Done.\n')
                except:
                    success = False
                    print('Failed.\n')
                break
        self.get_booked_classes()
        return success

    ## 取消课程
    def cancel_class(self, info_booked):
        self.WEBDRIVER.get(self.URL_BOOKED)
        WebDriverWait(self.WEBDRIVER, 20).until(
            EC.visibility_of_element_located((By.TAG_NAME, 'tbody'))
        )
        table = self.WEBDRIVER.find_elements_by_tag_name('tbody')[2]
        items = table.find_elements_by_tag_name('tr')
        for i in range(1, len(items)):
            info = items[i].find_elements_by_tag_name('td')
            unit0 = info_booked['unit']
            date0 = info_booked['date']
            time0 = info_booked['time']
            unit1 = info[0].text
            date1 = info[6].text.split('\n')[0]
            time1 = info[6].text.split('\n')[1]
            if unit0 == unit1 and date0 == date1 and time0 == time1:
                print(time.strftime("%Y/%m/%d %H:%M:%S", time.localtime()))
                print('Trying to cancel \'%s\'...' % unit0)
                try:
                    button = items[i].find_elements_by_tag_name('input')[1]
                    button.click()
                    WebDriverWait(self.WEBDRIVER, 10).until(EC.alert_is_present())
                    self.WEBDRIVER.switch_to.alert.accept()
                    success = True
                    print('Done.\n')
                except:
                    success = False
                    print('Failed.\n')
                break
        self.get_booked_classes()
        return success

    ## 优化课程安排
    def optimize_class(self): 
        self.get_bookable_class(self.URL_BOOKABLE)
        if len(self.INFO_BOOKABLE) == 0:
            return False
        success = True
        info = self.INFO_BOOKABLE[0]
        credit = int(info['credit'])
        date = time.mktime(
            time.strptime(info['date'], '%Y/%m/%d')
        )
        if self.CREDIT_BOOKED == [1, 1, 1, 1]:
            if credit == 2:
                if date < self.DATE_BOOKED[-2]:
                    success = self.cancel_class(self.INFO_BOOKED[-1]) and success
                    success = self.cancel_class(self.INFO_BOOKED[-1]) and success
            else:
                success = self.cancel_class(self.INFO_BOOKED[-1]) and success
        elif self.CREDIT_BOOKED == [1, 1, 2]:
            if credit == 2:
                success = self.cancel_class(self.INFO_BOOKED[-1]) and success
            else:
                if date < self.DATE_BOOKED[-2]:
                    success = self.cancel_class(self.INFO_BOOKED[-1]) and success
                    success = self.cancel_class(self.INFO_BOOKED[-1]) and success
        elif self.CREDIT_BOOKED == [1, 2, 1]:
            if credit == 2:
                if date < self.DATE_BOOKED[-2]:
                    success = self.cancel_class(self.INFO_BOOKED[-2]) and success
            else:
                success = self.cancel_class(self.INFO_BOOKED[-1]) and success
        elif self.CREDIT_BOOKED == [2, 1, 1]:
            if credit == 2:
                if date < self.DATE_BOOKED[-2]:
                    success = self.cancel_class(self.INFO_BOOKED[-1]) and success
                    success = self.cancel_class(self.INFO_BOOKED[-1]) and success
            else:
                success = self.cancel_class(self.INFO_BOOKED[-1]) and success
        else:
            if credit == 2:
                success = self.cancel_class(self.INFO_BOOKED[-1]) and success
            else:
                if date < self.DATE_BOOKED[-2]:
                    success = self.cancel_class(self.INFO_BOOKED[-1]) and success
        return success

    ## 启动EPC-BOT
    def start(self):
        self.login()
        self.get_booked_classes()
        while True:
            self.fill_class()
            self.optimize_class()
