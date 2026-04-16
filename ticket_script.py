# coding: utf-8
from json import loads
from time import sleep, time
from pickle import dump, load
from os.path import exists
from selenium import webdriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.common import exceptions
from selenium.common.exceptions import NoSuchWindowException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options


class Concert(object):
    def __init__(self, date, session, price, real_name, nick_name, ticket_num, viewer_person, damai_url, target_url, driver_path="chromedriver.exe"):
        self.date = date          # 日期序号优先级，如 [1,2] 表示优先选第1个日期，第2个备选
        self.session = session    # 场次序号优先级，如 [1,2]
        self.price = price        # 票价序号优先级，如 [1,2]
        self.real_name = real_name
        self.status = 0
        self.time_start = 0
        self.time_end = 0
        self.num = 0
        self.ticket_num = ticket_num   # 购买票数
        self.viewer_person = viewer_person  # 观演人序号优先级，如 [1,2]
        self.nick_name = nick_name
        self.damai_url = damai_url
        self.target_url = target_url
        self.driver_path = driver_path
        self.driver = None

    def isClassPresent(self, item, name, ret=False):
        try:
            result = item.find_element(by=By.CLASS_NAME, value=name)
            if ret:
                return result
            else:
                return True
        except:
            return False

    # 获取账号的 cookie 信息（手动扫码登录）
    def get_cookie(self):
        self.driver.get(self.damai_url)
        print("### 请点击登录 ###")
        self.driver.find_element(by=By.CLASS_NAME, value='login-user').click()
        while self.driver.title.find('大麦网-全球演出赛事官方购票平台') != -1:
            sleep(1)
        print("### 请扫码登录 ###")
        while self.driver.title == '大麦登录':
            sleep(1)
        dump(self.driver.get_cookies(), open("cookies.pkl", "wb"))
        print("### Cookie 保存成功 ###")

    # 载入已保存的 cookie
    def set_cookie(self):
        try:
            cookies = load(open("cookies.pkl", "rb"))
            for cookie in cookies:
                cookie_dict = {
                    'domain': '.damai.cn',
                    'name': cookie.get('name'),
                    'value': cookie.get('value'),
                    "expires": "",
                    'path': '/',
                    'httpOnly': False,
                    'HostOnly': False,
                    'Secure': False
                }
                self.driver.add_cookie(cookie_dict)
            print("### 载入 Cookie ###")
        except Exception as e:
            print(e)

    # 登录流程
    def login(self):
        print("### 开始登录 ###")
        # 必须先加载 Cookie 到大麦主域，再访问目标页面
        self.driver.get(self.damai_url)
        sleep(1)
        self.set_cookie()
        # 添加完 Cookie 后再跳转目标页面
        self.driver.get(self.target_url)
        # 等待购买按钮出现（页面能正常加载的标志）
        try:
            WebDriverWait(self.driver, 30, 0.5).until(
                EC.presence_of_element_located((By.CLASS_NAME, 'buy__button'))
            )
            print("### 页面加载成功 ###")
        except Exception as e:
            print(f">>> 等待购买按钮超时: {e}，继续尝试...")

    # 进入演出页面并初始化浏览器
    def enter_concert(self):
        print("### 打开浏览器，进入大麦网 ###")
        driver_exe = r"C:\Users\tang'wen'jing\.wdm\drivers\chromedriver\win64\146.0.7680.165\chromedriver-win32\chromedriver.exe"
        if not exists('cookies.pkl'):
            options = Options()
            options.add_argument('--disable-blink-features=AutomationControlled')
            options.add_argument('--blink-settings=imagesEnabled=false')
            options.page_load_strategy = 'eager'
            self.driver = webdriver.Chrome(service=Service(driver_exe), options=options)
            self.get_cookie()
            self.driver.quit()

        # 使用已有 Cookie 启动浏览器
        options = Options()
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument('--blink-settings=imagesEnabled=false')
        options.page_load_strategy = 'eager'

        self.driver = webdriver.Chrome(service=Service(driver_exe), options=options)

        # 页面加载后注入 JS 去除自动化检测
        try:
            self.driver.execute_script("""
                Object.defineProperty(navigator, 'webdriver', {
                    get: function() { return undefined; },
                    configurable: true
                });
                Object.defineProperty(navigator, 'plugins', {
                    get: function() { return [1, 2, 3, 4, 5]; },
                    configurable: true
                });
                window.navigator.chrome = { runtime: {} };
                const _origQuery = window.navigator.permissions.query;
                window.navigator.permissions.query = function(p) {
                    if (p.name === 'notifications') return Promise.resolve({state: Notification.permission});
                    return _origQuery(p);
                };
            """)
            print(">>> 反爬虫 JS 注入成功")
        except Exception as e:
            print(f">>> JS 注入跳过: {e}")

        self.login()
        self.driver.refresh()

    # 点击工具函数
    def click_util(self, btn, locator):
        while True:
            btn.click()
            try:
                return WebDriverWait(self.driver, 1, 0.1).until(EC.presence_of_element_located(locator))
            except:
                continue

    def is_browser_alive(self):
        """检查浏览器是否还在运行"""
        try:
            _ = self.driver.current_url
            return True
        except:
            return False

    # 核心抢票逻辑
    def choose_ticket(self):
        print("### 进入抢票界面 ###")
        while self.driver.title.find('订单确认') == -1:
            # 每轮开始前检查浏览器状态
            if not self.is_browser_alive():
                print("!!! 检测到浏览器已被关闭，暂停中...")
                return  # 返回主循环，主循环会处理暂停流程

            self.num += 1
            print(f"--- 第 {self.num} 轮尝试 ---")

            if self.driver.current_url.find("buy.damai.cn") != -1:
                print(">>> 已到达购买页面，跳出刷新循环")
                break

            # 关闭实名制遮罩（在整个页面范围内查找）
            try:
                popups = self.driver.find_elements(by=By.XPATH, value="//div[@class='realname-popup']//div[@class='operate']//div[@class='button']")
                if popups:
                    popups[0].click()
                    print(">>> 已关闭实名制遮罩")
            except:
                pass

            # ---------- 先检测是否需要点击"不，选座购票" ----------
            try:
                seat_link = WebDriverWait(self.driver, 3, 0.5).until(
                    EC.presence_of_element_located((By.XPATH, "//*[contains(text(),'不，选座购票')]"))
                )
                print(">>> 检测到'不，选座购票'选项，点击进入购买页")
                seat_link.click()
                sleep(2)
                continue  # 点击后等待页面跳转，重新检测按钮
            except:
                pass

            # 用一个变量记录当前是哪个按钮对象
            current_buybutton = None

            # 直接等待购买按钮出现（不再依赖 #app 元素）
            try:
                buybutton = WebDriverWait(self.driver, 5, 0.1).until(
                    EC.presence_of_element_located((By.CLASS_NAME, 'buy__button'))
                )
                sleep(0.5)
                buybutton_text: str = buybutton.text
                print(f">>> 当前按钮文字: [{buybutton_text}]")
                current_buybutton = buybutton
            except Exception as e:
                # Selenium 找不到按钮，改用 JS 查找
                print(f">>> Selenium 找不到按钮，改用 JS 检测: {e}")
                try:
                    result = self.driver.execute_script(
                        "const b = document.querySelector('.buy__button'); return b ? {text: b.innerText, exists: true} : {exists: false};"
                    )
                    if not result or not result.get('exists'):
                        # 再次尝试找"不，选座购票"（可能是隐式刷新导致的暂时找不到）
                        try:
                            seat_link = self.driver.find_element(By.XPATH, "//*[contains(text(),'不，选座购票')]")
                            if seat_link:
                                print(">>> JS 也找不到购买按钮，找到'不，选座购票'，点击进入")
                                seat_link.click()
                                sleep(2)
                                continue
                        except:
                            pass
                        print("!!! JS 也找不到购买按钮和选座链接，页面可能未完全加载，重新刷新")
                        self.driver.get(self.target_url)
                        sleep(1)
                        continue
                    buybutton_text = result['text']
                    current_buybutton = self.driver.execute_script(
                        "return document.querySelector('.buy__button');"
                    )
                    print(f">>> JS 检测到按钮文字: [{buybutton_text}]")
                except Exception as js_e:
                    print(f"!!! JS 执行失败: {js_e}")
                    self.driver.get(self.target_url)
                    sleep(1)
                    continue

            if "即将开抢" in buybutton_text:
                self.status = 2
                print(">>> 尚未开售，等待中...")
                sleep(2)
                continue

            if "缺货" in buybutton_text:
                print("!!! 票已缺货")
                sleep(2)
                continue

            if "选座购买" in buybutton_text:
                print(">>> 检测到【选座购买】，直接点击进入选座")
                try:
                    current_buybutton.click()
                except:
                    self.driver.execute_script(
                        "document.querySelector('.buy__button').click();"
                    )
                self.status = 5
                print("### 请自行在浏览器中选择座位和票价 ###")
                return

            if "立即预订" not in buybutton_text and "立即购买" not in buybutton_text:
                print(f"!!! 按钮不是预订/购买，当前为: [{buybutton_text}]，等待 2 秒后重试")
                sleep(2)
                continue

            print(">>> 点击购买按钮，进入选票流程")
            try:
                current_buybutton.click()
            except:
                self.driver.execute_script(
                    "document.querySelector('.buy__button').click();"
                )

            print(">>> 等待 sku-pop-wrapper 弹窗...")
            box = WebDriverWait(self.driver, 2, 0.1).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, '.sku-pop-wrapper'))
            )
            print(">>> 选票弹窗已出现")

            try:
                # ---------- 日期选择 ----------
                print(">>> 正在选择日期...")
                toBeClicks = []
                try:
                    date = WebDriverWait(box, 2, 0.1).until(
                        EC.presence_of_element_located((By.CLASS_NAME, 'bui-dm-sku-calendar'))
                    )
                except Exception as e:
                    print(f"!!! 日期选择器未找到: {e}")
                    self.driver.get(self.target_url)
                    continue

                if date is not None:
                    date_list = date.find_elements(by=By.CLASS_NAME, value='bui-calendar-day-box')
                    if len(date_list) == 0:
                        print("!!! 日期列表为空，可能页面结构变化")
                        self.driver.get(self.target_url)
                        continue
                    print(f">>> 发现 {len(date_list)} 个日期选项，尝试选择第 {self.date[0]} 个")
                    for i in self.date:
                        if i > len(date_list):
                            print(f"!!! 日期序号 {i} 超出范围，共 {len(date_list)} 个")
                            continue
                        j: WebElement = date_list[i - 1]
                        toBeClicks.append(j)
                        break
                    for i in toBeClicks:
                        i.click()
                        sleep(0.05)
                    print(">>> 日期选择完成")

                # ---------- 选定场次 ----------
                print(">>> 正在选择场次...")
                session = WebDriverWait(box, 2, 0.1).until(
                    EC.presence_of_element_located((By.CLASS_NAME, 'sku-times-card'))
                )
                session_list = session.find_elements(by=By.CLASS_NAME, value='bui-dm-sku-card-item')
                if len(session_list) == 0:
                    print("!!! 场次列表为空")
                    self.driver.get(self.target_url)
                    continue
                print(f">>> 发现 {len(session_list)} 个场次选项")

                toBeClicks = []
                for i in self.session:
                    if i > len(session_list):
                        i = len(session_list)
                    j: WebElement = session_list[i - 1]
                    k = self.isClassPresent(j, 'item-tag', True)
                    if k:
                        if k.text == '无票':
                            print(f">>> 场次 {i} 无票，跳过")
                            continue
                        elif k.text == '预售':
                            toBeClicks.append(j)
                            break
                        elif k.text == '惠':
                            toBeClicks.append(j)
                            break
                    else:
                        toBeClicks.append(j)
                        break

                if not toBeClicks:
                    print("!!! 没有可选的场次")
                    self.driver.get(self.target_url)
                    continue

                for i in toBeClicks:
                    i.click()
                    sleep(0.05)
                print(">>> 场次选择完成")

                # ---------- 选定票档 ----------
                print(">>> 正在选择票档...")
                toBeClicks = []
                price = WebDriverWait(box, 2, 0.1).until(
                    EC.presence_of_element_located((By.CLASS_NAME, 'sku-tickets-card'))
                )
                price_list = price.find_elements(by=By.CLASS_NAME, value='bui-dm-sku-card-item')
                if len(price_list) == 0:
                    print("!!! 票档列表为空")
                    self.driver.get(self.target_url)
                    continue
                print(f">>> 发现 {len(price_list)} 个票档选项")

                for i in self.price:
                    if i > len(price_list):
                        i = len(price_list)
                    j = price_list[i - 1]
                    k = self.isClassPresent(j, 'item-tag', True)
                    if k:
                        print(f">>> 票档 {i} 有标签 [{k.text}]，跳过")
                        continue
                    else:
                        toBeClicks.append(j)
                        break

                if not toBeClicks:
                    print("!!! 没有可选的票档")
                    self.driver.get(self.target_url)
                    continue

                for i in toBeClicks:
                    i.click()
                    sleep(0.1)
                print(">>> 票档选择完成")

                buybutton = box.find_element(by=By.CLASS_NAME, value='sku-footer-buy-button')
                sleep(1.0)
                buybutton_text = buybutton.text
                if buybutton_text == "":
                    print("!!! 提交按钮文字为空，可能页面未加载完成，等待后重试")
                    sleep(2)
                    continue

                try:
                    WebDriverWait(box, 2, 0.1).until(
                        EC.presence_of_element_located((By.CLASS_NAME, 'bui-dm-sku-counter'))
                    )
                except:
                    print("!!! 购票数量控件未出现")
                    self.driver.get(self.target_url)
                    continue

            except NoSuchWindowException:
                print("!!! 浏览器已被关闭，暂停中...")
                return
            except Exception as e:
                # 先检查是否是浏览器关闭
                if not self.is_browser_alive():
                    print("!!! 浏览器已被关闭，暂停中...")
                    return
                print(f"!!! 选择日期/场次/票档出错: {e}")
                self.driver.get(self.target_url)
                continue

            print(">>> 正在选择票数...")
            try:
                ticket_num_up = box.find_element(by=By.CLASS_NAME, value='plus-enable')
                print(f">>> 点击加号按钮 {self.ticket_num - 1} 次")
            except:
                if buybutton_text == "选座购买":
                    buybutton.click()
                    self.status = 5
                    print("### 请自行选择位置和票价 ###")
                    break
                elif buybutton_text == "提交缺货登记":
                    print("### 票已被抢完，持续捡漏中... ###")
                    sleep(2)
                    continue
                else:
                    print(f"!!! ticket_num_up 加号按钮找不到，按钮文字: [{buybutton_text}]")
                    sleep(2)
                    continue

            if buybutton_text == "立即预订" or buybutton_text == "立即购买" or buybutton_text == '确定':
                for i in range(self.ticket_num - 1):
                    ticket_num_up.click()
                    sleep(0.05)
                print(">>> 点击提交订单按钮")
                buybutton.click()
                self.status = 4
                print(">>> 等待跳转到订单确认页面...")
                WebDriverWait(self.driver, 3, 0.1).until(EC.title_contains("确认"))
                print(">>> 成功进入订单确认页面！")
                break
            else:
                print(f"!!! 未定义按钮：{buybutton_text}")
                sleep(2)
                continue

    # 确认订单 + 选择观演人
    def check_order(self):
        if self.status in [3, 4, 5]:
            toBeClicks = []
            WebDriverWait(self.driver, 5, 0.1).until(
                EC.presence_of_element_located(
                    (By.XPATH, '//*[@id="dmViewerBlock_DmViewerBlock"]/div[2]/div/div')
                )
            )
            people = self.driver.find_elements(
                By.XPATH, '//*[@id="dmViewerBlock_DmViewerBlock"]/div[2]/div/div'
            )
            sleep(0.2)

            for i in self.viewer_person:
                if i > len(people):
                    break
                j = people[i - 1]
                j.click()
                sleep(0.05)

            WebDriverWait(self.driver, 5, 0.1).until(
                EC.presence_of_element_located(
                    (By.XPATH, '//*[@id="dmOrderSubmitBlock_DmOrderSubmitBlock"]/div[2]/div/div[2]/div[3]/div[2]')
                )
            )
            comfirmBtn = self.driver.find_element(
                By.XPATH, '//*[@id="dmOrderSubmitBlock_DmOrderSubmitBlock"]/div[2]/div/div[2]/div[3]/div[2]'
            )
            sleep(0.5)
            comfirmBtn.click()

            print("### 等待跳转到付款界面，如长期不跳转可选择 Ctrl+C 重新抢票 ###")

            while True:
                try:
                    WebDriverWait(self.driver, 4, 0.1).until(EC.title_contains('支付宝'))
                except:
                    step = input("等待跳转到支付宝页面，请输入 1 确认成功 / 2 重新抢票: ")
                    if step == '1':
                        break
                    else:
                        raise Exception("### Error: 长期跳转不到付款界面 ###")
                break

            self.status = 6
            self.time_end = time()
            print("### 成功提交订单，请手动支付 ###")


# ==================== 主入口 ====================
if __name__ == '__main__':
    try:
        with open('./config.json', 'r', encoding='utf-8') as f:
            config = loads(f.read())

        con = Concert(
            config['date'],
            config['sess'],
            config['price'],
            config['real_name'],
            config['nick_name'],
            config['ticket_num'],
            config['viewer_person'],
            config['damai_url'],
            config['target_url'],
            config['driver_path']
        )
        con.enter_concert()

    except Exception as e:
        print(e)
        exit(1)

    while True:
        # 检查浏览器是否被关闭
        if not con.is_browser_alive():
            print("\n" + "=" * 50)
            print("!!! 检测到浏览器已被关闭，脚本暂停中...")
            print(">>> 请重新打开 Chrome 浏览器")
            print(">>> 浏览器打开后，按回车键继续抢票")
            print("=" * 50 + "\n")
            input()
            try:
                con.enter_concert()
                print(">>> 浏览器已重新启动，继续抢票")
            except Exception as e:
                print(f"!!! 重新启动浏览器失败: {e}")
                continue

        try:
            con.choose_ticket()
            con.check_order()
        except KeyboardInterrupt:
            print("### 用户中断抢票 ###")
            exit(0)
        except NoSuchWindowException:
            # 浏览器被关闭，触发暂停流程
            print("\n!!! 检测到浏览器已被关闭")
            print(">>> 请重新打开 Chrome 浏览器")
            print(">>> 浏览器打开后，按回车键继续\n")
            input()
            try:
                con.enter_concert()
                print(">>> 浏览器已重新启动，继续抢票")
            except Exception as e:
                print(f"!!! 重新启动浏览器失败: {e}")
                continue
        except Exception as e:
            print(f"!!! 本轮出错: {e}")
            try:
                # 先检查浏览器是否还活着
                if not con.is_browser_alive():
                    print("\n!!! 浏览器已关闭，请重新打开浏览器后按回车继续")
                    input()
                    con.enter_concert()
                    print(">>> 浏览器已重新启动，继续抢票")
                    continue
                con.driver.get(con.target_url)
                print(">>> 已返回详情页，准备下一轮...")
            except NoSuchWindowException:
                print("\n!!! 浏览器已关闭，请重新打开浏览器后按回车继续")
                input()
                try:
                    con.enter_concert()
                    print(">>> 浏览器已重新启动，继续抢票")
                except Exception as e2:
                    print(f"!!! 重新启动浏览器失败: {e2}")
                continue
            except Exception as e2:
                print(f"!!! 无法回到详情页: {e2}，尝试重启浏览器")
                try:
                    con.enter_concert()
                except Exception as e3:
                    print(f"!!! 重启浏览器失败: {e3}")
                continue
            continue

        if con.status == 6:
            print("### 经过 %d 轮奋斗，共耗时 %.1f 秒，抢票成功！请确认订单信息 ###" %
                  (con.num, round(con.time_end - con.time_start, 3)))
            break
