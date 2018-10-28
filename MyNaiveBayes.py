#!/usr/bin/python
#coding:utf-8
import os
import sys
import math
import pickle


# NaiveBayesで種々の分類を実行
class Classify():


    def __init__(self):
        # 訓練済みデータを格納するpklファイルパスを定義
        self.bin_nb_okng_body_path = os.path.join('.\\data', 'nb_okng_classify_body.pkl')
        self.bin_nb_page_type_body_path = os.path.join('.\\data', 'nb_page_type_classify_body.pkl')

        # ストップワード辞書のファイルパスを定義
        self.txt_stop_words_list_path = os.path.join('.\\data', 'stop_words.txt')

    # レスポンスデータから遷移の成否を分類
    def classify_flow_okng(self, str_response):
        # 訓練済みデータ(pkl)の読み込み
        if os.path.exists(self.bin_nb_okng_body_path):
            with open(self.bin_nb_okng_body_path, 'rb') as file_read:
                obj_naive_bayes = pickle.load(file_read)
        # 訓練済みのデータ(pkl)がない場合は処理を修了
        else:
            print "PKL File NOT FOUND."
            return ''

        # 分類対象のレスポンスデータを指定し分類を実行
        str_category, int_score = obj_naive_bayes.classify(str_response)
        return str_category, int_score

    # レスポンスデータからページの種類を分類
    def classify_page_type(self, lst_page_type):
        # 訓練済みデータ(pkl)の読み込み
        obj_naive_bayes = None
        if os.path.exists(self.bin_nb_page_type_body_path):
            with open(self.bin_nb_page_type_body_path, 'rb') as file_read:
                obj_naive_bayes = pickle.load(file_read)
        # 訓練済みのデータ(pkl)がない場合は処理を修了
        else:
            print "not found pkl(nb_page_type_classify_body.pkl)."
            return ''

        # 分類対象のtitleタグの値を指定し分類を実行
        str_category, int_score = obj_naive_bayes.classify(lst_page_type)
        return str_category

    # ストップワードを削除
    def remove_stop_words(self, lst_orig_text):
        # ストップワード辞書の読み込み
        if os.path.exists(self.txt_stop_words_list_path):
            with open(self.txt_stop_words_list_path, 'r') as file_read:
                str_read_text = file_read.read()
                lst_stop_words = str_read_text.split('\n')
                file_read.close()

                lst_edited_text = []
                int_idx = 0
                while int_idx < len(lst_orig_text):
                    int_idx2 = 0
                    bol_match_flag = False
                    while int_idx2 < len(lst_stop_words):
                        if lst_orig_text[int_idx] == lst_stop_words[int_idx2]:
                            bol_match_flag = True
                        int_idx2 += 1

                    # オリジナルwordがストップワードに含まれていない場合
                    if bol_match_flag is False:
                        lst_edited_text.append(lst_orig_text[int_idx])
                    int_idx += 1

                return lst_edited_text
        # ストップワード辞書がない場合は処理を修了
        else:
            print "not found stop_words.txt."
            return lst_orig_text


class NaiveBayes:
    def __init__(self):
        self.vocabularies = set()
        self.word_count = {}
        self.category_count = {}

    # カテゴリ単位でカウント(Bag-of-Wordsの作成)
    def word_count_up(self, word, category):
        self.word_count.setdefault(category, {})
        self.word_count[category].setdefault(word, 0)
        self.word_count[category][word] += 1
        self.vocabularies.add(word)

    # カテゴリ数のカウント
    def category_count_up(self, category):
        self.category_count.setdefault(category, 0)
        self.category_count[category] += 1

    # 画面名とカテゴリを基に学習
    def train(self, doc, category):
        #カテゴリ単位でカウントする
        self.word_count_up(doc, category)

        #カテゴリ数をカウントする
        self.category_count_up(category)

    # ベイズ定理における事前確率の計算
    def prior_prob(self, category):
        num_of_categories = sum(self.category_count.values())
        num_of_docs_of_the_category = self.category_count[category]

        return float(num_of_docs_of_the_category) / float(num_of_categories)

    def num_of_appearance(self, word, category):
        if word in self.word_count[category]:
            return self.word_count[category][word]

        return 0

    # ベイズ定理の計算
    def word_prob(self, word, category):
        # ラプラス・スムージング
        numerator = self.num_of_appearance(word, category) + 1
        denominator = sum(self.word_count[category].values()) + len(self.vocabularies)

        prob = float(numerator) / float(denominator)

        return prob

    # 分類対象の文字列が各カテゴリに含まれる確率を計算
    def score(self, tpl_classify_text, category):
        score = math.log(self.prior_prob(category))
        for word in tpl_classify_text:
            score += math.log(self.word_prob(word, category))
        return score

    # 分類の実行
    def classify(self, lst_classify_text):
        best_guessed_category = None
        max_prob_before = -sys.maxsize

        # カテゴリ単位で類似度のスコアを算出
        for category in self.category_count.keys():
            # 予測したい文章
            prob = self.score(tuple(lst_classify_text), category)

            # 予測したい文章を、スコアの最も大きいカテゴリに分類する
            if prob > max_prob_before:
                max_prob_before = prob
                best_guessed_category = category

        # 分類したカテゴリとスコアを返却
        return best_guessed_category, max_prob_before
