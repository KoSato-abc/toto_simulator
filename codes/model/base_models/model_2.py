import numpy as np
import pandas as pd
import codes.common as c
from sklearn.model_selection import train_test_split
import optuna.integration.lightgbm as lgb_o
from sklearn.metrics import mean_squared_error
import pickle
'''
model : rightGBM
description:試合結果の2値分類（分、その他）
''' 
class model():
    def __init__(self):
        self.common = c.common()
        self.common.PY_NAME = 'model_2'
        self.y_col = 'y_even_flg'
        
        self.x_train, self.x_val, self.x_test = None, None, None
        self.y_train, self.y_val = None, None
        self.model = None
        self.f_model_name = None
        
    def get_y_pred(self):
        
        self.preprocessing()
        
        self.set_model()
        
        y_pred, y_pred_proba = self.predict()
        
        df_y = pd.concat([pd.DataFrame(y_pred_proba, columns = ['proba_0_m2', 'proba_1_m2']), pd.DataFrame(y_pred, columns = ['pred_m2'])], axis = 1)
        
        return df_y
        
    def predict(self):
        y_pred_proba = self.model.predict(self.x_test, num_iteration=self.model.best_iteration)
        y_pred = np.argmax(y_pred_proba, axis=1)
        return y_pred, y_pred_proba
    
    def set_model(self):
        year = str(self.x_test[:1]['年月日'].values[0])[:4]
        self.f_model_name = 'data/model/base_models/model_2/model_for_' + year +'.sav'
        try:
            self.model = pickle.load(open(self.f_model_name, 'rb'))
        except:
            self.fit()
            
    def fit(self):
        lgb_train = lgb_o.Dataset(self.x_train, self.y_train)
        lgb_eval = lgb_o.Dataset(self.x_val, self.y_val) 
        # 学習用パラメータ
        lgbm_params = {
            'objective': 'multiclass',
            'metric': 'multi_logloss',
            'num_class': 2
        }
        # 学習
        model = lgb_o.train(lgbm_params,
                        lgb_train,
                        valid_sets=lgb_eval,
#                         early_stopping_rounds=500,
                        verbose_eval=200,)
        self.model = model
        # 保存
        pickle.dump(self.model, open(self.f_model_name, 'wb'))
        # Accuracy の計算
        y_pred_proba = self.model.predict(self.x_val, num_iteration=self.model.best_iteration)
        y_pred = np.argmax(y_pred_proba, axis=1)
        accuracy = sum(self.y_val == y_pred) / len(self.y_val)
        print('accuracy:', accuracy)


    def preprocessing(self):
        # 読み込み
        df = pd.read_csv("data/model/base_models/preprocessing/preprocessed_1.csv", index_col=0)
        # カテゴリ列処理
        category_columns = ['カテゴリ', 'H_team', 'A_team', 'H_監督', 'A_監督']
        df[category_columns] = df[category_columns].astype('category')
        # 引き分けとその他のデータ数を揃える
        train = df[df['train_test']=='train'].drop(columns = ['train_test'])
        train = train[train['y_goal_deff'] < 2].sort_values('年月日', ascending=False)
        train_0 = train[train['y_H_result'] == 0]
        train_1 = train[train['y_H_result'] == 1]
        train_2 = train[train['y_H_result'] == 2]
        n_row_0 = train_0.shape[0]
        n_row_1 = train_1.shape[0]
        n_row_2 = train_2.shape[0]
        n_row = min(min(n_row_1,n_row_2)*2, n_row_0)
        train = pd.concat([train_0.iloc[:n_row], train_1.iloc[:n_row//2], train_2.iloc[:n_row//2]])
        # 不要な列を削除
        train = self.common.drop_y_col(train, self.y_col)
        # train, val, testに分割
        x_train = train.drop(columns = self.y_col)
        y_train = train[self.y_col]
        self.x_train, self.x_val, self.y_train, self.y_val = train_test_split(x_train, y_train, stratify = y_train)
        
        test = df[df['train_test']=='test'].drop(columns = ['train_test'])
        test = self.common.drop_y_col(test, self.y_col)
        self.x_test = test.drop(columns = self.y_col)