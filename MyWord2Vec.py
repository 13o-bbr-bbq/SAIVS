# -*- coding: utf-8 -*-
from gensim.models import word2vec
import os
import logging

MODEL_NAME = 'text8'
DATA_PATH = 'data\\text8'


class Word2Vec:
    def __init__(self, int_count=10):
        self.int_word_count = int_count

    def learn_sentense(self):
        if os.path.exists(MODEL_NAME):
            # print('Using Word2Vec :', MODEL_NAME)
            return
        else:
            print('Learning sentense...')
            logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)
            obj_sentense = word2vec.Text8Corpus(DATA_PATH)
            obj_model = word2vec.Word2Vec(obj_sentense, size=200, min_count=20, window=15)
            obj_model.save(MODEL_NAME)
            return

    def cal_similarity(self, lst_posi, lst_nega, obj_model):
        int_idx = 1
        obj_result = None
        try:
            obj_result = obj_model.most_similar(positive=lst_posi, negative=lst_nega, topn = self.int_word_count)
            print("\nAnalogize the '%s'." % lst_posi[0])
            print("#######################candidate#############################")
            print("No.", "　", "word", "　", "cos distance")
            for r in obj_result:
                print(int_idx,'　', r[0],'　', r[1])
                int_idx += 1
            print("#############################################################")
            return obj_result
        except:
            obj_result = False
            return obj_result

    def get_candidate_word(self, str_target_word):
        self.learn_sentense()
        obj_model = word2vec.Word2Vec.load(MODEL_NAME)
        str_word = str_target_word
        lst_nega = []
        return self.cal_similarity([str_word.encode()], lst_nega, obj_model)