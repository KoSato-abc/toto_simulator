import numpy as np
import pandas as pd
import codes.common as c
from sklearn.model_selection import train_test_split
import xgboost as xgb
import pickle
import optuna
from . import meta_model as mm
from .base_models import preprocessing as p
from .base_models import model_1 as model1
from .base_models import model_2 as model2
from .base_models import model_3 as model3
from .base_models import model_4 as model4
from .base_models import model_5 as model5
from .base_models import model_6 as model6
from .base_models import model_7 as model7
from .base_models import model_8 as model8

class model():
    def __init__(self, test_keys):
        self.common = c.common()
        self.common.PY_NAME = 'model_for_toto'
        self.test_keys = test_keys
        
    def make_result(self):
        self.make_data()
        
        x_train, y_train, x_val, y_val, x_test = self.get_train_test()
        
        meta_model = mm.model(x_train, y_train, x_val, y_val, x_test)
        df_y = meta_model.get_y_pred()
        
        df_result = pd.read_csv('data/model/result.csv', index_col=0)
        df_tmp = pd.DataFrame(self.test_keys, columns = ['年月日', 'H_team'])
        df_tmp = pd.concat([df_tmp, df_y], axis = 1)
        df_result = pd.concat([df_result, df_tmp], axis = 0)
        df_result.drop_duplicates(subset=['年月日', 'H_team'], keep = 'last', inplace = True)
        df_result.to_csv("data/model/result.csv")
        
        self.tmp_def()
        
        return df_y
    
    def tmp_def(self):
        # 一旦閾値により期待値調整
        n1 = 0.025
        n2 = 0.043
        df_result = pd.read_csv('data/model/result.csv', index_col=0)
        df_result['ex'] = df_result['proba_1'] - df_result['proba_2']
        df_result['pred'] = '2'
        df_result.loc[df_result['ex'] < n1 , 'pred'] = '0'
        df_result.loc[df_result['ex'] > n2 , 'pred'] = '1'
        df_result.drop(columns = ['ex'], inplace = True)
        df_result.to_csv("data/model/result.csv")
        
    def get_train_test(self):
        df = pd.read_csv('data/model/data_for_meta.csv', index_col=0)
        df_test = None
        for val in self.test_keys:
            year = str(val[0])[:4]
            df_tmp = df[(df['年月日'] == val[0])&(df['H_team'] == val[1])]
            df_test = pd.concat([df_test, df_tmp])
        df_train = df[df['年月日']< int(year+'0000')]

        drop_col = ['H_team']
        df_train.drop(columns = drop_col, inplace = True)
        df_test.drop(columns = drop_col, inplace = True)
        
        train = df_train.sort_values('年月日', ascending=False)
        train_0 = train[train['y_H_result'] == 0]
        train_1 = train[train['y_H_result'] == 1]
        train_2 = train[train['y_H_result'] == 2]
        n_row_0 = train_0.shape[0]
        n_row_1 = train_1.shape[0]
        n_row_2 = train_2.shape[0]
        n_row = min(n_row_0, n_row_1, n_row_2)
        train = pd.concat([train_0.iloc[:n_row], train_1.iloc[:n_row], train_2.iloc[:n_row]])

        x_train = train.drop(columns = ['y_H_result'])
        y_train = train['y_H_result']
        x_train, x_val, y_train, y_val = train_test_split(x_train, y_train, stratify = y_train)
        x_test = df_test.drop(columns = ['y_H_result'])
        
        return x_train, y_train, x_val, y_val, x_test
    
    def make_data(self):
        preprocessing = p.preprocessing()
        m1 = model1.model()
        m2 = model2.model()
        m3 = model3.model()
        m4 = model4.model()
        m5 = model5.model()
        m6 = model6.model()
        m7 = model7.model()
        m8 = model8.model()

        preprocessing.all_preprocessing(self.test_keys)
        df = pd.DataFrame(self.test_keys, columns = ['年月日', 'H_team'])
        df = pd.concat([df,  m1.get_y_pred()], axis = 1)
        df = pd.concat([df,  m2.get_y_pred()], axis = 1)
        df = pd.concat([df,  m3.get_y_pred()], axis = 1)
        df = pd.concat([df,  m4.get_y_pred()], axis = 1)
        df = pd.concat([df,  m5.get_y_pred()], axis = 1)
        df = pd.concat([df,  m6.get_y_pred()], axis = 1)
        df = pd.concat([df,  m7.get_y_pred()], axis = 1)
        df = pd.concat([df,  m8.get_y_pred()], axis = 1)
        df_tmp = pd.read_csv('data/marge/marge_for_train.csv', index_col=0)[['年月日', 'H_team', 'y_H_result']]
        df = pd.merge(df, df_tmp, how='left')

        df_data_for_meta = pd.read_csv('data/model/data_for_meta.csv', index_col=0)
        df_data_for_meta = pd.concat([df_data_for_meta, df], axis = 0)
        df_data_for_meta.drop_duplicates(subset=['年月日', 'H_team'], keep = 'last', inplace = True)
        df_data_for_meta.to_csv("data/model/data_for_meta.csv")