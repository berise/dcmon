dcmon2
======
dcmon stands for DCinside Monitoring tool.

This tools is for testing selenium's automation functionalities.

Let script do the job and you just sit back.

dcmon2.py requires selenium package. ~~And basically uses firefox.~~

To run dcmon2 run following commands
$ python dcmon2.py -m
  - Yet, URL is hardcoded in dcmon2.py. so change it by yourself.

selenium for python binding
===========================
To install selenium please refer following page.
https://pypi.python.org/pypi/selenium

download selenium-3.7.0.tar.gz and install


ChromeDriver - WebDriver for Chrome
===================================
ChromeDriver is used to access to Chrome for automated testing of 
web pages across many browsers.

Please see following web pages.
https://sites.google.com/a/chromium.org/chromedriver/home

You can download chromedriver from following link.
https://sites.google.com/a/chromium.org/chromedriver/downloads
 - http://chromedriver.storage.googleapis.com/index.html?path=2.24/

Download chromedriver and put them in the same directory of dcmon.

Limitation
==========
Selenium doesn't support for tab in browsers.
