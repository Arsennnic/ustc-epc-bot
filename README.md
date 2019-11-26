# EPC-BOT for USTC
中国科学技术大学EPC系统自动抢课脚本.

## 功能列表

待更新.


## 使用说明

待更新.


## 实现原理

待更新.


## 选课逻辑

### 未达预约上限(4学时)的情况

- 结合筛选规则, 获取可预约课程列表.

- 预约日期最早的课程. 若存在1学时课程与2学时课程的日期相同, 优先选择2学时课程.

- 循环上述操作, 直至到达预约上限(4学时).


### 已达预约上限(4学时)的情况

- 检查已预约课程的总学时. 若未达预约上限(4学时), 则先预约课程至预约上限(4学时).

- 结合筛选规则, 获取可预约课程列表.

- 比较可预约课程与已预约课程的时间先后. 若存在可预约课程的日期早于已预约课程中的最晚日期, 则考虑进行一次课程替换. 若存在1学时课程与2学时课程的日期相同, 优先选择2学时课程.

- 将已预约课程按照日期先后排列, 共有五种学时组合, 分别讨论之:
    + 组合I (1, 1, 1, 1): 
        - 可预约课程为2学时: 
            + 可预约课程日期早于已预约的倒数第2节课, 将倒数第1-2节已预约课程替换为可预约课程.
            + 可预约课程日期晚于已预约的倒数第2节课, 不替换.
        - 可预约课程为1学时: 
            + 将倒数第1节已预约课程替换为可预约课程.
    + 组合II (1, 1, 2): 
        - 可预约课程为2学时: 
            + 将倒数第1节已预约课程替换为可预约课程.
        - 可预约课程为1学时: 
            + 可预约课程日期早于已预约的倒数第2节课, 将倒数第1-2节已预约课程替换为可预约课程.
            + 可预约课程日期晚于已预约的倒数第2节课, 不替换.
    + 组合III (1, 2, 1): 
        - 可预约课程为2学时: 
            + 可预约课程日期早于已预约的倒数第2节课, 将倒数第2节已预约课程替换为可预约课程.
            + 可预约课程日期晚于已预约的倒数第2节课, 不替换.
        - 可预约课程为1学时: 
            + 将倒数第1节已预约课程替换为可预约课程.
    + 组合IV (2, 1, 1): 
        - 可预约课程为2学时: 
            + 可预约课程日期早于已预约的倒数第2节课, 将倒数第1-2节已预约课程替换为可预约课程.
            + 可预约课程日期晚于已预约的倒数第2节课, 不替换.
        - 可预约课程为1学时: 
            + 将倒数第1节已预约课程替换为可预约课程.
    + 组合V (2, 2): 
        - 可预约课程为2学时: 
            + 将倒数第1节已预约课程替换为可预约课程.
        - 可预约课程为1学时: 
            + 可预约课程日期早于已预约的倒数第2节课, 将倒数第1节已预约课程替换为可预约课程(*注: 此操作将导致已预约总学时低于上限*).
            + 可预约课程日期晚于已预约的倒数第2节课, 不替换.

- 循环上述操作, 直至可预约的课程列表为空.


## Q & A

### 使用 PyInstaller 重新打包后, Selenium 运行时有黑色空职台弹出, 如何避免?  
打开 Python\Lib\site-packages\selenium\webdriver\common\service.py 文件, 将 
```
self.process = subprocess.Popen(cmd, env=self.env, close_fds=platform.system() != 'Windows', stdout=self.log_file, stderr=self.log_file, stdin=PIPE)
```
改写成
```
self.process = subprocess.Popen(cmd, stdin=PIPE, stdout=PIPE ,stderr=PIPE, shell=False, creationflags=0x08000000)
```
或直接用工程目录中的 Selenium\service.py 文件替换原生的 service.py 文件
并重新使用 PyInstaller 打包.


## 参考文献

[1] 木华生. 中科大EPC课程爬取\[OL\]. https://blog.csdn.net/qq_28491207/article/details/84261732, 2018.

[2] David Cortesi, William Caban. PyInstaller Manual\[OL\]. https://pyinstaller.readthedocs.io/.

[3] AhmedWas. Getting Rid of ChromeDirver Console Window with PyInstaller\[OL\]. https://stackoverflow.com/questions/52643556/getting-rid-of-chromedirver-console-window-with-pyinstaller, 2018.
