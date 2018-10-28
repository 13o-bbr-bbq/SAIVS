#!/usr/bin/python
# coding:utf-8
import random
import string
from requests import Request, Session
from MyDecision import Decision
from MyXSS import XSS
from MyWord2Vec import Word2Vec

# const variable
PROXY = {'http': '127.0.0.1:8083'}


# 診断リクエストの生成・送信・レスポンスの受信
class WebInspect(object):
    # コンストラクタ
    def __init__(self, obj_browser=None):
        self.obj_browser = obj_browser
        self.bol_result_display = True
        self.str_dummy_file_path = "C:\\Users\\itaka\\PycharmProjects\\saivs\\dummy.png"

    # UrlTreeTBLを基に画面遷移を再現
    def flow_replay(self, obj_session, obj_db_control, obj_agent, lst_row, lst_flow):
        obj_decision = Decision()
        int_flow_idx = 1
        bol_flow_status = True

        while int_flow_idx < len(lst_flow):
            lst_value = []
            int_page_no = lst_flow[len(lst_flow) - int_flow_idx]
            str_sql = "SELECT * FROM UrlTreeTBL WHERE site_id = 1 AND page_no = " + str(int_page_no)
            obj_cursor = obj_db_control.select(str_sql)
            lst_flow_row = obj_cursor.fetchone()

            bol_skip_flag = False
            obj_response = None
            # POSTパラメータが存在する場合
            if lst_flow_row[13] != '':
                # 親ページのレスポンス内から最新のパラメータ値を取得
                dic_post_flow_params = {}
                dic_post_flow_params, bol_skip_flag = obj_decision.update_post_parameter(obj_db_control, lst_flow_row)

                # ログイン処理以外の場合
                if lst_flow_row[3] != 1:
                    # 学習結果に基づき遷移に最適なパラメータ値を設定
                    int_idx = 0
                    bol_relearn_flag = False
                    lst_param_names = lst_flow_row[13].split('&')
                    lst_param_types = lst_flow_row[21].split(',')
                    lst_label_names = lst_flow_row[22].split(',')
                    while int_idx < int(lst_flow_row[14]):
                        # 対象パラメータがhiddenではない。かつ、ログイン処理(1)ではない場合。
                        if lst_label_names[int_idx] != '@' and lst_flow_row[3] != 1:
                            str_sql = "SELECT value from WordSimilarityTBL where word like '%" \
                                      + lst_label_names[int_idx] + "%';"
                            obj_cursor = obj_db_control.select(str_sql)
                            lst_all_row = obj_cursor.fetchall()
                            lst_param_names_tmp = lst_param_names[int_idx].split('=')
                            # 類似単語が類似単語管理テーブルに存在する
                            if len(lst_all_row) != 0:
                                lst_candidate = list(lst_all_row[0])
                                str_candidate_value = str(lst_candidate[0])
                                int_find_idx = str_candidate_value.find('@')
                                if int_find_idx > 0:
                                    str_random_value = ''.join(
                                        [random.choice(string.digits) for i in range(int_find_idx)])
                                    str_candidate_value = str_random_value + str_candidate_value[int_find_idx:]
                                dic_post_flow_params[lst_param_names_tmp[0]] = str_candidate_value
                            # 類似単語が類似単語管理テーブルに存在しない
                            else:
                                obj_word2vec = Word2Vec()
                                obj_result = obj_word2vec.get_candidate_word(lst_label_names[int_idx])
                                if obj_result is not False:
                                    for r in obj_result:
                                        str_sql = "SELECT value from WordSimilarityTBL where word like '%" \
                                                  + r[0] + "%';"
                                        obj_cursor = obj_db_control.select(str_sql)
                                        lst_all_row = obj_cursor.fetchall()
                                        if len(lst_all_row) != 0:
                                            lst_candidate = list(lst_all_row[0])
                                            str_candidate_value = str(lst_candidate[0])
                                            int_find_idx = str_candidate_value.find('@')
                                            if int_find_idx > 0:
                                                str_random_value = \
                                                    ''.join([random.choice(string.digits) for i in range(int_find_idx)])
                                                str_candidate_value = str_random_value + str_candidate_value[
                                                                                         int_find_idx:]
                                            dic_post_flow_params[lst_param_names_tmp[0]] = str_candidate_value
                                            break
                                    if dic_post_flow_params[lst_param_names_tmp[0]] == '':
                                        bol_relearn_flag = True
                                else:
                                    bol_relearn_flag = True
                        int_idx += 1

                    # if bol_relearn_flag is True:
                        # print('I don\'t know this param value.')
                        # return

                # POSTリクエストの送信
                obj_request = None
                if lst_flow_row[19] == "multipart/form-data":
                    # マルチパートリクエスト
                    dic_post_files = {}
                    dic_post_data = {}

                    # ファイルを保持するパラメータと通常のパラメータに切り分ける
                    dic_post_files, dic_post_data = obj_decision.divide_params(lst_flow_row[21],
                                                                               dic_post_flow_params,
                                                                               self.str_dummy_file_path)

                    obj_request = Request("POST",
                                          obj_decision.assemble_url(lst_row),
                                          files=dic_post_files,
                                          data=dic_post_data
                                          )
                else:
                    # 通常のリクエスト
                    if lst_flow_row[8] == 'POST':
                        obj_request = Request("POST",
                                              obj_decision.assemble_url(lst_flow_row),
                                              data=dic_post_flow_params
                                              )
                    else:
                        obj_request = Request("GET",
                                              obj_decision.assemble_url(lst_flow_row),
                                              params=dic_post_flow_params
                                              )

                obj_prepped = obj_session.prepare_request(obj_request)
                obj_response = obj_session.send(obj_prepped,
                                                verify=True,
                                                timeout=60,
                                                proxies=PROXY,
                                                allow_redirects=False
                                                )
            else:
                obj_request = Request("GET",
                                      obj_decision.assemble_url(lst_flow_row),
                                      )
                obj_prepped = obj_session.prepare_request(obj_request)
                obj_response = obj_session.send(obj_prepped,
                                                verify=True,
                                                timeout=60,
                                                proxies=PROXY,
                                                allow_redirects=False
                                                )
            # レスポンスをブラウザに表示（デモ用）
            if obj_response is not None:
                self.obj_browser.write_response_to_html(obj_response.text, obj_response.encoding)
                self.obj_browser.refresh_browser()

            # レスポンスがリダイレクトの場合
            # リダイレクトが終了するまで繰り返しリダイレクト
            while obj_response.is_redirect is True:
                # Locationヘッダから遷移先URLを取得
                dic_res_headers = obj_response.headers._store
                tpl_location_header = dic_res_headers["location"]
                str_redirect_url = tpl_location_header[1]
                if 'http' not in str_redirect_url and 'https' not in str_redirect_url:
                    str_fqdn = lst_flow_row[9].encode() + "://" + lst_flow_row[10].encode() + ":" + str(lst_flow_row[11])
                    if str_redirect_url.startswith('/') is False:
                        str_redirect_url = '/' + str_redirect_url
                    str_redirect_url = str_fqdn + str_redirect_url

                # リダイレクト
                obj_request = Request("GET", str_redirect_url)
                obj_prepped = obj_session.prepare_request(obj_request)
                obj_response = obj_session.send(obj_prepped,
                                                verify=True,
                                                timeout=60,
                                                proxies=PROXY,
                                                allow_redirects=False
                                                )

            # レスポンスをブラウザに表示（デモ用）
            if obj_response is not None:
                self.obj_browser.write_response_to_html(obj_response.text, obj_response.encoding)
                self.obj_browser.refresh_browser()

            # エラーが返ってきた場合の処理
            # TODO
            bol_flow_status = True

            # 最新のレスポンス値に更新
            if bol_skip_flag is False:
                str_parent_sql = "UPDATE UrlTreeTBL SET" \
                                 " response_raw = ?" \
                                 " WHERE id = ?;"
                lst_parent_value = [obj_response.text, lst_flow_row[0]]
                obj_db_control.update(str_parent_sql, lst_parent_value)

            int_flow_idx += 1

        return bol_flow_status

    # UrlTreeTBLを基に画面遷移順序を取得
    def get_flow(self, obj_db_control, lst_flow, int_parent_no):
        while int_parent_no != 0:
                lst_flow.append(int_parent_no)
                str_flow_sql = "SELECT parent_no FROM UrlTreeTBL WHERE site_id = 1 AND page_no = ?"
                lst_flow_value = [int_parent_no]
                obj_cursor = obj_db_control.select(str_flow_sql, lst_flow_value)
                lst_all_row = obj_cursor.fetchone()
                int_parent_no = int(lst_all_row[0])

        return lst_flow

    # 診断のメインコントロール
    def exec_inspect(self, obj_db_control, obj_agent, obj_env, lst_target_row, lst_flow, str_train_action):
        obj_decision = Decision()
        bol_vuln_flag = False

        int_param_count = 0
        while int_param_count < lst_target_row[14]:
            # XSSの検査
            obj_xss = XSS(int_param_count, str_train_action, self.obj_browser)
            obj_xss.exec_xss(obj_db_control, obj_agent, lst_target_row, lst_flow)
            int_param_count += 1

        return bol_vuln_flag