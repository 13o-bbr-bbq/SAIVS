#!/usr/bin/python
# coding:utf-8
import sys
import datetime
import time
import platform
import numpy as np
from requests import Request, Session
from MyParser import HtmlParser
from MyDbControl import Sqlite3Control
from MyDecision import Decision
from MyEnvironment import Environment
from MyAgent import Agent
from MyInspect import WebInspect
from MyBrowser import Browser

# UrlTreeTBLのカラム情報
str_col_urltreetbl = "site_id, " \
                     "page_no, " \
                     "page_type, " \
                     "accessed, " \
                     "status, " \
                     "parent_no, " \
                     "depth, " \
                     "method, " \
                     "protocol, " \
                     "fqdn, " \
                     "port, " \
                     "path, " \
                     "param, " \
                     "param_no, " \
                     "response_code, " \
                     "request_raw, " \
                     "response_raw, " \
                     "scan_status, " \
                     "enc_type," \
                     "learned," \
                     "param_type," \
                     "param_label," \
                     "access_date"

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


# 初回起動時に指定URLにアクセスし、リンクURLやフォーム送信先のURLを抽出
def initial_access(obj_session, obj_db_control, str_protocol="http", str_fqdn="127.0.0.1", int_port=80, str_path='/'):

    # Webサイトの指定ページにアクセスしてレスポンスを取得
    str_url = str_protocol + "://" + str_fqdn + ":" + str(int_port) + str_path
    obj_request = Request("GET", str_url)
    obj_prepped = obj_session.prepare_request(obj_request)
    obj_response = obj_session.send(obj_prepped,
                                    verify=True,
                                    timeout=60
                                    )

    # レスポンスからaタグのhref要素、formタグの各要素を取得
    obj_parser = HtmlParser()
    obj_decision = Decision()
    lst_ahref = obj_parser.get_a_tags(str_protocol, int_port, str_fqdn, str_path, obj_response.text)
    lst_form, lst_page_type, str_param_label = obj_parser.get_form_tags(str_protocol,
                                                                        int_port,
                                                                        str_fqdn,
                                                                        str_path,
                                                                        obj_response.text)
    obj_parser = None

    # href要素をUrlTreeTBLに登録
    for str_element in lst_ahref:
        if obj_decision.check_target_match(obj_db_control, "GET", str_element, '', '') is False:
            # 実行するSQL文の組み立て
            str_sql = "INSERT INTO UrlTreeTBL(" + str_col_urltreetbl + ") " \
                      "VALUES (1, " \
                      "(SELECT CASE " \
                      "WHEN page_no IS NULL THEN 1 " \
                      "WHEN page_no IS NOT NULL THEN MAX(page_no)+1 " \
                      "END FROM UrlTreeTBL)," \
                      " 0, 0, 0, 0, 1, 'GET', ?, ?, ?, ?, '', 0, '', '', '', 2, '', 0, '', '', '')"

            # Pathの先頭には必ず'/'を付与
            if str_element.startswith('/') is False:
                str_element = '/' + str_element

            # プレースホルダーに埋め込む値をリスト化
            lst_sql_value = [str_protocol, str_fqdn, int_port, str_element]

            # SQL文(insert)の実行
            obj_db_control.insert(str_sql, lst_sql_value)

    # formタグの要素をUrlTreeTBLに登録
    obj_decision = Decision()
    for lst_element in lst_form:
        if obj_decision.check_target_match(obj_db_control,
                                           "POST",
                                           lst_element[0],
                                           lst_element[1],
                                           lst_element[2]) is False:
            # 実行するSQL文の組み立て
            str_sql = "INSERT INTO UrlTreeTBL(" + str_col_urltreetbl + ") " \
                      "VALUES (1, " \
                      "(SELECT CASE " \
                      "WHEN page_no IS NULL THEN 1 " \
                      "WHEN page_no IS NOT NULL THEN MAX(page_no)+1 " \
                      "END FROM UrlTreeTBL)," \
                      " ?, 0, 0, 0, 1, 'POST', ?, ?, ?, ?, ?, ?, '', '', '', 0, ?, 0, ?, ?, '')"

            # form要素を基に、ページタイプ(ログイン、会員登録、検索など)を判定する。
            int_page_type = obj_decision.decide_page_type(lst_page_type)

            # Pathの先頭には必ず'/'を付与
            if lst_element[1].startswith('/') is False:
                lst_element[1] = '/' + lst_element[1]

            # プレースホルダーに埋め込む値をリスト化
            lst_sql_value = [int_page_type, str_protocol, str_fqdn, int_port, lst_element[1], lst_element[3],
                             int(lst_element[3].count('&'))+1, lst_element[2], lst_element[5], str_param_label]

            # SQL文(insert)の実行
            obj_db_control.insert(str_sql, lst_sql_value)

# メイン
if __name__ == "__main__":
    obj_session = Session()
    # コマンドライン引数から対象のドメイン、パスなどを取得
    lst_argvs = sys.argv
    int_argvc = len(lst_argvs)

    # CAPTCHA解析テスト
    # obj_recog = RecognizeImage()
    # obj_recog.recognize_captcha(".\\data\\cp1.png")

    # 引数チェック
    # 第一引数が未指定、http、https以外の場合はプログラム終了
    if lst_argvs[1].strip() is not None and lst_argvs[1] != "http" and lst_argvs[1] != "https":
        print("argv[0] is not http or https.")
        sys.exit(0)

    # 第三引数が数値ではない、または、1～65535以外の数値の場合はプログラム終了
    if lst_argvs[3].strip() is not None and lst_argvs[3].isdigit() is True\
            and (int(lst_argvs[3]) < 0 or int(lst_argvs[3]) > 65535):
        print("argv[2] is invalid.")
        sys.exit(0)

    # 第五引数がTRAIN または ACTION以外の場合はTRAINとする
    str_train_action = lst_argvs[5]
    if str_train_action != 'TRAIN' and str_train_action != 'ACTION':
        str_train_action = 'TRAIN'

    # SAIVSクレジットの表示
    print("###################################################")
    print("#                                                 #")
    print("# / ____|      /\     |_   _| \ \    / / / ____|  #")
    print("# | (___      /  \      | |    \ \  / /  | (___   #")
    print("#  \___ \    / /\ \     | |     \ \/ /    \___ \  #")
    print("#  ____) |  / ____ \   _| |_     \  /     ____) | #")
    print("# |_____/  /_/    \_\ |_____|     \/     |_____/  #")
    print("#                                                 #")
    print("###################################################")
    print("python ver : %s" % platform.python_version())
    print("Using 'Keras, word2vec, BeautifulSoup, Request'")
    print("\n")
    print("Scanning target : " + lst_argvs[1] + "://" + lst_argvs[2] + ":" + lst_argvs[3] + lst_argvs[4] + "\n")
    time.sleep(5)

    # 開始時間の取得
    flt_start = time.time()

    # Webサイトのトップページにアクセスし、1階層目のリンク、フォームをDBに登録
    # 但し、一回取得している場合は実行しない
    obj_db_control = Sqlite3Control()
    # DBの初期化（CODE BLUEデモ用）
    str_sql = "DELETE FROM CredentialsTBL;"
    obj_db_control.delete(str_sql)
    str_sql = "DELETE FROM UrlTreeTBL;"
    obj_db_control.delete(str_sql)
    str_sql = "DELETE FROM ScanResultTBL;"
    obj_db_control.delete(str_sql)

    str_sql = "SELECT id FROM UrlTreeTBL WHERE site_id = 1"
    obj_cursor = obj_db_control.select(str_sql)
    lst_all_row = obj_cursor.fetchall()
    if len(lst_all_row) == 0:
        initial_access(obj_session, obj_db_control, lst_argvs[1], lst_argvs[2], lst_argvs[3], lst_argvs[4])

    # デモ用ブラウザの起動
    obj_browser = Browser()
    obj_browser.start_browser()

    # 未アクセスのリンク、フォームを取得(site_id,page_noで昇順)
    obj_cursor = None
    str_sql = "SELECT * FROM UrlTreeTBL WHERE accessed = 0 ORDER BY site_id ASC, page_no ASC"
    obj_cursor = obj_db_control.select(str_sql)

    # 取得したレコードをリストに格納
    lst_all_row = obj_cursor.fetchall()

    # 1階層ずつ遷移。全てのURLにアクセスし終えたら終了。
    obj_parser = HtmlParser()
    obj_decision = Decision()
    obj_env = Environment(str_train_action, obj_browser)
    obj_agent = Agent(save_name='dqn_crawl')
    obj_web_inspect = WebInspect(obj_browser)
    lst_ahref = []
    lst_form = []
    bol_login_skip_flag = False
    int_loop_count = 0
    bol_1st_regist_flag = True
    while int_loop_count < 1000:

        # UrlTreeTBLに登録された未アクセスのURLにアクセス
        for lst_row in lst_all_row:
            # 環境に対象URLを設定
            obj_env.set_url(obj_decision.assemble_url(lst_row))

            int_depth = 1

            # ルートから当該ページまでの順序を取得([n, n-1, n-2, ... , root])
            lst_flow = [int(lst_row[2])]
            int_page_no = int(lst_row[2])
            int_parent_no = int(lst_row[6])
            obj_cursor = None
            if int_parent_no != 0:
                lst_flow = obj_web_inspect.get_flow(obj_db_control, lst_flow, int_parent_no)

            # ルートから当該ページの一つ手前まで遷移
            if obj_web_inspect.flow_replay(obj_session, obj_db_control, obj_agent, lst_row, lst_flow) is False:
                int_loop_count += 1
                continue

            # POSTパラメータが存在する場合
            dic_post_params = {}
            if lst_row[13] != '':
                # 最新のパラメータ構成を取得
                dic_post_params, bol_login_skip_flag = obj_decision.update_post_parameter(obj_db_control, lst_row)

            # ログイン処理、かつ、ログインアカウントが存在しない場合はスキップ
            if bol_login_skip_flag is True:
                int_loop_count += 1
                continue

            obj_response = None

            # 状態(State)の設定(親ページNo、次ページNo、遷移状態(0…初期、1…成功、-1…エラー)
            lst_state = [lst_row[6], lst_row[2], 0]

            # 全パラメータ構成を定義
            lst_init_param, bol_agent_use_flag = obj_env.create_init_param(dic_post_params)

            # DQNを使用する場合
            if bol_agent_use_flag is True and str_train_action == 'TRAIN':
                # DQNの定義
                # 10/1 追加
                nd_state = np.array(lst_state, dtype=np.uint8)
                obj_agent.build_dqn(state_size=nd_state.shape, number_of_actions=len(lst_init_param))
                obj_agent.new_episode()
                int_action, nd_values = obj_agent.act(nd_state)
                dic_post_params = dict(lst_init_param[int_action])

                # エージェントの学習
                obj_response = obj_env.flow_learning(obj_db_control,
                                                     obj_session,
                                                     obj_agent,
                                                     obj_web_inspect,
                                                     lst_row,
                                                     lst_flow,
                                                     dic_post_params,
                                                     )

            # 学習結果を基にリクエストを送信
            obj_response, dic_success_params = obj_env.send_message(obj_db_control,
                                                                    obj_session,
                                                                    obj_agent,
                                                                    obj_web_inspect,
                                                                    lst_state,
                                                                    lst_row,
                                                                    lst_flow
                                                                    )

            # 対象が会員登録または会員情報編集＆パスワード変更の場合、認証情報をUpdateする。
            if lst_row[3] == 2 and bol_1st_regist_flag is True:
                # 初めての会員登録か否か
                if lst_row[3] == 2:
                    bol_1st_regist_flag = False

                # 認証情報の取得
                lst_param = obj_decision.change_dictionary_to_list(dic_success_params)
                lst_credentials, str_temp_label_value = obj_decision.decide_get_credentials(lst_param, lst_row[22])

                # 認証情報が取得できた場合、認証情報を入れ替える
                if len(lst_credentials) != 0:
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

                    # UrlTreeTBLをUpdate(アクセスの優先度を上げる(accessed=0))
                    str_sql = "UPDATE UrlTreeTBL SET" \
                              " accessed = 0" \
                              " WHERE page_type = 1 AND site_id = 1 AND accessed = 2;"
                    obj_db_control.update(str_sql)

                # 認証情報が取得できない場合、一旦temp領域にパラメータ情報を入れておく
                else:
                    '''
                    str_sql = "DELETE FROM CredentialsTBL WHERE site_id = 1;"
                    obj_db_control.delete(str_sql)

                    str_sql = "INSERT INTO CredentialsTBL(" + str_col_credentialstbl + ") " \
                              "VALUES (1, 1, '', '', '', '', '', '', '', ?)"
                    lst_value = [str_temp_label_value]
                    obj_db_control.insert(str_sql, lst_value)
                   '''

            # レスポンスを受信した場合はDBの更新処理を行う。
            if obj_response is not None:
                # レスポンスからaタグのhref要素を取得
                lst_ahref = obj_parser.get_a_tags(lst_row[9].encode(), str(lst_row[11]),
                    lst_row[10].encode(), lst_row[12].encode(), obj_response.text)

                # レスポンスからformタグの各要素を取得
                lst_form, lst_page_type, str_param_label = obj_parser.get_form_tags(lst_row[9].encode(),
                    str(lst_row[11]),
                    lst_row[10].encode(),
                    lst_row[12].encode(),
                    obj_response.text)

                # アクセスした結果をUrlTreeTBLにUpdate
                str_sql = "UPDATE UrlTreeTBL SET" \
                          " accessed = 1," \
                          " response_code = ?," \
                          " request_raw = ?," \
                          " response_raw = ?," \
                          " learned = 1," \
                          " access_date = ?" \
                          " WHERE id = ?;"
                lst_value = [obj_response.status_code, "no data", obj_response.text,
                             datetime.datetime.today(), lst_row[0]]
                obj_db_control.update(str_sql, lst_value)

                # 会員登録後ページに含まれるリンク、フォームは登録しない
                if lst_row[3] != 2:
                    # href要素をUrlTreeTBLに登録
                    for str_element in lst_ahref:
                        # 重複するURL(パス+GETパラメータ)が存在しない場合に登録(重複排除)
                        if obj_decision.check_target_match(obj_db_control,
                                                           "GET",
                                                           str_element,
                                                           '',
                                                           '') is False:
                            str_sql = "INSERT INTO UrlTreeTBL(" + str_col_urltreetbl + ") " \
                                      "VALUES (1, " \
                                      "(SELECT CASE " \
                                      "WHEN page_no IS NULL THEN 1 " \
                                      "WHEN page_no IS NOT NULL THEN MAX(page_no)+1 " \
                                      "END FROM UrlTreeTBL)," \
                                      " 0, 0, 0, ?, ?, 'GET', ?, ?, ?, ?, '', 0, '', '', '', 2, '', 0, '', '', '')"

                            if str_element.startswith('/') is False:
                                str_element = '/' + str_element

                            lst_value = [lst_row[2], int(lst_row[7])+1, lst_row[9].encode(),
                                         lst_row[10].encode(), lst_row[11], str_element]
                            obj_db_control.insert(str_sql, lst_value)

                    # formタグの要素をUrlTreeTBLに登録
                    for lst_element in lst_form:
                        # 重複するURL(パス+GETパラメータ+POSTパラメータ)が存在しない場合に登録(重複排除)
                        if obj_decision.check_target_match(obj_db_control,
                                                           lst_element[0].upper(),
                                                           lst_element[1],
                                                           lst_element[3],
                                                           lst_element[2]) is False:
                            str_sql = "INSERT INTO UrlTreeTBL(" + str_col_urltreetbl + ") " \
                                      "VALUES (1, " \
                                      "(SELECT CASE " \
                                      "WHEN page_no IS NULL THEN 1 " \
                                      "WHEN page_no IS NOT NULL THEN MAX(page_no)+1 " \
                                      "END FROM UrlTreeTBL)," \
                                      " ?, 0, 0, ?, ?, ?, ?, ?, ?, ?, ?, ?, '', '', '', 0, ?, 0, ?, ?, '')"

                            # ページタイプ(ログイン、会員登録、検索など)の判定
                            int_page_type = 0
                            if len(lst_page_type) != 0:
                                int_page_type = obj_decision.decide_page_type(lst_page_type)
                            else:
                                int_page_type = 0

                            if lst_element[1].startswith('/') is False:
                                lst_element[1] = '/' + lst_element[1]

                            lst_value = [int_page_type, lst_row[2], int(lst_row[7])+1, lst_element[0].upper(),
                                         lst_row[9].encode(), lst_row[10].encode(), lst_row[11], lst_element[1],
                                         lst_element[3], int(lst_element[3].count('&'))+1, lst_element[2],
                                         lst_element[5], str_param_label]
                            obj_db_control.insert(str_sql, lst_value)

                # 診断の実施
                if lst_row[18] == 0:
                    print("\n")
                    print("####################### Attack #############################")
                    print("Target URL :" + obj_decision.assemble_url(lst_row))
                    print("############################################################")
                    # time.sleep(2)
                    bol_vuln_flag = obj_web_inspect.exec_inspect(obj_db_control,
                                                                 obj_agent,
                                                                 obj_env,
                                                                 lst_row,
                                                                 lst_flow,
                                                                 str_train_action)

                    str_sql = "UPDATE UrlTreeTBL SET" \
                              " scan_status = 1" \
                              " WHERE id = ?;"
                    lst_value = [lst_row[0]]
                    obj_db_control.update(str_sql, lst_value)

                    if bol_vuln_flag is True:
                        print("\n")

            # リストの初期化
            lst_ahref = ''
            lst_form = ''

        # n階層目のリンク、フォームを全取得
        str_sql = "SELECT * FROM UrlTreeTBL WHERE accessed = 0 AND site_id = 1 " \
                  "ORDER BY site_id ASC, page_no ASC, depth ASC"
        obj_cursor = obj_db_control.select(str_sql)
        lst_all_row = obj_cursor.fetchall()

        # 全ページにアクセスし終えたら終了
        if len(lst_all_row) == 0:
            break

        # loop countを1インクリメント(無限ループ防止)
        int_loop_count += 1

    # 診断結果の出力
    # 診断対象リストを取得
    str_sql = "SELECT * FROM UrlTreeTBL ORDER BY site_id ASC, page_no ASC"
    obj_cursor = obj_db_control.select(str_sql)
    lst_target_row = obj_cursor.fetchall()

    f = open("scan_result_" + str(datetime.date.today()) + ".csv", 'w')
    f.write("[Target List]\n")
    f.write("No" + "," + "Method" + "," + "PageType" + "," + "URL" + "," + "Status" + "," + "Date" + "\n")
    for lst_row in lst_target_row:
        str_page_type = ''
        if int(lst_row[3]) == 1:
            str_page_type = 'Login'
        elif int(lst_row[3]) == 2:
            str_page_type = 'Register'
        elif int(lst_row[3]) == 3:
            str_page_type = 'Search'
        elif int(lst_row[3]) == 4:
            str_page_type = 'Settlement'
        elif int(lst_row[3]) == 5:
            str_page_type = 'Edit'
        else:
            str_page_type = 'Unknown'

        str_url = obj_decision.assemble_url(lst_row)
        str_record = str(lst_row[2]) + "," \
                     + lst_row[8] + ","\
                     + str_page_type + ","\
                     + str_url + ","\
                     + lst_row[15] + ","\
                     + lst_row[23] + "\n"
        f.write(str_record.encode())

    # 脆弱性判定の情報を取得
    str_sql = "SELECT * FROM ScanResultTBL WHERE result = 1"
    obj_cursor = obj_db_control.select(str_sql)
    lst_result_row = obj_cursor.fetchall()

    f.write("\n")
    f.write("[Scan Result]\n")
    f.write("No" + "," + "Param Name" + "," + "Value" + "," + "Vulnerability" + "," + "Date" + "\n")
    for lst_row in lst_result_row:
        f.write(str(lst_row[2]) + ","
                + lst_row[4] + ","
                + lst_row[7] + ","
                + str(lst_row[6]) + ","
                + lst_row[13] + "\n")

    f.close()
    obj_browser.refresh_browser()
    # obj_browser.close_browser()
    print("\n")
    print("######################## Finish!! ###########################")

    # サマリの表示
    str_sql = "SELECT id FROM UrlTreeTBL WHERE site_id = 1 and accessed = 1"
    obj_cursor = obj_db_control.select(str_sql)
    lst_page_row = obj_cursor.fetchall()
    print("Crawled pages : %d" % len(lst_page_row))
    str_sql = "SELECT id FROM UrlTreeTBL WHERE site_id = 1 and scan_status = 1"
    obj_cursor = obj_db_control.select(str_sql)
    lst_page_row = obj_cursor.fetchall()
    print("Scanned pages : %d" % len(lst_page_row))
    print("Detected RXSS : %d" % len(lst_result_row))
    flt_elapsed_time = time.time() - flt_start
    print("Elapsed time  :{0}".format(flt_elapsed_time) + "[sec]")

