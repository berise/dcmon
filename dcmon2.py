#!/usr/bin/env python
# -*- coding: utf-8 -*-

# berise@
import threading
import time
import os
import Queue
import logging

from selenium import webdriver
import pprint
from selenium.webdriver.common.action_chains import ActionChains
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




class Monitor():
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

        self.chrome_options = {}
        self.chrome_options['download_folder'] = temp_download_dir
        self.web_driver = self.init_selenium_driver("chrome", self.chrome_options)


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
            fp.set_preference("browser.download.folderList", 1)
            #fp.set_preference("browser.download.manager.showWhenStarting", False)
            fp.set_preference("browser.download.panel.shown", False)
            #fp.set_preference("browser.download.dir", os.getcwd())
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


    def browse_category_and_collect(self, url):
        start_page = 1
        #
        curr_url = url
        next_page = start_page + 1
        while True:
            self.collect_apk_urls(self.web_driver, curr_url)

            logging.info("[collect_urls] URL(page) : %s(%d), " % (curr_url, next_page))
            logging.info("[collect_urls] collected url count : %d" % len(self.app_urls))
            pprint.pprint(self.app_urls)

            (ret, next_url) = self.get_next_page(self.web_driver, next_page)
            if ret:
                curr_url = next_url
                next_page += 1
            else:
                break

    def collect_apk_urls(self, web_driver, url):
        web_driver.get(url)

        try:
            ul_elements = web_driver.find_element_by_css_selector('#appSoftListBox')

            lis = ul_elements.find_elements_by_tag_name('li')
            for li in lis:
                a = li.find_element_by_tag_name('a')
                href = a.get_attribute('href')
                self.app_urls[href] = 1  # duplicated url will be removed
        except:
            logging.info("[collect_apk_urls] find_element_by_css_selector failed.")


    def download_if_attached(self, url):
        self.web_driver.get(url)
        #logging.info("Wait for 3 seconds till web page download")

        WebDriverWait(self.web_driver, 3)

        ul_elements = self.web_driver.find_element_by_css_selector('#dgn_content_de > div.re_gall_box_3 > div > ul')

        lis = ul_elements.find_elements_by_tag_name('li')
        print (lis)

        for li in lis:
            a = li.find_element_by_tag_name('a')
            print (a.text)
            a.click()
            time.sleep(random.randrange(1, 2))
            #href = a.get_attribute('href')
            #print (href)
            #href.click()

        # wait a file being downloaded for 3 seconds.
        # make it a longer if file is broken
        WebDriverWait(self.web_driver, 3)


    def get_next_page(self, web_driver, next_page):
        """
            @brief Find paging elements in html and go to next page
        """

        try:
            page_elements = web_driver.find_element_by_css_selector('#softListBox > div.page_box > div')
            #print page_elements

            paging_elements = page_elements.find_elements_by_tag_name('a')

            for e in paging_elements:
                logging.info("[get_next_page] Looking for the next page index/href %s:%s", e.text, e.get_attribute('href'))

                if is_digit(e.text):
                    page_n = int(e.text)
                    if next_page == page_n:
                        return (True, e.get_attribute('href'))
                        #e.click()
        except:
            logging.info("[get_next_page] find_element_by_css_selector failed.")

        return (False, None)



    def run_collector_url(self):
        web_driver = self.init_selenium_driver("chrome", self.chrome_options)

        # overall process as follows.
        # do the similar jobs as styner did. (gather urls and put them all in db and process each records)

        # start_urls???�회?�면???�집??url(app_urls)??db???��? ??app_urls 초기??
        for url in self.start_urls:
            self.browse_category_and_collect(web_driver, url)

            for k, v in self.app_urls.iteritems():
                print "db_insert_url(%d) insert %s, %s into db" % (ret, k, v)

            self.app_urls.clear()


        web_driver.quit()


    def run_collector_downloader(self):
        """
            download apk in the database
        """
        logging.info("init selenium driver %s", "chrome")
        web_driver = self.init_selenium_driver("chrome", self.chrome_options)

        # to watch download path
        #threading.Thread(group=None, target=watch, args=[self.chrome_options['download_folder'], cb_file_watch])

        # thread_watcher�?while?�에 ?�을 경우??문제??
        # URL??리소?��? ?�는 경우 timeout??발생?�며(60*60) ??경우 thread_watcher???�상 종료?��? ?�음.
        # ?�라??watcher??종료 ?�이 계속 모니?�링?�는 ?�몬 ?�식?�로 �?��
        stop_event = threading.Event()
        logging.info("[downloader] start a watch thread")
        thread_watcher = ThreadWorker(watch, stop_event, collector.chrome_options['download_folder'], self.downloaded_files)
        thread_watcher.start()      # daemonize will also works

        ###
        logging.info("[downloader] start a user action thread")
        #ret = self.download_apk(web_driver, row['url'])
        #ThreadWorker(self.download_apk, web_driver, row['url']).start()
        #thread_simulator = ThreadWorker(self.simulate_user_action, web_driver, row['url'])
        thread_simulator = ThreadWorker(self.simulate_user_action, web_driver, row['url'])
        thread_simulator.start()
        thread_simulator.join()

        # ?�레?��? ?�성????DirectoryChange?�벤?��? 기다린다
        wait_time = 60 * 30   # 60 sec * 30 = .5 hour
        #wait_time = 6   # test
        logging.info("[downloader] Wait stop_event from watch thread. %d seconds left", wait_time)
        ret_wait = stop_event.wait(wait_time)
        stop_event.clear()      # Subsequently, threads calling wait() will block until set() is called to set the internal flag to true again.

#           if ret_wait == True:        # stop_event is set(notified)

#               time.sleep(5)       # let browser have some time to finish download
#               logging.info("[downloader] stop_event get notified")

#               file_fullpath = self.downloaded_files.get()
#               logging.info("[downloader] downloaded file : %s", file_fullpath)
#               logging.info("[downloader] wait for the threads")


#               # new file process routine.
#               scheme, netloc, path, query, fragment = urlparse.urlsplit(file_fullpath)
#               filename = os.path.basename(path)

#               sha256_hash = berlib.sha256sum(file_fullpath)
#               apk_dest = os.path.join(self.kLOCATION, self.kGALLERY_NAME, sha256_hash[0])
#               if not os.path.exists(apk_dest):
#                   os.makedirs(apk_dest)
#               try:
#                   shutil.move(file_fullpath, apk_dest)
#               except:
#                   logging.info("[downloader] can not move a file. maybe it is already exists")

#               #logging.info("[downloader] start to upload file : %s")
#               apk_dest_fullpath  = os.path.join(self.kLOCATION, self.kGALLERY_NAME, sha256_hash[0], filename)
#               apk_dest_halfpath  = os.path.join(self.kGALLERY_NAME, sha256_hash[0], filename)


#               logging.info("[downloader] set download/visit flag")

#               if ret:
#                   logging.info("[downloader] apk(No. %d) is downloaded" % row['no'])
#                   #logging.info("[downloader] remove a file : %s", file_fullpath)
#                   #os.remove(file_fullpath)
#           else:           # ret_wait
#               logging.info("[downloader] stop_event timeout %d", wait_time)
#               if ret:
#                   logging.info("[downloader] apk(No. %d) is not downloaded(with visit flag set)" % row['no'])


#               # set visit flag and go to next number
#               # Here we need to add DB field download to tell downloaded or not

            #else:
            #    logging.info("[downloader] Can't click Fast Download button. Just set a visit flag")

        web_driver.close()

    def test_run(self):
        web_driver = self.init_selenium_driver("chrome")

        # overall process as follows.
        # do the similar jobs as styner did. (gather urls and put them all in db and process each records)

        # start_urls???�회?�면???�집??url(app_urls)??db???��? ??app_urls 초기??
        for url in self.start_urls:
            self.browse_category_and_collect(web_driver, url)

            self.app_urls.clear()

        web_driver.quit()

    """ monitor and collect to given url """
    def test_url(self, url):
        ###
        logging.info("[downloader] start a user action thread")
        #ret = self.download_apk(web_driver, row['url'])
        #ThreadWorker(self.download_apk, web_driver, row['url']).start()
        #thread_simulator = ThreadWorker(self.simulate_user_action, web_driver, row['url'])
        thread_simulator = ThreadWorker(self.simulate_user_action, url)
        thread_simulator.start()
        thread_simulator.join()





    def test_db_query(self):
        print row['no'], row['url']


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

        try:
            self.download_if_attached(url)
        except:
             logging.error("Browser Page load timed out")
             #reset the page for the next test
             #web_driver.get("about:blank")
             return False

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
    parser.add_argument('-l', '--location',     dest='location',action="store", help='Location to put files')
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

    args.test_url = kGALLERIES[0]
    args.location = 'test_dir'
    mon = Monitor(args.test_url, args.location)
    args.test_url = "http://gall.dcinside.com/board/view/?id=game_classic&no=6329821&page=1"
    mon.test_url(args.test_url)

    #mon.close_selenium()
#   if args.get_url:
#       logging.info("selected mode : get url")
#       collector.run_collector_url()

#   if args.get_apk:
#       logging.info("selected mode : download apk")
#       if args.location is None:
#           logging.info("-l must be given to run a program")
#           sys.exit(1)
#       collector.run_collector_downloader()
