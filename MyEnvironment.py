#!/usr/bin/python
# coding:utf-8
import numpy as np
import random
import string
from requests import Request, Session
from MyDecision import Decision
from MyWord2Vec import Word2Vec

PROXY = {'http': '127.0.0.1:8083'}

# CredentialsTBLのカラム情報
str_col_credentialstbl = "site_id, " \
                         "type, " \
                         "credential_info1, " \
                         "credential_info2, " \
                         "credential_info3, " \
                         "credential_info4, " \
                         "credential_info5, " \
                         "secret_question, " \
                         "secret_answer, " \
                         "temp"

# WordSimilarityTBLのカラム情報
str_col_wordsimilaritytbl = "page_type, " \
                            "word, " \
                            "value"

# 環境の定義
class Environment(object):
    int_max_learning_episode = 30  # 学習回数
    #int_max_learning_episode = 100
    int_which_episode = 0
    int_learning_episode = 0
    int_total_reward = 0
    int_total_step = 0

    # multipartリクエスト用のダミーファイル
    str_dummy_file_path = ".\\dummy.png"

    # パラメータ値の集合(16種類)
    str_3num = str(random.randint(100, 999))
    str_6num = str(random.randint(100000, 999999))
    str_8num = str(random.randint(10000000, 99999999))
    str_9num = str(random.randint(100000000, 999999999))
    str_12num = str(random.randint(100000000000, 999999999999))
    str_16num = str(random.randint(1000000000000000, 9999999999999999))
    #lst_param_value_collections = [str_3num, str_6num, str_9num, str_12num, str_16num,
    #                               "abc", "abcdef", "abcdefghi",
    #                               str_3num + "abc", str_6num + "abcdef",
    #                               str_3num + "@@@", str_6num + "@@@@@@",
    #                               "abc@@@", str_16num + "@hoge.com",
    #                               str_3num + "ab@@", str_6num + "abcd@@@@"]

    # パラメータ値の集合(4種類)
    lst_param_value_collections = [str_8num, str_16num, str_3num + "abc", str_16num + "@hoge.com"]

    def __init__(self, str_train_action='TRAIN', obj_browser=None):
        self.obj_browser = obj_browser
        self.bol_use_dqn_flag = False
        self.lst_create_param = []
        self.lst_default_param = []
        self.str_train = str_train_action

    # 対象URLの設定
    def set_url(self, str_url):
        self.str_target_url = str_url

    # パラメータ値の集合の更新
    def update_random_params(self):
        self.str_3num = str(random.randint(100, 999))
        self.str_6num = str(random.randint(100000, 999999))
        self.str_8num = str(random.randint(10000000, 99999999))
        self.str_9num = str(random.randint(100000000, 999999999))
        self.str_12num = str(random.randint(100000000000, 999999999999))
        self.str_16num = str(random.randint(1000000000000000, 9999999999999999))
        #self.lst_param_value_collections = [self.str_3num, self.str_6num, self.str_9num, self.str_12num, self.str_16num,
        #                                    "abc", "abcdef", "abcdefghi",
        #                                    self.str_3num + "abc", self.str_6num + "abcdef",
        #                                    self.str_3num + "@@@", self.str_6num + "@@@@@@",
        #                                    "abc@@@", self.str_16num + "@hoge.com",
        #                                    self.str_3num + "ab@@", self.str_6num + "abcd@@@@"]

        # パラメータ値の集合(4種類)
        self.lst_param_value_collections = [self.str_8num, self.str_16num,
                                            self.str_3num + "abc", self.str_16num + "@hoge.com"]

    # 最適パラメータの取得
    def index_to_action(self, int_index_action, dic_post_param):
        lst_param_name = dic_post_param.keys()
        for str_param_name in lst_param_name:
            # 値が未設定の場合
            if dic_post_param[str_param_name] == '':
                # ε-greedyで選択した値をパラメータ値に設定
                dic_post_param[str_param_name] = self.lst_param_value_collections[int_index_action]

        return dic_post_param

    # 初回アクセス時のパラメータ構成を定義
    def create_init_param(self, dic_post_params=''):
        # 行動パターンの算出：パラメータと全候補パラメータ値の組み合わせ
        # 但し、元値を持っているパラメータには候補パラメータ値を設定しない
        lst_param_name = dic_post_params.keys()
        lst_param_collections = []
        lst_value_collections2 = []
        lst_param_collections_no_value = []
        int_idx = 0
        int_repeat = 0

        # パラメータ毎の取り得る値を設定
        for str_param_name in lst_param_name:
            # 値が未設定のパラメータを抽出
            if dic_post_params[str_param_name] == '':
                lst_param_collections_no_value.append(str_param_name)
                int_repeat += 1
            # 値が設定されているパラメータを抽出
            else:
                lst_param_collections.append(tuple([str_param_name, dic_post_params[str_param_name]]))

            int_idx += 1

        # 値が未設定のパラメータが存在する場合
        if int_repeat != 0:
            lst_param_temp = []

            for str_value_collection in self.lst_param_value_collections:
                for int_idx in range(int_repeat):
                    lst_param_temp.append(tuple([lst_param_collections_no_value[int_idx], str_value_collection]))
                lst_value_collections2.append(lst_param_temp)
                lst_param_temp = []

            # 全パラメータ組み合わせを行動パターンとする
            for int_idx in range(len(lst_value_collections2)):
                lst_value_collections2[int_idx] += lst_param_collections

            self.bol_use_dqn_flag = True
            return lst_value_collections2, self.bol_use_dqn_flag

        # 既存のパラメータに全て値が入力されている、または、POSTパラメータが無い場合
        else:
            # print "Not Use DQN."
            self.lst_default_param = lst_param_collections
            self.bol_use_dqn_flag = False
            return lst_param_collections, self.bol_use_dqn_flag

    # HTTPレスポンス内容から状態を判定
    def judge_state(self, obj_response, int_group_id, int_parent_seq):
        obj_decision = Decision()

        # 正常遷移の可否を判定
        #int_result, int_score = obj_decision.decide_flow_okng(obj_response, int_group_id, int_parent_seq)
        int_result = obj_decision.decide_flow_okng(obj_response, int_group_id, int_parent_seq)
        int_next_state = 0
        if int_result == 1:
            int_reward = 1000              # 正常遷移した場合は報酬「100」を与える
            int_next_state = 10            # 正常遷移した場合は状態を成功「1」にする
        elif int_result == 0:
            int_reward = -1000             # 正常遷移しない場合は報酬「-100」を与える
            int_next_state = 1             # 正常遷移しない場合は状態を変化なし「0」にする
        else:
            int_reward = -1000             # エラーが発生した場合は報酬「-1000」を与える
            int_next_state = 0             # エラーが発生した場合は状態をエラー「-1」にする

        return int_reward, int_next_state

    # 当該ページへの遷移方法を学習
    def flow_learning(self,
                      obj_db_control,
                      obj_session,
                      obj_agent,
                      obj_web_inspect,
                      lst_row,
                      lst_flow,
                      dic_post_params):
        obj_decision = Decision()
        lst_temp_action = []
        int_reward = 0

        # 学習済みデータの有無を確認
        # エージェントの学習
        int_learning_episode = 0
        int_total_cost = 0.0    # 10/1 追加
        int_total_reward = 0.0  # 10/1 追加
        int_frame = 0  # 10/1 追加
        while int_learning_episode < self.int_max_learning_episode:
            int_frame += 1
            int_reward = 0
            obj_request = None

            # POSTリクエストの送信
            if lst_row[19] == "multipart/form-data":
                # マルチパートリクエスト
                dic_post_files = {}
                dic_post_data = {}

                # ファイルを保持するパラメータと通常のパラメータに切り分ける
                dic_post_files, dic_post_data = obj_decision.divide_params(lst_row[21],
                                                                           dic_post_params,
                                                                           self.str_dummy_file_path)
                obj_request = Request("POST",
                                      obj_decision.assemble_url(lst_row),
                                      files=dic_post_files,
                                      data=dic_post_data
                                      )
            else:
                # 通常のリクエスト
                if lst_row[8].upper() == 'POST':
                    obj_request = Request("POST",
                                          obj_decision.assemble_url(lst_row),
                                          data=dic_post_params
                                          )
                else:
                    obj_request = Request("GET",
                                          obj_decision.assemble_url(lst_row),
                                          params=dic_post_params
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
                if 'http://' not in str_redirect_url and 'https://' not in str_redirect_url:
                    str_fqdn = lst_row[9].encode() + "://" + lst_row[10].encode() + ":" + str(lst_row[11])
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

            # レスポンス内容から報酬を決定
            int_reward, int_next_state = self.judge_state(obj_response, lst_row[2], lst_row[6])

            # 対象が会員情報変更の場合、かつ、遷移に成功した場合、認証情報を入れ替える
            if lst_row[3] == 5 and int_reward > 0:
                # 認証情報の取得
                lst_credentials, str_temp_label_value = obj_decision.decide_get_credentials(
                    obj_decision.change_dictionary_to_list(dic_post_params),
                    lst_row[22])

                # 認証情報が取得できた場合、認証情報を入れ替える
                if lst_credentials[0] is not None and lst_credentials[1] is not None:
                    str_sql = "DELETE FROM CredentialsTBL WHERE site_id = 1;"
                    obj_db_control.delete(str_sql)
                    str_sql = "INSERT INTO CredentialsTBL(" + str_col_credentialstbl + ") " \
                              "VALUES (1, 1, ?, ?, ?, ?, ?, '', '', '')"
                    lst_value = [lst_credentials[0],
                                 lst_credentials[1],
                                 lst_credentials[2],
                                 lst_credentials[3],
                                 lst_credentials[4]]
                    obj_db_control.insert(str_sql, lst_value)
                # 認証情報が取得できない場合、一旦temp領域にパラメータ情報を入れておく
                else:
                    str_sql = "DELETE FROM CredentialsTBL WHERE site_id = 1;"
                    obj_db_control.delete(str_sql)

                    str_sql = "INSERT INTO CredentialsTBL(" + str_col_credentialstbl + ") " \
                              "VALUES (1, 1, '', '', '', '', '', '', '', ?)"
                    lst_value = [str_temp_label_value]
                    obj_db_control.insert(str_sql, lst_value)

            # 次の状態を設定
            lst_state_dash = [lst_row[6], lst_row[2], int_next_state]
            int_total_cost += obj_agent.observe(int_reward)
            int_total_reward += int_reward
            obj_agent.new_episode()
            nd_state = np.array(lst_state_dash, dtype=np.uint8)
            int_index_action, nd_values = obj_agent.act(nd_state)
            print('frame:%d / total reward:%d / total cost:%f / action:%d / reward:%d' %
                  (int_frame, int_total_reward, int_total_cost, int_index_action, int_reward))

            # 次の学習の準備：ルートから当該ページの一つ手前まで遷移
            obj_session = None
            obj_session = Session()  # 新しいセッションで遷移を再生
            if obj_web_inspect.flow_replay(obj_session, obj_db_control, obj_agent, lst_row, lst_flow) is False:
                continue

            # 次の学習の準備：パラメータ値の更新
            # POSTパラメータが存在する場合
            if lst_row[13] != '':
                # 最新のパラメータ構成を取得
                self.update_random_params()
                dic_post_params, bol_skip_flag = obj_decision.update_post_parameter(obj_db_control, lst_row)
                dic_post_params = self.index_to_action(int_index_action, dic_post_params)

            int_learning_episode += 1

            # 学習済みの単語・値のセットを単語類似度管理テーブルに格納
            dic_post_params, bol_skip_flag = obj_decision.update_post_parameter(obj_db_control, lst_row)
            lst_state = [lst_row[6], lst_row[2], 0]
            int_action_index, nd_values = obj_agent.act(np.array(lst_state, dtype=np.uint8))
            lst_params = np.argsort(nd_values)[0].tolist()
            int_action_index = len(lst_params) - 1
            self.update_random_params()
            dic_post_params = self.index_to_action(int_action_index, dic_post_params)

            int_idx = 0
            lst_param_names = lst_row[13].split('&')
            lst_param_types = lst_row[21].split(',')
            lst_label_names = lst_row[22].split(',')
            while int_idx < int(lst_row[14]):
                if lst_label_names[int_idx] != '@':
                    lst_param_names_tmp = lst_param_names[int_idx].split('=')
                    str_param_value = dic_post_params[lst_param_names_tmp[0]]
                    str_sql = "INSERT INTO WordSimilarityTBL(" + str_col_wordsimilaritytbl + ") " \
                              "VALUES (?, ?, ?)"
                    lst_value = [int(lst_row[3]), lst_label_names[int_idx], str_param_value]
                    obj_db_control.insert(str_sql, lst_value)
                int_idx += 1

    # 対象URLにPOSTリクエストを送信し、正常遷移の可否を返却。
    def send_message(self, obj_db_control, obj_session, obj_agent, obj_web_inspect, lst_state, lst_row, lst_flow):
        obj_decision = Decision()

        # DQNを使用する場合、かつ、ログイン処理ではない場合
        if self.bol_use_dqn_flag is True:
            # 最新のパラメータ構成を取得
            dic_post_params, bol_skip_flag = obj_decision.update_post_parameter(obj_db_control, lst_row)

            int_idx = 0
            bol_relearn_flag = False
            lst_param_names = lst_row[13].split('&')
            lst_param_types = lst_row[21].split(',')
            lst_label_names = lst_row[22].split(',')
            while int_idx < int(lst_row[14]):
                if lst_label_names[int_idx] != '@':
                    str_sql = "SELECT value from WordSimilarityTBL where word like '%"\
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
                            str_random_value = ''.join([random.choice(string.digits) for i in range(int_find_idx)])
                            str_candidate_value = str_random_value + str_candidate_value[int_find_idx:]
                        dic_post_params[lst_param_names_tmp[0]] = str_candidate_value
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
                                        str_candidate_value = str_random_value + str_candidate_value[int_find_idx:]
                                    dic_post_params[lst_param_names_tmp[0]] = str_candidate_value
                                    break
                            if dic_post_params[lst_param_names_tmp[0]] == '':
                                bol_relearn_flag = True
                        else:
                            bol_relearn_flag = True
                int_idx += 1

            if bol_relearn_flag is True and self.str_train == 'TRAIN':
                # エージェントの学習
                obj_response = self.flow_learning(obj_db_control,
                                                  obj_session,
                                                  obj_agent,
                                                  obj_web_inspect,
                                                  lst_row,
                                                  lst_flow,
                                                  dic_post_params
                                                  )

                # 学習結果に基づき遷移に最適なパラメータ値を設定
                int_action_index, nd_values = obj_agent.act(np.array(lst_state, dtype=np.uint8))
                lst_params = np.argsort(nd_values)[0].tolist()
                int_action_index = len(lst_params) - 1
                self.update_random_params()
                dic_post_params = self.index_to_action(int_action_index, dic_post_params)

            # POSTリクエストの送信
            if lst_row[19] == "multipart/form-data":
                # マルチパートリクエスト
                dic_post_files = {}
                dic_post_data = {}

                # ファイルを保持するパラメータと通常のパラメータに切り分ける
                dic_post_files, dic_post_data = obj_decision.divide_params(lst_row[21],
                                                                           dic_post_params,
                                                                           self.str_dummy_file_path)

                obj_request = Request("POST",
                                      obj_decision.assemble_url(lst_row),
                                      files=dic_post_files,
                                      data=dic_post_data
                                      )
            else:
                # 通常のリクエスト
                if (lst_row[8].upper() == 'POST'):
                    obj_request = Request(lst_row[8],
                                          obj_decision.assemble_url(lst_row),
                                          data=dic_post_params
                                          )
                else:
                    obj_request = Request(lst_row[8],
                                          obj_decision.assemble_url(lst_row),
                                          params=dic_post_params
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
                if 'http://' not in str_redirect_url and 'https://' not in str_redirect_url:
                    str_fqdn = lst_row[9].encode() + "://" + lst_row[10].encode() + ":" + str(lst_row[11])
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

            return obj_response, dic_post_params

        else:
            # GET/POSTリクエストの送信
            obj_request = Request(lst_row[8],
                                  obj_decision.assemble_url(lst_row),
                                  data=dict(self.lst_default_param)
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
                if 'http://' not in str_redirect_url and 'https://' not in str_redirect_url:
                    str_fqdn = lst_row[9].encode() + "://" + lst_row[10].encode() + ":" + str(lst_row[11])
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

            return obj_response, dict(self.lst_default_param)
