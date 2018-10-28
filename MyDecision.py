#!/usr/bin/python
#coding:utf-8
import difflib
import random
from collections import OrderedDict
from MyNaiveBayes import Classify
from MyDbControl import Sqlite3Control
from MyParser import HtmlParser
from bs4 import BeautifulSoup


# 様々な判定処理を実行
class Decision():

    def __init__(self):
        return

    # ページ種別(ログイン(1)、会員登録(2)、検索(3)、決済(4)、会員編集＆パスワード変更(5)、その他(0))を判定
    def decide_page_type(self, lst_page_type):

        # ページ種別を特徴づけるテキストから判定に不要な記号等を取り除く
        int_idx = 0
        while int_idx < len(lst_page_type):
            str_temp = lst_page_type[int_idx]
            str_temp = str_temp.replace('!', '')
            str_temp = str_temp.replace('@', '')
            str_temp = str_temp.replace('.', '')
            str_temp = str_temp.replace(':', '')
            str_temp = str_temp.replace(' ', '')
            lst_page_type[int_idx] = str_temp.lower()
            int_idx += 1

        # ナイーブベイズでページ種別を判定
        obj_naive_bayes = Classify()
        str_classify_result = obj_naive_bayes.classify_page_type(lst_page_type)
        if str_classify_result == "Login":
            # ログイン
            return 1
        elif str_classify_result == "Regist":
            # 会員登録
            return 2
        elif str_classify_result == "Search":
            # 検索
            return 3
        elif str_classify_result == "Settlement":
            # 決済
            return 4
        elif str_classify_result == "Edit":
            # 会員編集＆パスワード変更
            return 5
        else:
            # その他と判定
            return 0

    # 認証情報をパラメータに設定
    def decide_set_credentials(self, str_new_params, lst_candidate_values, str_param_label):
        lst_new_params = str_new_params.split('&')
        lst_param_label = str_param_label.split(',')
        str_return_params = ''
        if len(lst_new_params) == 1:
            print "Invalid Parameter."
            return str_return_params
        else:
            # ログインID、パスワードの値を設定
            int_idx = 0
            for str_temp_param in lst_new_params:
                lst_temp_param = str_temp_param.split('=')
                str_label = lst_param_label[int_idx]

                # パラメータ値が空の場合に設定
                if lst_temp_param[1] == '':
                    # 認証情報が設定されている場合
                    if lst_candidate_values[3] != '':
                        # 当該パラメータのラベルと一致する認証情報を取得
                        int_idx2 = 0
                        while int_idx2 < 5:
                            lst_credential_param = lst_candidate_values[3 + int_idx2].split(':')
                            if lst_credential_param[0] == str_label:
                                str_return_params += '&' + lst_temp_param[0] + '=' + lst_credential_param[1]
                                break
                            int_idx2 += 1
                    # 認証情報が設定されていない場合はtempから抽出
                    else:
                        lst_credential_candidate = lst_candidate_values[10].split(',')
                        int_idx2 = 0
                        while int_idx2 < len(lst_credential_candidate):
                            lst_label_value = lst_credential_candidate[int_idx2].split(':')
                            if lst_label_value[0] == str_label:
                                str_return_params += '&' + lst_temp_param[0] + '=' + lst_label_value[1]
                                break
                            int_idx2 += 1
                else:
                    # 返却するパラメータをリストに追加
                    str_return_params += '&' + lst_temp_param[0] + '=' + lst_temp_param[1]

                int_idx += 1

        return str_return_params[1:]

    # パラメータから認証情報を取得
    def decide_get_credentials(self, lst_params, str_param_label):
        lst_credential_label = []
        lst_return_credentials = []
        str_temp_label_value = ''

        # UrlTreeTBLからログイン処理用のパラメータラベルを取得
        obj_db_control = Sqlite3Control()
        str_sql = "SELECT param_label FROM UrlTreeTBL WHERE site_id = 1 AND page_type = 1"
        obj_cursor = obj_db_control.select(str_sql)
        lst_row = obj_cursor.fetchone()

        # 既にログインフォームの情報が登録されている場合(会員情報登録の前にログインフォームにアクセスしている)
        if lst_row is not None:
            # ログインフォームのラベル情報を取得
            lst_label = lst_row[0].split(',')
            for str_label in lst_label:
                if str_label != '@':
                    lst_credential_label.append(str_label)

            # 会員情報登録フォーム、会員情報編集フォームのラベル情報を取得
            # パラメータのindexを合わせるため、「@」も含めて取得
            lst_credential_candidate_label = str_param_label.split(',')

            # ログインフォームのラベルが正常に登録されていない場合
            if len(lst_credential_label) == 0:
                print "Invalid Credential Label."
                lst_return_credentials = []
                return lst_return_credentials, str_temp_label_value

            # 会員情報登録・更新のラベルが正常に登録されていない場合
            if len(lst_credential_candidate_label) == 0:
                print "Invalid Credential Candidate Label."
                lst_return_credentials = []
                return lst_return_credentials, str_temp_label_value

            # 会員情報登録・更新のパラメータが正常に取得できていない場合
            if len(lst_params) == 1:
                print "Invalid Parameter."
                lst_return_credentials = []
                return lst_return_credentials, str_temp_label_value

            # 認証情報の取得
            int_idx = 0
            for str_credential_candidate_label in lst_credential_candidate_label:
                for str_credential in lst_credential_label:
                    # 候補文字列がパラメータ名に含まれる場合
                    if str_credential_candidate_label.lower() == str_credential.lower():
                        # 認証情報を取得
                        lst_credential_param = lst_params[int_idx].split('=')
                        # ラベルとパラメータ値のセットを登録
                        lst_return_credentials.append(str_credential.lower() + ':' + lst_credential_param[1])
                int_idx += 1

            # 認証情報の格納数を必ず5にする
            while len(lst_return_credentials) < 5:
                lst_return_credentials.append('')

            # 5つ分の認証情報を返す
            return lst_return_credentials[0:5], str_temp_label_value

        # 未だログインフォームの情報が登録されていない場合(ログインフォームの前に会員情報登録フォームにアクセスしている)
        else:
            # 会員情報登録フォーム、会員情報編集フォームのラベル情報を取得
            # パラメータのindexを合わせるため、「@」も含めて取得
            lst_temp_label = str_param_label.split(',')
            int_idx = 0
            for str_temp_label in lst_temp_label:
                lst_param_value = lst_params[int_idx].split('=')
                str_temp_label_value = str_temp_label_value + ',' + str_temp_label + ':' + lst_param_value[1]
                int_idx += 1

            # 空の認証情報とtempのラベル：値情報を返す
            return lst_return_credentials, str_temp_label_value[1:]


    # 以下の判定ロジックを使って、遷移の成否を判定
    # 判定1：レスポンスコードを利用
    # 判定2：レスポンスボディの差分内容を利用
    def decide_flow_okng(self, obj_response, int_group_id, int_parent_no):
        # レスポンスデータからTitleタグの値を取得
        obj_parser = HtmlParser()
        obj_naive_bayes = Classify()

        # 判定1：レスポンスコードを基に遷移の成否を判定
        if obj_response.status_code == 500 or obj_response.status_code == 503 or obj_response.status_code == 404:
            # レスポンスコードが500,503,404の場合、正常に遷移できなかったとみなす。
            return -1
        # 判定2：レスポンスボディの差分内容を利用
        else:
            # 親ノード(遷移元)のレスポンスデータを取得
            obj_db_control = Sqlite3Control()
            str_sql = "SELECT response_raw FROM UrlTreeTBL WHERE site_id = 1 AND page_no = ?"
            lst_sql_value = [int_parent_no]
            obj_cursor = obj_db_control.select(str_sql, lst_sql_value)
            lst_response_parent = obj_cursor.fetchone()

            # 遷移元と遷移先のレスポンスを比較
            int_diff_count = 0
            str_diff_html = ''
            for str_line in difflib.unified_diff(obj_response.text.splitlines(), lst_response_parent[0].splitlines()):
                # 先頭が空白(一致)ではない場合
                if str_line.startswith(' ') is False:
                    int_diff_count += 1  # 差分行数のカウント
                    str_diff_html += str_line  # 差分内容の取得

            # 差分内容から判定に不要な記号等を取り除く
            obj_bs4 = BeautifulSoup(str_diff_html)
            str_diff_text = obj_bs4.text
            str_diff_text = str_diff_text.replace('-', '')
            str_diff_text = str_diff_text.replace('+', '')
            str_diff_text = str_diff_text.replace('@', '')
            str_diff_text = str_diff_text.replace('[', '')
            str_diff_text = str_diff_text.replace(']', '')
            str_diff_text = str_diff_text.replace('"', '')
            str_diff_text = str_diff_text.replace(',', '')
            str_diff_text = str_diff_text.replace('!', '')
            str_diff_text = str_diff_text.replace('\'', '')
            str_diff_text = str_diff_text.replace('\n', ' ')
            lst_temp = str_diff_text.split(' ')
            lst_diff_text = []
            int_idx = 0
            while int_idx < len(lst_temp):
                if lst_temp[int_idx] != '':
                    lst_diff_text.append(lst_temp[int_idx].lower())
                int_idx += 1

            # 差分内容からストップワードを取り除く
            lst_use_classify_words = obj_naive_bayes.remove_stop_words(lst_diff_text)

            # 差分内容のテキストを基にナイーブベイズで遷移成否を判定
            str_category, int_score = obj_naive_bayes.classify_flow_okng(lst_use_classify_words)
            if str_category == 'NG':
                # 差分内容が"遷移失敗"に分類された場合、正常に遷移できなかったとみなす。
                #return 0, int_score
                return 0
            else:
                # "遷移失敗"以外は全て成功と見なす。
                #return 1, int_score
                return 1

    # request用にパラメータを辞書形式に変換
    def change_string_to_dictionary(self, str_parameter):
        dic_post_params = OrderedDict()

        lst_params = str_parameter.split('&')
        for str_temp in lst_params:
            # パラメータ名とパラメータ値に分割
            int_idx = str_temp.index('=')
            str_temp_name = str_temp[0: int_idx]
            str_temp_value = str_temp[int_idx+1:]

            # 辞書にパラメータ要素を追加
            dic_post_params[str_temp_name] = str_temp_value

        return dic_post_params

    # 辞書形式からリスト形式に変換
    def change_dictionary_to_list(self, dic_parameter):
        lst_param_name = dic_parameter.keys()
        lst_parameter = []

        # パラメータ毎の取り得る値を設定
        for str_param_name in lst_param_name:
            lst_parameter.append(str_param_name + '=' + dic_parameter[str_param_name])

        return lst_parameter

    # パラメータ内容を最新情報にUpdate
    def update_post_parameter(self, obj_db_control, lst_child_row):
        # 対象ページへのアクセスをスキップする為のフラグ
        bol_skip_flag = False

        # 親ページのレスポンスから最新のパラメータ値を取得
        str_sql = "SELECT response_raw FROM UrlTreeTBL" \
                  " WHERE site_id = 1 AND page_no = ?"
        lst_parent_no = [int(lst_child_row[6])]
        obj_cursor = obj_db_control.select(str_sql, lst_parent_no)
        lst_parent_row = obj_cursor.fetchone()

        # 最新のパラメータ値を取得(method, path, params, response_rawを渡す)
        obj_parser = HtmlParser()
        str_new_params = obj_parser.get_new_parameter_values(lst_child_row[8], lst_child_row[12],
                                                             lst_child_row[13], lst_parent_row[0])

        # 対象がログイン処理の場合、認証情報の有無を確認する。
        lst_all_row_login = []
        if lst_child_row[3] == 1:
            str_sql_login = "SELECT * FROM CredentialsTBL WHERE site_id = 1"
            obj_cursor_login = obj_db_control.select(str_sql_login)
            lst_all_row_login = obj_cursor_login.fetchall()

            # 認証情報が存在する場合、ログイン処理パラメータに認証情報を設定する。
            if len(lst_all_row_login) != 0:
                str_new_params = self.decide_set_credentials(str_new_params, lst_all_row_login[0], lst_child_row[22])
            else:
                # UrlTreeTBLをUpdate(ログイン処理のアクセス優先度を下げる(accessed=2))
                str_sql = "UPDATE UrlTreeTBL SET" \
                          " accessed = 2" \
                          " WHERE id = ?;"
                lst_value = [lst_child_row[0]]
                obj_db_control.update(str_sql, lst_value)
                bol_skip_flag = True

        # 最新のパラメータ値に更新
        str_sql = "UPDATE UrlTreeTBL SET" \
                  " param = ?" \
                  " WHERE id = ?;"
        lst_parent_id = [str_new_params, lst_child_row[0]]
        obj_db_control.update(str_sql, lst_parent_id)

        # パラメータ値の取得先がselectの場合、ランダム取得した一つのoption valueをパラメータに設定する。
        if "select" in lst_child_row[21]:
            lst_params = str_new_params.split('&')
            str_new_params = ''
            str_temp_params = ''
            for str_each_param in lst_params:
                lst_param = str_each_param.split('=')
                if "|+|" in lst_param[1]:
                    lst_select_values = lst_param[1].split("|+|")
                    int_idx = random.randint(0, len(lst_select_values)-1)
                    str_value = lst_select_values[int_idx]
                    str_temp_params = str_temp_params + '&' + lst_param[0] + '=' + str_value
                else:
                    str_temp_params = str_temp_params + '&' + lst_param[0] + '=' + lst_param[1]

            # selectを含むパラメータを更新
            str_new_params = str_temp_params[1:]

        # requests用にパラメータ形式を辞書に変換
        return self.change_string_to_dictionary(str_new_params), bol_skip_flag

    # UrlTreeTBLのレコードからアクセス先URLを組み立てる
    def assemble_url(self, lst_row):
        return lst_row[9].encode() + "://" + lst_row[10].encode() + ":" + str(lst_row[11]) + lst_row[12].encode()

    # ページの重複チェック
    def check_target_match(self, obj_db_control, str_method, str_path, str_param, str_enc_type):
        str_sql = "SELECT method, path, param, enc_type FROM UrlTreeTBL WHERE site_id = 1 ORDER BY page_no ASC"
        obj_cursor = obj_db_control.select(str_sql)
        lst_all_row = obj_cursor.fetchall()

        # 重複チェック
        bol_path_match_flag = False
        bol_param_match_flag = False
        lst_path_temp = str_path.split('?')
        lst_post_params = str_param.split('&')
        for lst_row in lst_all_row:
            lst_row_temp = lst_row[1].split('?')
            # Pathが一致している場合
            if lst_path_temp[0] == lst_row_temp[0]:
                lst_get_params = []
                # GETパラメータが存在する場合
                if len(lst_path_temp) == 2:
                    lst_get_params = lst_path_temp[1].split('&')
                else:
                    # 比較先(TBLデータ)にGETパラメータが存在しない場合
                    if len(lst_row_temp) == 1:
                        if str_method == lst_row[0]:
                            # 重複と判定
                            bol_path_match_flag = True

                int_match_count = 0
                lst_row_get_params = []
                # GETパラメータの重複チェック
                for str_get_param in lst_get_params:
                    lst_get_param_temp = str_get_param.split('=')
                    lst_row_get_params = []
                    if len(lst_row_temp) == 2:
                        lst_row_get_params = lst_row_temp[1].split('&')
                        for str_row_get_param in lst_row_get_params:
                            lst_row_param_temp = str_row_get_param.split('=')

                            # パラメータ名が一致している場合
                            if lst_get_param_temp[0] == lst_row_param_temp[0]:
                                # 一致件数をカウント
                                int_match_count += 1

                # パラメータ構成が一致している場合
                if int_match_count == len(lst_row_get_params):
                    # メソッドも一致している場合
                    if str_method == lst_row[0]:
                        # 重複と判定
                        bol_path_match_flag = True

                # Param(POSTパラメータ)の重複チェック
                int_match_count = 0
                for str_post_param in lst_post_params:
                    lst_post_param_temp = str_post_param.split('=')
                    lst_row_post_params = lst_row[2].split('&')
                    for str_row_post_param in lst_row_post_params:
                        lst_row_param_temp = str_row_post_param.split('=')

                        # パラメータ名が一致している場合
                        if lst_post_param_temp[0] == lst_row_param_temp[0]:
                            # 一致件数をカウント
                            int_match_count += 1

                    # POSTパラメータ数が異なる場合
                    if len(lst_post_params) != len(lst_row_post_params):
                        bol_param_match_flag = False
                    # POSTパラメータが存在しない場合
                    elif len(lst_post_params) == 1:
                        if str_method == lst_row[0]:
                            bol_param_match_flag = True
                    # POSTパラメータ構成が一致する場合
                    elif int_match_count == len(lst_row_post_params):
                        if str_method == lst_row[0] and str_enc_type == lst_row[3]:
                            bol_param_match_flag = True
                    else:
                        bol_param_match_flag = False

            # Path、POSTパラメータ共に一致している場合
            if bol_path_match_flag and bol_param_match_flag:
                return True

        # 一致する画面が存在しない場合
        return False

    # POSTパラメータをファイルと通常のデータに分割する
    def divide_params(self, str_param_types, dic_post_params, str_dummy_file_path):
        lst_param_types = str_param_types.split(',')
        dic_file_param = OrderedDict()
        dic_data_param = OrderedDict()

        # パラメータ毎の取り得る値を設定
        int_idx = 0
        for str_key, str_value in dic_post_params.items():
            if lst_param_types[int_idx].lower() == "file":
                dic_file_param[str_key] = open(str_dummy_file_path, 'rb')
            else:
                dic_data_param[str_key] = str_value
            int_idx += 1

        return dic_file_param, dic_data_param
