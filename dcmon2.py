#!/usr/bin/env python
# -*- coding: utf-8 -*-

# berise@
import threading
import time
import os
import Queue
import logging

import selenium
from selenium import webdriver
import pprint
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait # available since 2.4.0

import module_locator
import argparse
import sys
import datetime
import tempfile
import berlib
import urlparse
import shutil
import random
import json


# util
def is_digit(str):
    try:
        tmp = float(str)
        return True
    except ValueError:
        return False

def is_integer(i):
    i = str(i)
    return i == '0' or (i if i.find('..') > -1 else i.lstrip('-+').rstrip('0').rstrip('.')).isdigit()


def print_web_driver_info(sb_driver):
    print "sb_driver info"
    print " cookie : "  #, sb_driver.get_cookies()
    pprint.pprint(sb_driver.get_cookies())
    sb_driver_cookies = sb_driver.get_cookies()
    print sb_driver_cookies[-1]['value']



class ThreadWorker(threading.Thread):
    def __init__(self, callable, *args, **kwargs):
        super(ThreadWorker, self).__init__()
        self.callable = callable
        self.args = args
        self.kwargs = kwargs
        self.setDaemon(True)

    def run(self):
        logging.info("running thread %s" % threading.current_thread())

        try:
            self.callable(*self.args, **self.kwargs)
        except Exception, e:
            print e




class Robot():
    """
    kGALLERY_URL = "given as an arg"
    """

    downloaded_files = Queue.Queue()

    def __init__(self, gall_url, id):
        self.gall_list = {}
        self.kGALLERY_URL = gall_url
        self.gallery_id = id


        self.list_url = gall_url + id
        self.view_url = self.list_url


        self.app_urls = {}

        # find out current module(exeuctable) path and set to temporary download dir
        # where we'll watch
        collector_current_path = module_locator.module_path()
        temp_download_dir = os.path.join(collector_current_path, 'dn_' + id)
        if not os.path.exists(temp_download_dir):
            logging.info("make a download dir : %s", temp_download_dir)
            os.makedirs(temp_download_dir)

        self.browser_options = {}
        self.browser_options['download_folder'] = os.path.abspath(temp_download_dir)

        # option --browser firefox
        # option -c -f -???
        # on linux, firefox causes an error when clicking links with delays.
        self.web_driver = self.init_selenium_driver("chrome", self.browser_options)
        #self.web_driver = self.init_selenium_driver("firefox", self.browser_options)


    def close_selenium(self):
        self.web_driver.close()
        if self.web_driver:
            self.web_driver.quit()


    def init_selenium_driver(self, browser_type, options = None):
        """
        @param browser_type:    firefox, chrome, ie, ... safari?
        @return:    web_driver
        """
        sb_driver = None
        if (browser_type == "firefox"):
            fp = webdriver.FirefoxProfile()

            fp.set_preference("browser.download.manager.showWhenStarting", False)
            fp.set_preference("browser.download.panel.shown", False)

            fp.set_preference("browser.download.folderList", 2)  # 2 implicitg custom location
            fp.set_preference("browser.download.dir", options['download_folder'])

            fp.set_preference("browser.helperApps.neverAsk.saveToDisk", "text/csv")
            fp.set_preference("browser.helperApps.neverAsk.openFile", "application/octet-stream")
            fp.set_preference("browser.helperApps.neverAsk.saveToDisk", "application/octet-stream")

            sb_driver = webdriver.Firefox(firefox_profile=fp)
        elif (browser_type == "chrome"):
            chrome_profile = webdriver.ChromeOptions()

            if options:
                prefs = {"download.default_directory" : options['download_folder']}
                chrome_profile.add_experimental_option("prefs",prefs)

            sb_driver = webdriver.Chrome(chrome_options = chrome_profile)
        elif (browser_type == "ie"):
            sb_driver = webdriver.Ie()
        else:
            sb_driver = webdriver.Firefox()
        return sb_driver


    def get_page_no(self, url, list):
        self.web_driver.get(url)

        # 17.11
        # dgn_gallery_left > div > div.list_table > table
        try:
            dom_thread = self.web_driver.find_element_by_css_selector('# dgn_gallery_left > div > div.list_table > table')
            dom_trs = dom_thread.find_elements_by_tag_name('tr')

            for dom_tr in dom_trs:
                try:
                    # first t_notice is not a number
                    e1 = dom_tr.find_element_by_class_name('t_notice')
                except:
                        logging.error("t_notice is not found")
                else:
                    #print (e1.text)
                    if is_digit(e1.text):
                        list.append(int(e1.text))
                    else:
                        logging.info("pass on non numeric element %s", e1.text)

        except selenium.common.exceptions.NoSuchElementException:
            return

    def get_seed_urls(self, url):
        self.web_driver.get(url)
        selector_1 = '#gallerlist'

        try:
            iframe = self.web_driver.find_element_by_css_selector(selector_1)
            print(iframe)
            containerFrame = self.web_driver.find_element_by_css_selector(selector_1)


            self.web_driver.switch_to_frame(containerFrame)
            print(containerFrame)


            div_gall_list = self.web_driver.find_element_by_css_selector('#gall_list')
            print(div_gall_list)

            lists = div_gall_list.find_elements_by_class_name('list_title')

            for l in lists:
                t = l.get_attribute('text')
                a = l.get_attribute('href')
                #print("{0} -> {1}".format(t, a))

                self.gall_list[l.text] = a

            print(self.gall_list)


            self.web_driver.switch_to_default_content()

        except selenium.common.exceptions.NoSuchElementException:
            print("no such element")


    def get_url(self, text):
        return self.gall_list[text]


    def get_page_no(self, url):
        list = []
        self.web_driver.get(url)

        # css path to thread
        #'#dgn_gallery_left > div.gallery_list > div.list_table > table > thead'


        # 17.11.28
        # dgn_gallery_left > div > div.list_table > table > tbody > tr.on > td.t_subject > a
        # dgn_gallery_left > div > div.list_table > table
        try:
            dom_thread = self.web_driver.find_element_by_css_selector('#dgn_gallery_left > div > div.list_table > table')
            dom_trs = dom_thread.find_elements_by_tag_name('tr')

            for dom_tr in dom_trs:
                try:
                    # first t_notice is not a number
                    dom_notice = dom_tr.find_element_by_class_name('t_notice')
                except:
                        logging.error("t_notice is not found")
                else:
                    #print (e1.text)
                    list.append(dom_notice.text)
                    dom_td = dom_tr.find_element_by_class_name('t_subject')

                    # 17.11
                    # dgn_gallery_left > div.gallery_list > div.list_table > table > tbody > tr:nth-child(1) > td.t_subject > a
                    dom_a_href = dom_td.find_element_by_tag_name('a')
                    view_url = dom_a_href.get_attribute('href')
                    t1 = urlparse.urlsplit(view_url)
                    self.view_url = t1.scheme + "://" + t1.netloc + t1.path

                    #print("%s(url:%s)" % (dom_notice.text, dom_a_href.get_attribute('href')))

        except selenium.common.exceptions.NoSuchElementException:
            return list

        return list

    def compare_no(self, l1, l2):
        for i in range(len(l1)):
            if l1[i] != l2[i]:
                return i
        return -1

    def monitor_and_get(self, url):
        list1 = []
        list2 = []
        list1 = self.get_page_no(url)
        list2 = list1

        while(1):
            list2 = self.get_page_no(url)

            if len(list2) < len(list1):     # something wrong
                logging.info("list2 length is not shorter than list1")
                continue
            if len(list1) != len(list2):      # also fail  to read whole web contents... ???
                logging.info("list2 length is not same to list1")
                continue

            print(list1)
            print(list2)
            new_article_list = list(set(list2) - set(list1))

            # to make a full url
            #http://gall.dcinside.com/board/view/?id=game_classic&no=6349933&page=1
            if new_article_list:
                logging.info(new_article_list)
            for i in new_article_list:
            #target_url = "{0}&no={1}&page=1".format(kGALLERIES[0], i)
            # down in a new tab
                #body = self.web_driver.find_element_by_tag_name("body")
                #ActionChains(self.web_driver).send_keys(Keys.CONTROL, "t").perform()

                target_url = "{}?id={}&no={}&page=1".format(self.view_url, self.gallery_id, i)
                print (target_url)
                #self.do_threaded_click(target_url)

                try:
                    self.download_if_attached(target_url)
                except:
                    #logging.info("web page doesn't fully loaded")
                    #logging.info("force to refresh")
                    #self.web_driver.refresh()

                    # or simply
                    continue


            # update list
            list1 = list2
            logging.info("update list1")

            # take a sleep for little bit
            time.sleep(random.randrange(2, 3))


    def download_if_attached(self, url):
        """
        attached file css path : #dgn_content_de > div.re_gall_box_3 > div > ul
        XPATH : //*[@id="dgn_content_de"]/div[5]/div/ul
        """
        self.web_driver.get(url)
        #logging.info("Wait for 3 seconds till web page download completed")
        #WebDriverWait(self.web_driver, 3)


        file_css_selectors = [ '#dgn_content_de > div.re_gall_box_3 > div > ul' ]
        css = '#dgn_content_de > div.re_gall_box_3 > div > ul'
        #file_xpath_selectors = [ '//*[@id="dgn_content_de"]/div[5]/div/ul' ]

        #ul_elements = None
        try:
            #for css in file_css_selectors:
            ul_elements = self.web_driver.find_element_by_css_selector(css)

        except selenium.common.exceptions.NoSuchElementException:
            return
        else:
            #https://code.google.com/p/selenium/issues/detail?id=2766
            # Find an element and define it
            #WebElement elementToClick = driver.findElement(By.xpath("some xpath"));
            #// Scroll the browser to the element's Y position
            #((JavascriptExecutor) driver).executeScript("window.scrollTo(0,"+elementToClick.getLocation().y+")");
            #// Click the element
            #elementToClick.click();

            lis = ul_elements.find_elements_by_tag_name('li')

            logging.info("found attachment links")
            for li in lis:
                logging.info("  %s", li.find_element_by_tag_name('a').text)

            for li in lis:
                a = li.find_element_by_tag_name('a')

                #// Scroll the browser to the element's Y position
                self.web_driver.execute_script("window.scrollTo(0,"+str(a.location['y'])+"*0.5)")
                #logging.info("click on a link : %s(%s)", a.text, a.find_element_by_link_text(a.text))
                logging.info("click a link : %s(%s)", a.text, a.get_attribute("href"))
                a.click()

                # wait until file be seen on download directory
                for c in range(3):
                    a_path = os.path.join(self.browser_options['download_folder'], a.text)
                    logging.info("[%d] see if %s exists",c , a_path)
                    if os.path.isfile(a_path):
                        logging.info("%s download complete", a.text)
                        break
                    else:
                        time.sleep(random.randrange(2, 4)) # 1d3+1


                # Note. on chrome, a.click method takes a little bit more time than
                # in firefox. Chrome seems that it is likely to download all elements before
                # proceed click action.


    def do_threaded_click(self, url):
        ###
        logging.info("[downloader] start a user action thread")

        thread_simulator = ThreadWorker(self.simulate_user_action, url )
        thread_simulator.start()
        thread_simulator.join()


    def run(self):
        # test all
        #self.test_run()
        #self.test_db_query()

        #self.db_set_visit_flag(self, self.my_table, no)
        #self.helper.db_reset_visit_flag(self.my_table)

        # test collect urls
        #self.test_collect_urls()
        #

        self.run_collector_downloader()


    """

    see thie page : http://docs.seleniumhq.org/docs/04_webdriver_advanced.jsp
    https://code.google.com/p/selenium/issues/detail?id=687
    Message: u'timeout: Timed out receiving message from renderer: 10.000\n  (Session info: chrome=36.0.1985.125)\n  (Driver info: chromedriver=2.10.267521,platform=Windows NT 6.1 SP1 x86_64)'
    #driver.manage().timeouts().pageLoadTimeout(5000,TimeUnit.MILLISECONDS)

        #try:
        #     driver.get("http://www.techcrunch.com");
        # catch (TimeoutException e
        #     System.out.println("Page load timed out");
        # }
        # //reset the page for the next test
        # driver.get("about:blank");

    """
    def simulate_user_action(self, url):
        logging.info("[simulate_user_action] opening : %s", url)
        self.download_if_attached(url)
        logging.info("[simulate_user_action] exit thread")


    def hover_on_button(self, web_driver):
        # jquery??mouse over event�??�해 ?�운로드 버튼??보임
        # ?�라??ActionChains???�한 mouse_hover ?�과 ?�공 ??버튼 ?�릭...
        dn_selectors = [ 'body > div.full_bg > div.wrapper > div.show_main > div.show_top.clearfix > div.app_info > div.app_download.clearfix > div:nth-child(1) > a'
                         ]
        try:
            logging.info("[hover_on_button] action hovering")
            for dn in dn_selectors:
                download_button = web_driver.find_element_by_css_selector(dn)
                mouse_hover = ActionChains(web_driver).move_to_element(download_button).click().move_to_element_with_offset(download_button, 3, 3).click()
                mouse_hover.perform()
        except:
            ret = False
        else:
            ret = True

        return ret


    def click_button(self, web_driver, css_selector):
        logging.info("[click_button] try to find a css selector : %s", css_selector)

        button_clicked = False
        #raise exception_class(message, screen, stacktrace)
        #selenium.common.exceptions.NoSuchElementException: Message: u'no such element\n  (Session info: chrome=36.0.1985.125)\n  (Driver info: chromedriver=2.10.267521,platform=Windows NT 6.1 SP1 x86_64)'
        try:
            hidden_button = web_driver.find_element_by_css_selector(css_selector)
            if hidden_button:
                #web_driver.move_to_element(hidden_button).move_to_element_with_offset(hidden_button, 5, 5).move_to_element_with_offset(hidden_button, 0, 0).click()
                hidden_button.click()
                button_clicked = True
                logging.info("[click_button] trying to click on : %s", css_selector)

                return button_clicked
        except:
            logging.info("[click_button] %s is not a valid css selector", css_selector)
            return False
        else:
            button_clicked = True
            return button_clicked


    def click_button_css(self, web_driver):
        logging.info("[click_button_css]")


        css_selectors = ['#webInnerContent > div > div.detail_right > div.code_box_border > div:nth-child(10)',
                         '#webInnerContent > div > div.detail_right > div.code_box_border > div:nth-child(10) > a'
                          ]

        button_clicked = False

        # try�??�용?�야 ?�래 exception???�함
        #raise exception_class(message, screen, stacktrace)
        #selenium.common.exceptions.NoSuchElementException: Message: u'no such element\n  (Session info: chrome=36.0.1985.125)\n  (Driver info: chromedriver=2.10.267521,platform=Windows NT 6.1 SP1 x86_64)'
        for cs in css_selectors:
            try:
                hidden_button = web_driver.find_element_by_css_selector(cs)
                logging.info("[click_button] trying : %s", cs)
                if hidden_button:
                    #web_driver.move_to_element(hidden_button).move_to_element_with_offset(hidden_button, 5, 5).move_to_element_with_offset(hidden_button, 0, 0).click()
                    hidden_button.click()
                    button_clicked = True
            except:
                logging.info("[click_button] %s is not a valid css selector", cs)
            else:
                button_clicked = True
                logging.info("[click_button] clicked : %s", cs)
                return button_clicked



    def click_button_xpath(self, web_driver, xpath):
        logging.info("[click_button_xpath]")

        button_clicked = False
        #raise exception_class(message, screen, stacktrace)
        #selenium.common.exceptions.NoSuchElementException: Message: u'no such element\n  (Session info: chrome=36.0.1985.125)\n  (Driver info: chromedriver=2.10.267521,platform=Windows NT 6.1 SP1 x86_64)'
        try:
            hidden_button = web_driver.find_element_by_xpath(xpath)
            if hidden_button:
                print hidden_button
                #web_driver.move_to_element(hidden_button).move_to_element_with_offset(hidden_button, 5, 5).move_to_element_with_offset(hidden_button, 0, 0).click()
                hidden_button.click()
                button_clicked = True
                logging.info("[click_button_xpath] trying to click on : %s", xpath)

                return button_clicked
        except:
            logging.info("[click_button_xpath] %s is not a valid", xpath)
            return False
        else:
            button_clicked = True
            return button_clicked

        # if not clicked, return False to let caller know this failed
        #logging.info("[click_button] click return value : %d", button_clicked)
        return button_clicked

    def simulate_user_action_2(self, web_driver, url):
        logging.info("[simulate_user_action_2] open url : %s", url)
        web_driver.get(url)

        # jquery??mouse over event�??�해 ?�운로드 버튼??보임
        # ?�라??ActionChains???�한 mouse_hover ?�과 ?�공 ??버튼 ?�릭...

        dn_selectors = [ 'body > div.full_bg > div.wrapper > div.show_main > div.show_top.clearfix > div.app_info > div.app_download.clearfix > div:nth-child(1) > a',
                         'body > div.full_bg > div.wrapper > div.show_main > div.show_top.clearfix > div.app_info > div.app_download.clearfix > div:nth-child(1)'
                         ]
        try:
            logging.info("[simulate_user_action_2] action hovering")
            for dn in dn_selectors:
                download_button = web_driver.find_element_by_css_selector(dn)
                mouse_hover = ActionChains(web_driver).move_to_element(download_button).move_to_element_with_offset(download_button, 3, 3)
                mouse_hover.perform()
        except:
            return False;


        #
        # @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
        # Download 버튼 ?�공???�양?�게 ?�고 ?�음.. -_-;
        # Google play class : '#new_fastdown_div > div.down_server.clearfix > a.btn_fast.btn_fast_android'
        # local download :  : '#new_fastdown_div > div.down_server.clearfix > a.btn_fast'
        # netdisk:  : 'body > div.full_bg > div.wrapper > div.show_main > div.show_top.clearfix > div.app_info > div.app_download.clearfix > div.func_download.on > div > div.down_netdisk > div.btn_down_netdisk.clearfix > a'
        css_selectors = ['#new_fastdown_div > div.down_server.clearfix > a.btn_fast.btn_fast_android',
                         '#new_fastdown_div > div.down_server.clearfix > a.btn_fast',
                         'body > div.full_bg > div.wrapper > div.show_main > div.show_top.clearfix > div.app_info > div.app_download.clearfix > div.func_download.on > div > div.down_netdisk > div.btn_down_netdisk.clearfix > a'
                         '#new_fastdown_div > div.down_server.clearfix > a',     # http://download.pandaapp.com/android-app/kingdoms-of-camelot-battle15.2.2-id11302.html#.U8SBlvnjDmc
                         '#new_fastdown_div > div.down_server.clearfix'
        ]

        button_clicked = False
        #raise exception_class(message, screen, stacktrace)
        #selenium.common.exceptions.NoSuchElementException: Message: u'no such element\n  (Session info: chrome=36.0.1985.125)\n  (Driver info: chromedriver=2.10.267521,platform=Windows NT 6.1 SP1 x86_64)'
        for cs in css_selectors:
            try:
                hidden_button = web_driver.find_element_by_css_selector(cs)
                if hidden_button:
                    hidden_button.click()
                    logging.info("[simulate_user_action_2] trying to click on : %s", cs)
                    button_clicked = True
            except:
                logging.info("[simulate_user_action_2] No css selector")
                pass
            else:
                logging.info("[simulate_user_action_2] clicked on : %s", cs)
                break

            # if not clicked, return False to let caller know this failed
        return button_clicked


def parse_arguments():
    # append parent path
    #git_info = git_revision_info.git_revision_info()

    program_description = "dcmon2 -- rev" #.%s" % (git_rev.git_rev().get_git_info())
    parser = argparse.ArgumentParser(description = program_description)

    parser.add_argument('-m', '--monitor',          dest='monitor', default=None, action="store_true", help='monitor with a given url')
    parser.add_argument('-l', '--list-galleries',     dest='list',action="store", help='list urls of galleries')
    parser.add_argument('-r', '--dry-run',     dest='dry_run',action="store", help='directory to put files')

    #
    parser.add_argument('-t', '--test-url', dest='test_function1', default=None, action="store_true", help='test run with a given url')
    #parser.add_argument('-v', '--version',   dest='version',  default=None,   action="store_true", help='show program revision')


    if len(sys.argv)<=1:
        parser.print_help()
        #sys.exit(1)

    (args) = parser.parse_args()
    #logging.info(program_description)

    return args

# conditions to exit
def do_jobs(options):
    if options.list:
        print ("get urls of galleries")
        collect_gallery_urls()

    if options.test_function1:
        test_function1()

    if options.monitor:
        gallery_list_url = 'http://gall.dcinside.com/board/lists?id='
        gallery_view_url = 'http://gall.dcinside.com/board/view/?id='
        monitor_gallery(gallery_list_url, 'game_classic1')


""" monitor and collect """
def test_get_and_download():
        ###
        logging.info("[downloader] start a user action thread")

        urls = [ "http://gall.dcinside.com/board/view/?id=game_classic&no=11036580&page=1"
                 "http://gall.dcinside.com/board/view/?id=game_classic&no=6388291&page=1"
                 ]

        urls = ['http://gall.dcinside.com/board/view/?id=game_classic&no=11037859&page=1']

        mon = Robot('', 'game_classic')
        for url in urls:
            #mon.do_threaded_click(url)
            mon.download_if_attached(url)

        mon.close_selenium()

def test_refactoring1():
    robot = Robot()

    """
    gall_id = 'aaa'
    gall_url = '~~~~/list'
    robot.set_config()
        # get gall_view_url
        view_url = robot.get_view_url()

    robot.monitor(view_url)

    """
    for url in urls:
        # mon.do_threaded_click(url)
        mon.download_if_attached(url)

    mon.close_selenium()


def monitor_gallery(url_base, id):

    mon = Robot(url_base, id)
    mon.monitor_and_get(mon.list_url)

def collect_gallery_urls():
    gall_list = 'gall_list.json'

    if os.path.exists(gall_list) == False:
        #get_seed_url
        #write_json
        r = Robot('', '')
        seed_url = 'http://gall.dcinside.com'
        r.get_seed_urls(seed_url)

        with open(gall_list,  'w') as f:
            json.dump(r.gall_list, f)
    else:
        with open(gall_list,  'r') as f:
            gd = json.load(f)

#        print(gd)
#        print gd[u'고전게임']

# selenium doesn't support for tab in browser. please see doc in seleniumhq.org
def test_new_tab():
    gname = 'http://gall.dcinside.com/board/view/?id=game_classic'
    mon = Robot('', '')
    #ActionChains(mon.web_driver).send_keys(Keys.CONTROL, "t").perform()
    ActionChains(mon.web_driver).send_keys(Keys.LEFT_CONTROL, "t").perform()
    handle = mon.web_driver.current_window_handle

    mon.web_driver.execute_script("window.open('');")
    new_tab_handle = mon.web_driver.window_handles[-1] # -1 is the latest window handle
    #new_tab_handle = mon.web_driver.current_window_handle

    mon.get_page_no(gname)
    #ActionChains(mon.web_driver).send_keys(Keys.LEFT_CONTROL, "w").perform()
    mon.web_driver.execute_script("self.opener = self; window.close();")
    #mon.web_driver.switch_to.window(new_tab_handle)

    mon.web_driver.get(gname)
    mon.web_driver.switch_to.window(handle)



def init_log():
    log_filename = "{0}_{1}".format("dcmon", datetime.datetime.now().strftime('%Y_%m_%d_%M_%H.log'))
    log_filename = os.path.join(tempfile.gettempdir(), log_filename)

    LOGGING_LEVEL = logging.INFO  # Modify if you just want to focus on errors
    logging.basicConfig(level=LOGGING_LEVEL,
                    format='%(asctime)s %(levelname)-8s %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S',
                    filename = log_filename)

    # define a Handler which writes INFO messages or higher to the sys.stderr
    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    # set a format which is simpler for console use
    formatter = logging.Formatter('%(asctime)s %(levelname)-8s %(message)s')
    # tell the handler to use this format
    console.setFormatter(formatter)
    # add the handler to the root logger
    logging.getLogger('').addHandler(console)
    logging.info("Logging to file  : %s", log_filename)


if __name__ == "__main__":
    init_log()

    kGALLERIES  = [
            "game_classic",
            "comedy_new1"
        ]


    args = parse_arguments()
    do_jobs(args)
