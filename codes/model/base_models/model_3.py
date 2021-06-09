import numpy as np
import pandas as pd
import codes.common as c
from sklearn.model_selection import train_test_split
import optuna.integration.lightgbm as lgb_o
from sklearn.metrics import mean_squared_error
import pickle

'''
model : rightGBM
description:得失点の回帰
''' 
class model():
    def __init__(self):
        self.common = c.common()
        self.common.PY_NAME = 'model_3'
        self.y_col = 'y_goal_deff'
        
        self.x_train, self.x_val, self.x_test = None, None, None
        self.y_train, self.y_val = None, None
        self.model = None
        self.f_model_name = None
        
    def get_y_pred(self):
        
        self.preprocessing()
        
        self.set_model()
        
        y_pred = self.predict()
        
        df_y = pd.DataFrame(y_pred, columns = ['pred_m3'])
        
        return df_y
        
    def predict(self):
        y_pred = self.model.predict(self.x_test, num_iteration=self.model.best_iteration)
        return y_pred
    
    def set_model(self):
        year = str(self.x_test[:1]['年月日'].values[0])[:4]
        self.f_model_name = 'data/model/base_models/model_3/model_for_' + year +'.sav'
        try:
            self.model = pickle.load(open(self.f_model_name, 'rb'))
        except:
            self.fit()
            
    def fit(self):
        lgb_train = lgb_o.Dataset(self.x_train, self.y_train)
        lgb_eval = lgb_o.Dataset(self.x_val, self.y_val) 
        # 学習用パラメータ
        lgbm_params = {
            'objective': 'regression', # 回帰  
            'metric': 'rmse', # rsme(平均二乗誤差の平方根) 
        }
        # 学習
        model = lgb_o.train(lgbm_params,
                        lgb_train,
                        valid_sets=lgb_eval,
                        verbose_eval=200,)
        self.model = model
        # 保存
        pickle.dump(self.model, open(self.f_model_name, 'wb'))
        # rmse の計算
        y_pred = self.model.predict(self.x_val, num_iteration=self.model.best_iteration)
        mse = mean_squared_error(self.y_val, y_pred)
        rmse = np.sqrt(mse)
        print('rmse : ', rmse)

    def preprocessing(self):
        # 読み込み
        df = pd.read_csv("data/model/base_models/preprocessing/preprocessed_1.csv", index_col=0)
        # カテゴリ列処理
        category_columns = ['カテゴリ', 'H_team', 'A_team', 'H_監督', 'A_監督']
        df[category_columns] = df[category_columns].astype('category')
        # 不要な列を削除
        df = self.common.drop_y_col(df, self.y_col)
        # train, val, testに分割
        train = df[df['train_test']=='train'].drop(columns = ['train_test'])
        x_train = train.drop(columns = self.y_col)
        y_train = train[self.y_col]
        self.x_train, self.x_val, self.y_train, self.y_val = train_test_split(x_train, y_train)    
        test = df[df['train_test']=='test'].drop(columns = ['train_test'])
        self.x_test = test.drop(columns = self.y_col)