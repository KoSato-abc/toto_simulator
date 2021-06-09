import numpy as np
import pandas as pd
import codes.common as c
from sklearn.model_selection import train_test_split
import xgboost as xgb
from sklearn.metrics import mean_squared_error
import pickle
import optuna

'''
model : XGboost
description:試合結果の3値分類（勝分敗）
''' 
class model():
    def __init__(self):
        self.common = c.common()
        self.common.PY_NAME = 'model_1'
        self.y_col = 'y_H_result'
        
        self.x_train, self.x_val, self.x_test = None, None, None
        self.y_train, self.y_val = None, None
        self.model = None
        self.f_model_name = None
        
    def get_y_pred(self):
        
        self.preprocessing()
        
        self.set_model()
        
        y_pred = self.predict()
        
        df_y = pd.DataFrame(y_pred, columns = ['pred_m7'])
        
        return df_y
        
    def predict(self):
        dtest = xgb.DMatrix(self.x_test)
        
        y_pred = self.model.predict(dtest)
        return y_pred
    
    def set_model(self):
        year = str(self.x_test[:1]['年月日'].values[0])[:4]
        self.f_model_name = 'data/model/base_models/model_7/model_for_' + year +'.sav'
        try:
            self.model = pickle.load(open(self.f_model_name, 'rb'))
        except:
            self.fit()
            
    def fit(self):
        self.dtrain = xgb.DMatrix(self.x_train, label=self.y_train)
        dval = xgb.DMatrix(self.x_val, label=self.y_val)
        study = optuna.create_study()
        study.optimize(self.objective, n_trials=2)#50)
        
        trial = study.best_trial
        
        self.params["max_depth"] = trial.params["max_depth"]
        self.params["eta"] = trial.params["eta"]

        model = xgb.train(params=self.params,
                  dtrain=self.dtrain,
                  num_boost_round=1000,
                  early_stopping_rounds=5,
                  evals=[(dval, "test")])

        self.model = model
        # 保存
        pickle.dump(self.model, open(self.f_model_name, 'wb'))
        # Accuracy の計算
        y_pred = self.model.predict(dval)
        
        accuracy = sum(self.y_val == y_pred) / len(self.y_val)
        print('accuracy:', accuracy)
        
    def objective(self, trial):
        self.params = {
            "silent": 1,
            "max_depth": trial.suggest_int("max_depth", 1, 9),
            "min_child_weight": 1,
            "eta": trial.suggest_loguniform("eta", 0.01, 1.0),
            "tree_method": "exact",
            "objective": "multi:softmax",
            "num_class": 3,
            "predictor": "cpu_predictor"  
        }
        cv_results = xgb.cv(
            self.params,
            self.dtrain,
            num_boost_round=1000,
            seed=0,
            nfold=5, # CVの分割数
#             metrics={"rmse"},
            early_stopping_rounds=200
        )
        return cv_results["test-merror-mean"].min()

    def preprocessing(self):
        # 読み込み
        df = pd.read_csv("data/model/base_models/preprocessing/preprocessed_1.csv", index_col=0)
        # 目的変数のデータ数を揃える
        train = df[df['train_test']=='train'].drop(columns = ['train_test'])
        train = train.sort_values('年月日', ascending=False)
        train_0 = train[train['y_H_result'] == 0]
        train_1 = train[train['y_H_result'] == 1]
        train_2 = train[train['y_H_result'] == 2]
        n_row_0 = train_0.shape[0]
        n_row_1 = train_1.shape[0]
        n_row_2 = train_2.shape[0]
        n_row = min(n_row_0, n_row_1, n_row_2)
        train = pd.concat([train_0.iloc[:n_row], train_1.iloc[:n_row], train_2.iloc[:n_row]])
        # 不要な列を削除
        train = self.common.drop_y_col(train, self.y_col)
        # train, val, testに分割
        x_train = train.drop(columns = self.y_col)
        y_train = train[self.y_col]
        self.x_train, self.x_val, self.y_train, self.y_val = train_test_split(x_train, y_train, stratify = y_train)
        
        test = df[df['train_test']=='test'].drop(columns = ['train_test'])
        test = self.common.drop_y_col(test, self.y_col)
        self.x_test = test.drop(columns = self.y_col)