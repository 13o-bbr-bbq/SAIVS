#!/usr/bin/python
#coding:utf-8
import os
import time
from selenium import webdriver
import codecs

# const variable
SIZE_WIDTH = 780
SIZE_HEIGHT = 480
POS_WIDTH = 520
POS_HEIGHT = 1

# 様々なブラウザ連携を行う
class Browser():

    # ブラウザの初期設定
    def __init__(self):
        # ブラウザの定義
        # obj_options = webdriver.ChromeOptions()
        # obj_options.add_argument('--disable-javascript')
        # self.obj_browser = webdriver.Chrome(executable_path=r".\\chromedriver_win32\\chromedriver.exe", chrome_options=obj_options)
        self.obj_browser = webdriver.Chrome(executable_path=r".\\chromedriver_win32\\chromedriver.exe")

        # 受信したレスポンスを出力するファイルパス
        self.str_html_file_path = os.path.join('.\\result', 'response.html')

    # 初回ブラウザ起動
    def start_browser(self):
        # print self.obj_browser.get_window_size(windowHandle='current')
        # print self.obj_browser.get_window_position(windowHandle='current')
        self.obj_browser.set_window_size(SIZE_WIDTH, SIZE_HEIGHT)
        self.obj_browser.set_window_position(POS_WIDTH, POS_HEIGHT)
        self.obj_browser.get("file://C:\\Users\\itaka\\PycharmProjects\\saivs\\result\\response.html")

    # レスポンスのファイル出力
    def write_response_to_html(self, str_response, str_charset):
        obj_fout = codecs.open(self.str_html_file_path, 'w', str_charset)
        obj_fout.write(str_response)
        obj_fout.close()

    # レスポンスをブラウザで開く
    def refresh_browser(self):
        # ページを更新する
        try:
            self.obj_browser.refresh()
        except:
            self.obj_browser.switch_to.alert.accept()

    # ドライバを閉じる
    def close_browser(self):
        # クローズ
        self.obj_browser.close()
