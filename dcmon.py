#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Distill DCINSIDE Pictures(zzalbangs)
#
# usage
# python dcinside_crawler.py [gallery name] [range]
# eg. python dcinside_crawler.py [game_classic] [1, 1000]
# berise@gmail.com
# you need a 'wget' in you PATH

# Webpages from http://gall.dcinside.com/list.php?id=game_classic&no=403226&page=1&bbs=
# to http://gall.dcinside.com/list.php?id=game_classic&no=1&page=1&bbs=
# total pages : around 400,000 pages 
#


import HTMLParser, urllib2, urlparse, sys
import httplib
import time, random
import os
import re 


directory_name = "call_setup_directory"

def get_html(url):
	response = urllib2.urlopen(url) 
	html = response.read()
	return html


def get_html_and_serialize(filenames = [], links = []):
	if filenames is None:
		return
	if len(filenames) >= len(links):
		count = len(links)
	else:
		count = len(filename)
	print "image(s) in page : %d" % count
	for i in range(0, count):
		filename = filenames[i]
		link = links[i]

		global directory_name

		filename = directory_name + "/" + filename
		response = urllib2.urlopen(link) 
		html_contents = response.read()
		serialize(filename, html_contents)
		print "%s is saved\n" % filename


def serialize(filename, contents):
	u = unicode(filename, 'utf-8')
	FILE = open(u, "wb")
	FILE.write(contents)
	FILE.close()

#
# html_contents1Í≥º Í∞ôÏùÄ Í≤ÉÏóêÏÑú Ïù¥Î¶ÑÏùÑ Ï∂îÏ∂ú
def extract_a_href_lists(html_contents):
	# (jpg|~~~)*?¿∫ »Æ¿Â¿⁄∞° æ¯æÓµµ ¿Ã∏ß √ﬂ√‚¿Ã ∞°¥…«‘ "99aa0--a"
	pattern = r"<a class='txt03' href='.*?'\s+>.*?.(jpg|jpeg|gif|bmp|png)*?</a>"   # in raw string
	regex = re.compile(pattern, re.IGNORECASE)

	href_lists = []
	for match in regex.finditer(html_contents):
		#print "%s:%s" %(match.start(), match.group(0)) 
		href_lists.append(match.group())
	return href_lists

def extract_filename(html_contents):
	pattern = r">.*?.(jpg|jpeg|gif|bmp|png)*?<"
	regex = re.compile(pattern, re.IGNORECASE)
	for match in regex.finditer(html_contents):
		str = match.group().replace(">", "")
		str = str[0:str.find("<")]
		return str



def extract_picture_links(html_contents, links = []):
	pattern = r"src='http://dcimg1.dcinside.com/viewimage.php.*?'"
	regex = re.compile(pattern)
	matched_iterator = regex.finditer(html_contents)
	for match in matched_iterator:
		str = match.group().replace("src='", "")
		str = str.replace("'", "")
#print str
		links.append(str)
#str = match.group().replace(">", "")

#http://gall.dcinside.com/list.php?id=game_classic&no=403897&page=1&bbs=
def navigate_page(id,no):
	url_prefix = "http://gall.dcinside.com/list.php?id=" + id + "&"
	url_postfix = "no=" + str(no) + "&page=1&bbs="
	url = url_prefix + url_postfix
	print "[peeping]" + url

	response = urllib2.urlopen(url) 
	html = response.read()
	return html


def save(html_contents):
	filenames = []
	links = []
	href_lists = extract_a_href_lists(html_contents)
	for href in href_lists:
		#print href
		filenames.append(extract_filename(href))
	
	if filenames is None:
		return
	if links is None:
		return

#	for name in filenames:
#		print "[save]filename : %s" % name

	extract_picture_links(html_contents, links)
#	for link in links:
#		print link
	get_html_and_serialize(filenames, links)


def suck_it(id, no):
	html_contents = navigate_page(id, no)
	save(html_contents)


def test():
	href_lists = extract_a_href_lists(html_contents1)
	for href in href_lists:
		extract_filename(href)


def setup_directory(gallery_name, end=9999999):
	global directory_name
	directory_name = gallery_name + "/" + "dcmon"

	if os.path.exists(gallery_name) is False:
		print "Make directory %s" %gallery_name
		os.mkdir(gallery_name);
	else:
		print "%s Directory already exists" % gallery_name

	if os.path.exists(directory_name) is False:
		print "Make directory %s" % (directory_name)
		os.mkdir(directory_name)
	else:
		print "%s Directory already exists" % directory_name


# idea starts from here
# url2 gives binary stream 
#url2 = "http://image.dcinside.com/viewimage.php?id=game_classic&no=29bcc427b78377a16fb3dab004c86b6fcc182254367d30ef20fc9427f2201dca7c2787cf008a67b8b6b1b4dc9579b84dd93ccf744212e480e42a86651e92cca47ecfe97e288aea1" 
def main(gallery_name, begin, end):
	setup_directory(gallery_name, begin, end)

	for i in range(begin, end):
		suck_it(gallery_name, i)
	
#sleep_time = random.randrange(1, 3)
#		time.sleep(sleep_time)
#		print "sleep %d seconds" % sleep_time
#http://gall.dcinside.com/list.php?id=game_classic

def update_no(no):
	if os.file.exists("no.txt"):
		# read file and return number in it
		return 1


#<a href="/list.php?id=game_classic&no=405809&page=1&bbs="   >≥≤¿⁄¥¬ 10¥ÎµÁ 20¥ÎµÁ 80¥ÎµÁ∞£ø°..</a>	
def get_recent_no(gallery_name):
	html_url = "http://gall.dcinside.com/list.php?id=" + gallery_name

	html_contents = get_html(html_url)
	# (jpg|~~~)*?¿∫ »Æ¿Â¿⁄∞° æ¯æÓµµ ¿Ã∏ß √ﬂ√‚¿Ã ∞°¥…«‘ "99aa0--a"
	pattern = "list.php\?id=" + gallery_name + "&no=(\d+)&page=\d+&bbs=.*?>.*?</a>"
	regex = re.compile(pattern, re.IGNORECASE)

	href_lists = []
	for match in regex.finditer(html_contents):
		#print "%s:%s" % (match.start(), match.group(1)) 
		href_lists.append(match.group(1))
	return href_lists[0:6]



def determine_most_recent_page_number(no_lists, prev_no_lists):
	mru_index = -1

	print no_lists, prev_no_lists
	if len(prev_no_lists) != 0:
		print no_lists, prev_no_lists

		for x in range(0, len(no_lists)):
			if (no_lists[x] != prev_no_lists[x]):
				mru_index = x
				print mru_index, no_lists[mru_index] 
				break;

	return mru_index




def get_recent_image(gallery):
	no = -2
	prev_no = -1
	prev_no_lists = []
	mru_index = -1

	while True:
		no_lists = get_recent_no(gallery)

		# determine most recent page number
		if prev_no == -1:
			print "trying to determine most recent page number"
			no_index = determine_most_recent_page_number(no_lists, prev_no_lists);
			prev_no_lists = no_lists;
			if ((no_index != len(no_lists)) and (no_index != -1)):
				prev_no = int(no_lists[no_index]) 
			sleep_time = random.randrange(3, 9)
			print "[sleep %d seconds]" % sleep_time
			time.sleep(sleep_time) 
			continue

		if no_lists is None:
			continue
		if (prev_no != no_lists[no_index]):
			print "page " + no_lists[no_index] +" is being skimmed"# % no_lists[no_index] # peeped
			suck_it(gallery, no_lists[no_index])
		else:
			print "@%d" % int(no_lists[no_index])
			sleep_time = random.randrange(3, 9)
			print "[sleep %d seconds]" % sleep_time
			time.sleep(sleep_time) 

		prev_no = no_lists[no_index]
			
def dcmon_main(target_gallery):
	setup_directory(target_gallery)
	get_recent_image(target_gallery)

# just it is a main
if __name__ == '__main__': 
	if len(sys.argv) > 1:
		dcmon_main(sys.argv[1])
	else:
		print "Usage :"
		print "python dcmon.py GalleryName"



