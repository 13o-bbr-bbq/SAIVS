#!/usr/bin/python
#coding:utf-8
import lxml.html
import re
from bs4 import BeautifulSoup


# 受信したレスポンスの解析(遷移先URLの抽出)
class HtmlParser:

    def __init__(self):
        return

    # aタグのhref要素の取得
    def get_a_tags(self, str_protocol, int_Port, str_fqdn, str_path, str_response):
        # 診断対象のFQDN
        str_target_url_full = str_protocol + "://" + str_fqdn + ":" + int_Port + str_path
        str_target_url = str_protocol + "://" + str_fqdn + str_path

        obj_bs4 = BeautifulSoup(str_response)
        obj_next_url = obj_bs4.find_all("a")
        int_idx = 0
        lst_tags = []
        while int_idx < len(obj_next_url):
            str_href = obj_next_url[int_idx].get("href")
            if str_href is None:
                int_idx += 1
                continue

            # 診断対象の絶対パスが含まれている場合はリストに相対パスを追加
            if (str_target_url_full in str_href) or (str_target_url in str_href):
                int_len = len(str_target_url_full)
                lst_tags.append(str_href[int_len:])
            # 診断対象以外の絶対パスが含まれている場合はリストに追加しない
            elif ("http://" in str_href) or ("https://" in str_href):
                print("not target :" + str_href)
            # プロトコルがhttpまたはhttps以外の場合はリストに追加しない
            elif (str_href.find(':') > 0) or (str_href.find('@') > 0):
                print("not target :" + str_href)
            elif str_href == '':
                print("not target : /")
            # href要素が上記以外(対象の相対パス)はリストに追加(アンカー以外)
            else:
                if str_href.startswith('#') is False:
                    lst_tags.append(str_href)
            int_idx += 1

        return lst_tags

    # formタグ内のinputタグからname属性を取得する
    def get_input_tags(self, obj_element):
        # inputタグからnameとvalueのセットを取得する
        int_idx = 0
        bol_initial = True
        str_param = ''
        obj_input_element = obj_element.find_all('input')
        while int_idx < len(obj_input_element):
            str_name = obj_input_element[int_idx].get('name')
            str_value = obj_input_element[int_idx].get('value')
            if str_name is not None:
                if str_value is not None:
                    if bol_initial is True:
                        str_param = str_name + '=' + str_value
                    else:
                        str_param = str_param + '&' + str_name + '=' + str_value
                else:
                    if bol_initial is True:
                        str_param = str_name + '='
                    else:
                        str_param = str_param + '&' + str_name + '='

                bol_initial = False
            int_idx += 1

        return str_param

    # formタグ内のselectタグからname属性とoption value属性を取得する
    def get_select_tags(self, obj_element):
        # selectタグからname、option valueのセットを取得
        int_idx = 0
        str_param = ''
        str_value = ''
        bol_initial = True
        obj_select_element = obj_element.find_all('select')
        while int_idx < len(obj_select_element):
            # パラメータのname
            str_name = obj_select_element[int_idx].get('name')

            # optionタグからvalueを根こそぎ取得
            int_idx2 = 0
            obj_option_element = obj_select_element[int_idx].find_all('option')
            while int_idx2 < len(obj_option_element):
                # optionタグのvalue
                str_option_value = obj_option_element[int_idx2].get('value')
                if str_option_value is not None:
                    str_value = str_value + "|+|" + str_option_value
                int_idx2 += 1

            if str_name is not None:
                if str_value is not None:
                    if bol_initial is True:
                        str_param = str_name + '=' + str_value
                    else:
                        str_param = str_param + '&' + str_name + '=' + str_value
                else:
                    if bol_initial is True:
                        str_param = str_name + '='
                    else:
                        str_param = str_param + '&' + str_name + '='

                bol_initial = False
            int_idx += 1

        return str_param

    # formタグのmethod要素・action要素・enctype要素、inputタグ・selectタグのname要素を根こそぎ取得
    def get_form_tags(self, str_protocol, str_fqdn, int_port, str_path, obj_response):
        obj_bs4 = BeautifulSoup(obj_response)
        obj_form_element = obj_bs4.find_all("form")

        # ページ種別判定用のテキストを取得（hタグ）
        lst_page_type_text = []
        int_idx = 0
        obj_h_element = obj_bs4.find_all(re.compile("^h[1-6]"))
        while int_idx < len(obj_h_element):
            str_temp = obj_h_element[int_idx].text.lower()
            str_temp = str_temp.replace('!', '')
            str_temp = str_temp.replace('@', '')
            str_temp = str_temp.replace('.', '')
            str_temp = str_temp.replace(':', '')
            str_temp = str_temp.replace(' ', '')
            lst_page_type_text.append(str_temp)
            int_idx += 1

        int_idx = 0
        lst_url_list = []
        str_param_label = ''
        lst_param_feature_temp = []
        lst_param_feature_raw = []
        while int_idx < len(obj_form_element):
            # method要素・action要素・enctype要素の取得
            str_method = obj_form_element[int_idx].get('method')
            str_raw_url = obj_form_element[int_idx].get('action')
            str_enc_type = obj_form_element[int_idx].get('enctype')
            bol_flag = True

            # ページ種別判定用、パラメータの特徴決定用のテキストを取得（formタグ）
            lst_temp_text = obj_form_element[int_idx].text.split('\n')
            for str_text in lst_temp_text:
                str_text = str_text.replace(' ', '')
                if str_text != '':
                    lst_param_feature_raw.append(str_text)

            # ラベル以外の文字列の排除
            lst_form_contents = obj_form_element[int_idx].contents
            int_idx_raw = 0
            str_form_contents = ''
            while int_idx_raw < len(lst_form_contents):
                str_form_contents += lst_form_contents[int_idx_raw].encode()
                int_idx_raw += 1
            str_form_contents = str_form_contents.replace(' ', '')
            str_form_contents = str_form_contents.replace('\n', '')
            int_idx_raw = 0
            int_start_idx = 0
            int_end_idx = 0
            while int_idx_raw < len(lst_param_feature_raw):
                int_start_idx = str_form_contents.find(lst_param_feature_raw[int_idx_raw])
                if (int_idx_raw + 1) == len(lst_param_feature_raw):
                    int_end_idx = len(str_form_contents)
                else:
                    int_end_idx = str_form_contents.find(lst_param_feature_raw[int_idx_raw + 1])

                if '<input' not in str_form_contents[int_start_idx:int_end_idx] and \
                    '<select' not in str_form_contents[int_start_idx:int_end_idx] and \
                    'textarea' not in str_form_contents[int_start_idx:int_end_idx]:
                    del lst_param_feature_raw[int_idx_raw]
                    int_idx_raw -= 1
                int_idx_raw += 1

            for str_text in lst_param_feature_raw:
                str_text = str_text.lower()
                str_text = str_text.replace('!', '')
                str_text = str_text.replace('@', '')
                str_text = str_text.replace('.', '')
                str_text = str_text.replace(':', '')
                if str_text != '':
                    lst_page_type_text.append(str_text)
                    lst_param_feature_temp.append(str_text)

            # inputタグ、selectタグ、textareaタグからname、value(option value)、typeのセットを取得
            int_idx2 = 0
            str_param = ''
            str_types = ''
            obj_input_element = obj_form_element[int_idx].find_all(["input", "select", "textarea"])
            while int_idx2 < len(obj_input_element):
                # inputタグの場合
                if obj_input_element[int_idx2].name.lower() == "input":
                    # パラメータのname、value
                    str_name = obj_input_element[int_idx2].get('name')
                    str_value = obj_input_element[int_idx2].get('value')
                    if str_value is None:
                        str_value = ''

                    # nameとvalueのセットを保存
                    if str_name is not None:
                        str_param = str_param + '&' + str_name + '=' + str_value

                        # パラメータのtype
                        str_type = obj_input_element[int_idx2].get('type')
                        str_types = str_types + ',' + str_type

                # selectタグの場合
                if obj_input_element[int_idx2].name.lower() == "select":
                    # name、option valueのセットを取得
                    str_name = obj_input_element[int_idx2].get('name')
                    str_value = ''

                    # optionタグからvalueを根こそぎ取得
                    int_idx3 = 0
                    obj_option_element = obj_input_element[int_idx2].find_all('option')
                    while int_idx3 < len(obj_option_element):
                        # optionタグのvalue
                        str_option_value = obj_option_element[int_idx3].get('value')
                        if str_option_value is not None:
                            str_value = str_value + "|+|" + str_option_value
                        int_idx3 += 1

                    if str_name is not None:
                        str_param = str_param + '&' + str_name + '=' + str_value

                        # パラメータのtype("select"固定)
                        str_types = str_types + ',' + "select"

                # textareaタグの場合
                if obj_input_element[int_idx2].name.lower() == "textarea":
                    # パラメータのname
                    str_name = obj_input_element[int_idx2].get('name')
                    str_value = obj_input_element[int_idx2].get('value')
                    if str_value is None:
                        str_value = ''

                    # nameとvalueのセットを保存
                    if str_name is not None:
                        str_param = str_param + '&' + str_name + '=' + str_value

                        # パラメータのtype
                        str_type = obj_input_element[int_idx2].get('type')
                        if str_type is None:
                            str_type = 'none'
                        str_types = str_types + ',' + str_type

                int_idx2 += 1
            int_idx += 1

            # 入力フォームのラベルを設定
            lst_param_types = str_types[1:].split(',')
            int_idx4 = 0
            for str_param_type in lst_param_types:
                if str_param_type.lower() == "text" or str_param_type.lower() == "password":
                    str_param_label = str_param_label + ',' + lst_param_feature_temp[int_idx4]
                    int_idx4 += 1
                elif str_param_type.lower() == "checkbox" or str_param_type.lower() == "radio" or str_param_type.lower() == "file":
                    str_param_label = str_param_label + ',' + '@'
                    int_idx4 += 1
                else:
                    str_param_label = str_param_label + ',' + '@'

            # action要素に対象の絶対パス(プロトコル＋FQDN＋ポート番号(省略も有り))が含まれている場合はリストに追加
            if (str_protocol + str_fqdn + int_port + str_path in str_raw_url)\
                    or (str_protocol + str_fqdn + str_path in str_raw_url):
                bol_flag = True

            # action要素に対象以外の絶対パスが含まれている場合はリストに追加しない
            elif ("http://" in str_raw_url) or ("https://" in str_raw_url):
                bol_flag = False

            # action要素が上記以外(対象の相対パス)はリストに追加
            else:
                if str_raw_url != '#':
                    bol_flag = True

            # タプルに一つのformタグに関連する情報を格納
            if bol_flag is True:
                tpl_form_info = (str_method,
                                 str_raw_url,
                                 str_enc_type,
                                 str_param[1:],
                                 obj_response.encode('utf_8'),
                                 str_types[1:])
                lst_url_list.append(tpl_form_info)

        if len(lst_url_list) != 0:
            return lst_url_list, lst_page_type_text, str_param_label[1:]
        else:
            return lst_url_list, lst_page_type_text, str_param_label

    # titleタグの文字列を取得
    def get_title_tag(self, obj_response):
        obj_bs4 = BeautifulSoup(obj_response.text)
        obj_title_element = obj_bs4.find_all("title")
        str_title = obj_title_element.text

        return str_title

    # 全てのタグ文字列を取得
    def get_all_tag(self, obj_diff_string):
        obj_root = lxml.html.fromstring(obj_diff_string)

        # rootからtitleタグの文字列を取得
        lst_diff_value = []
        for str_value in obj_root.xpath('//'):
            lst_diff_value.append(str_value)

        return lst_diff_value

    # 対象と一致するformタグの要素から、最新のパラメータ値を取得
    def get_new_parameter_values(self, str_method, str_path, str_params, str_parent_response):
        obj_bs4 = BeautifulSoup(str_parent_response)
        obj_form_element = obj_bs4.find_all("form")

        int_idx = 0
        str_parent_params = ''
        str_return_params = ''
        while int_idx < len(obj_form_element):
            str_parent_method = obj_form_element[int_idx].get('method')
            str_parent_raw_url = obj_form_element[int_idx].get('action')

             # methodとpathの比較
            if str_method.lower() == str_parent_method.lower() and str_path == str_parent_raw_url:
                str_parent_params = self.get_input_tags(obj_form_element[int_idx])
                str_parent_select_params = self.get_select_tags(obj_form_element[int_idx])
                if str_parent_select_params != '':
                    str_parent_params = str_parent_params + '&' + str_parent_select_params
            else:
                int_idx += 1
                continue

            # パラメータ数の比較
            lst_params = []
            lst_parent_params = []
            if len(str_params.split('&')) == len(str_parent_params.split('&')):
                lst_params = str_params.split('&')
                lst_parent_params = str_parent_params.split('&')
            else:
                int_idx += 1
                continue

            # パラメータ構成の比較
            int_match_count = 0
            for str_param in lst_params:
                lst_param = str_param.split('=')
                for str_parent_param in lst_parent_params:
                    lst_parent_param = str_parent_param.split('=')

                    # パラメータ名が一致している場合、最新の値を取得。
                    if lst_param[0] == lst_parent_param[0]:
                        lst_param[1] = lst_parent_param[1]
                        str_return_params += '&' + lst_param[0] + '=' + lst_param[1]
                        int_match_count += 1

            # パラメータ構成が一致している場合、最新のパラメータ情報を返す。
            if int_match_count == len(str_parent_params.split('&')):
                return str_return_params[1:]

            int_idx += 1

        # 一致するする要素が無い場合は元のパラメータを返す
        return str_params
