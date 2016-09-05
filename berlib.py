#!python
# coding=utf-8
# berise@

import os, time
import hashlib


def md5sum(filename):
    fh = open(filename, 'rb')
    m = hashlib.md5()
    while True:
        data = fh.read(8192)
        if not data:
            break
        m.update(data)
    return m.hexdigest()

def sha256sum(filename):
    with open(filename, mode='rb') as f:
        d = hashlib.sha256()
        while True:
            buf = f.read(1024) # 128 is smaller than the typical filesystem block
            if not buf:
                break
            d.update(buf)
        return d.hexdigest()


def read_blob(filename):
    #print ("[read_blob]")
    with open(filename, 'rb') as fin:
        img = fin.read()
        #print ("read %d bytes\n" % (len(img)))

    return img
