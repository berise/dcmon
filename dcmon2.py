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
    kGALLERY_NAME = "given as an arg"
    """

    downloaded_files = Queue.Queue()

    def __init__(self, gall_name, location):
        self.kGALLERY_NAME = gall_name
        self.kLOCATION = location


        self.start_urls = [
            "http://gall.dcinside.com/board/view/?id=game_classic&no=6329821&page=1"
        ]

        self.app_urls = {}

        # find out current module(exeuctable) path and set to temporary download dir
        # where we'll watch
        collector_current_path = module_locator.module_path()
        temp_download_dir = os.path.join(collector_current_path, 'dn_' + location)
        if not os.path.exists(temp_download_dir):
            os.makedirs(temp_download_dir)

        self.browser_options = {}
        self.browser_options['download_folder'] = os.path.abspath(temp_download_dir)
        #self.web_driver = self.init_selenium_driver("chrome", self.browser_options)
        self.web_driver = self.init_selenium_driver("firefox", self.browser_options)


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

        # css path to thread
        #'#dgn_gallery_left > div.gallery_list > div.list_table > table > thead'

        try:
            dom_thread = self.web_driver.find_element_by_css_selector('#dgn_gallery_left > div.gallery_list > div.list_table > table > thead')
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

    def get_page_no(self, url):
        list = []
        self.web_driver.get(url)

        # css path to thread
        #'#dgn_gallery_left > div.gallery_list > div.list_table > table > thead'
        try:
            dom_thread = self.web_driver.find_element_by_css_selector('#dgn_gallery_left > div.gallery_list > div.list_table > table > thead')
            dom_trs = dom_thread.find_elements_by_tag_name('tr')

            for dom_tr in dom_trs:
                try:
                    # first t_notice is not a number
                    e1 = dom_tr.find_element_by_class_name('t_notice')
                except:
                        logging.error("t_notice is not found")
                else:
                    #print (e1.text)
                    list.append(e1.text)


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
                print (new_article_list)
            for i in new_article_list:
            #target_url = "{0}&no={1}&page=1".format(kGALLERIES[0], i)
            # down in a new tab
                #body = self.web_driver.find_element_by_tag_name("body")
                #ActionChains(self.web_driver).send_keys(Keys.CONTROL, "t").perform()

                target_url = "http://gall.dcinside.com/board/view/?id=game_classic&no={0}&page=1".format(i)
                print (target_url)
                self.do_robot_click(target_url)
                #self.download_if_attached(target_url)

            # update list
            list1 = list2
            logging.info("update list1")

            # sleep little time
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

            logging.info("found a links")
            for li in lis:
                a = li.find_element_by_tag_name('a')

                #// Scroll the browser to the element's Y position
                self.web_driver.execute_script("window.scrollTo(0,"+str(a.location['y'])+")")
                logging.info("click on a file attachment link : %s", a.text)
                a.click()
                #time.sleep(1)

        #try:
        # for xpath in file_xpath_selectors:
        #     ul_elements = self.web_driver.find_element_by_xpath(xpath)
        #
        # lis = ul_elements.find_elements_by_tag_name('li')
        # #print (lis)
        #
        # for li in lis:
        #     a = li.find_element_by_tag_name('a')
        #
        #     a.click()
            #time.sleep(random.randrange(1, 2))
        #except:
        #    logging.error("%s : no such xpath element", url)


        # wait a file being downloaded for 3 seconds.
        # make it a longer if file is broken
        #WebDriverWait(self.web_driver, 3)

        #self.web_driver.close()

    def do_robot_click(self, url):
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


def process_agruments():
    # append parent path
    #git_info = git_revision_info.git_revision_info()

    program_description = "dcmon2 -- rev" #.%s" % (git_rev.git_rev().get_git_info())
    parser = argparse.ArgumentParser(description = program_description)

    parser.add_argument('-u', '--url',          dest='get_url', default=None, action="store_true", help='monitor a given url')
    parser.add_argument('-t', '--test-url', dest='test_url', default=None, action="store_true", help='test run with a given url')
    parser.add_argument('-d', '--directory',     dest='directory',action="store", help='directory to put files')
    #parser.add_argument('-v', '--version',   dest='version',  default=None,   action="store_true", help='show program revision')


    if len(sys.argv)<=1:
        parser.print_help()
        sys.exit(1)

    (args) = parser.parse_args()
    logging.info(program_description)

    return args

# conditions to exit
def verify_options(options):
    if options.get_url:
        print ("get url")

    if options.get_apk:
        print ("get apk")



""" monitor and collect """
def test_url():
        ###
        logging.info("[downloader] start a user action thread")
        mon = Robot('', '')

        urls = [ "http://gall.dcinside.com/board/view/?id=game_classic&no=6329821&page=1",
                 "http://gall.dcinside.com/board/view/?id=game_classic&no=6388291&page=1"
                 ]
        for url in urls:
            #mon.do_robot_click(url)
            mon.download_if_attached(url)

def test_gallery_name():
        gname = 'http://gall.dcinside.com/board/view/?id=game_classic'

        mon = Robot('', '')
        mon.monitor_and_get(gname)

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





if __name__ == "__main__":
    kGALLERIES  = [
            "http://gall.dcinside.com/board/view/?id=game_classic"
        ]

    kGALLERY_NAME = ""

    ## setup log
    log_filename = "{0}_{1}".format(kGALLERIES[0], datetime.datetime.now().strftime('%Y_%m_%d_%M_%H.log'))
    log_filename = os.path.join(tempfile.gettempdir(), log_filename)

    LOGGING_LEVEL = logging.INFO  # Modify if you just want to focus on errors
    logging.basicConfig(level=LOGGING_LEVEL,
                    format='%(asctime)s %(levelname)-8s %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S'),
                    #filename = log_filename)

    # define a Handler which writes INFO messages or higher to the sys.stderr
    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    # set a format which is simpler for console use
    formatter = logging.Formatter('%(asctime)s %(levelname)-8s %(message)s')
    # tell the handler to use this format
    console.setFormatter(formatter)
    # add the handler to the root logger
    #logging.getLogger('').addHandler(console)
    #logging.info("Logging to file  : %s", log_filename)

    args = process_agruments()
    #verify_options(args)

    #test_url()
    test_gallery_name()
    #test_new_tab()