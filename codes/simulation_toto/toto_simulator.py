import numpy as np
import pandas as pd
import pickle
import codes.model.model_for_toto as m

class toto_simulator():
    
    def __init__(self, toto_n, toto_kind):
        self.toto_n = toto_n
        self.toto_kind = toto_kind
        self.df_toto = None
        self.test_keys = None
        self.df_result = None
        self.ini()
        
    def ini(self):
        self.df_toto = pd.read_csv('data/marge/toto_info.csv', index_col=0)
        self.df_toto = self.df_toto[(self.df_toto['第n回'] == self.toto_n)&(self.df_toto['種別'] == self.toto_kind)].reset_index(drop = True)

        self.test_keys = []
        for i, row in self.df_toto.iterrows():
            self.test_keys += [[row['開催日']] +  [row['ホーム']]]
        
        m.model(self.test_keys).make_result()
        
        df_result = pd.read_csv('data/model/result.csv', index_col=0)
        self.df_result = pd.merge(self.df_toto, df_result, 
                                  left_on = ['開催日', 'ホーム'], 
                                 right_on = ['年月日', 'H_team']).drop(columns = ['年月日', 'H_team'])
        
    def get_result(self):
        df = self.df_result[['第n回', '種別', '開催日', 'ホーム', 'アウェイ', 'pred', 'proba_0', 'proba_1', 'proba_2']]
        df[['proba_0', 'proba_1', 'proba_2']] = df[['proba_0', 'proba_1', 'proba_2']].round(2)
        return df