#!/usr/bin/python
# coding:utf-8
import sqlite3


# Sqlite3の操作クラス
class Sqlite3Control():

    # テーブルが存在しない場合は作成
    def __init__(self):
        self.obj_db_conn = sqlite3.connect('project.db', timeout=5, isolation_level='DEFERRED')

        # クローリングツリーテーブルの作成
        str_sql = "CREATE TABLE IF NOT EXISTS UrlTreeTBL(" \
                  "id INTEGER PRIMARY KEY AUTOINCREMENT, " \
                  "site_id INTEGER, " \
                  "page_no INTEGER, " \
                  "page_type INTEGER, " \
                  "accessed INTEGER, " \
                  "status INTEGER, " \
                  "parent_no INTEGER, " \
                  "depth INTEGER, " \
                  "method TEXT, " \
                  "protocol TEXT, " \
                  "fqdn TEXT, " \
                  "port INTEGER, " \
                  "path TEXT, " \
                  "param TEXT, " \
                  "param_no INTEGER, " \
                  "response_code TEXT, " \
                  "request_raw TEXT, " \
                  "response_raw TEXT, " \
                  "scan_status INTEGER, " \
                  "enc_type TEXT," \
                  "learned INTEGER," \
                  "param_type TEXT," \
                  "param_label TEXT," \
                  "access_date TEXT);"
        self.obj_db_conn.execute("begin transaction")
        self.obj_db_conn.execute(str_sql)
        self.obj_db_conn.commit()

        # 認証情報管理テーブルの作成
        str_sql = "CREATE TABLE IF NOT EXISTS CredentialsTBL(" \
                  "id INTEGER PRIMARY KEY AUTOINCREMENT, " \
                  "site_id INTEGER, " \
                  "type INTEGER, " \
                  "credential_info1 TEXT, " \
                  "credential_info2 TEXT, " \
                  "credential_info3 TEXT, " \
                  "credential_info4 TEXT, " \
                  "credential_info5 TEXT, " \
                  "secret_question TEXT, " \
                  "secret_answer TEXT, " \
                  "temp TEXT);"
        self.obj_db_conn.execute("begin transaction")
        self.obj_db_conn.execute(str_sql)
        self.obj_db_conn.commit()

        # 診断結果管理テーブルの作成
        str_sql = "CREATE TABLE IF NOT EXISTS ScanResultTBL(" \
                  "id INTEGER PRIMARY KEY AUTOINCREMENT, " \
                  "site_id INTEGER, " \
                  "page_no INTEGER, " \
                  "param_type INTEGER, " \
                  "param_name TEXT, " \
                  "param_value TEXT, " \
                  "signature_no INTEGER, " \
                  "inspect_value TEXT, " \
                  "result INTEGER," \
                  "inspection INTEGER," \
                  "response_code INTEGER, " \
                  "request_raw TEXT, " \
                  "response_raw TEXT, " \
                  "scan_date TEXT);"
        self.obj_db_conn.execute("begin transaction")
        self.obj_db_conn.execute(str_sql)
        self.obj_db_conn.commit()

        # 単語類似度管理テーブルの作成
        str_sql = "CREATE TABLE IF NOT EXISTS WordSimilarityTBL(" \
                  "id INTEGER PRIMARY KEY AUTOINCREMENT, " \
                  "page_type INTEGER, " \
                  "word TEXT, " \
                  "value TEXT);"
        self.obj_db_conn.execute("begin transaction")
        self.obj_db_conn.execute(str_sql)
        self.obj_db_conn.commit()

    def insert(self, str_sql, lst_params = ''):
        self.obj_db_conn.execute("begin transaction")
        self.obj_db_conn.execute(str_sql, lst_params)
        self.obj_db_conn.commit()

    def update(self, str_sql, lst_params = ''):
        self.obj_db_conn.execute("begin transaction")
        self.obj_db_conn.execute(str_sql, lst_params)
        self.obj_db_conn.commit()

    def delete(self, str_sql, lst_params = ''):
        self.obj_db_conn.execute("begin transaction")
        self.obj_db_conn.execute(str_sql, lst_params)
        self.obj_db_conn.commit()

    def select(self, str_sql, lst_params = ''):
        obj_cursor = self.obj_db_conn.cursor()
        obj_cursor.execute(str_sql, lst_params)
        return obj_cursor