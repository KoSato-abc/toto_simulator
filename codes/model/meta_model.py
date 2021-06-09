import numpy as np
import pandas as pd
import codes.common as c
from sklearn.model_selection import train_test_split
import optuna
from sklearn.metrics import mean_squared_error
import pickle
import xgboost as xgb
'''
model : rightGBM
description:試合結果の3値分類（勝分敗）
''' 
class model():
    def __init__(self, x_train, y_train, x_val, y_val, x_test):
        self.common = c.common()
        self.common.PY_NAME = 'meta_model'
        self.y_col = 'y_H_result'
        
        self.x_train, self.x_val, self.x_test = x_train, x_val, x_test
        self.y_train, self.y_val = y_train, y_val
        self.model = None
        self.f_model_name = None
        
    def get_y_pred(self):
        
        self.set_model()
        
        y_pred, y_pred_proba = self.predict()
        
        df_y = pd.concat([pd.DataFrame(y_pred_proba, columns = ['proba_0', 'proba_1', 'proba_2']), pd.DataFrame(y_pred, columns = ['pred'])], axis = 1)
        
        return df_y
        
    def predict(self):
        dtest = xgb.DMatrix(self.x_test)
        y_pred_proba = self.model.predict(dtest)
        y_pred = np.argmax(y_pred_proba, axis=1)
        return y_pred, y_pred_proba
    
    def set_model(self):
        year = str(self.x_test[:1]['年月日'].values[0])[:4]
        self.f_model_name = 'data/model/meta_model/model_for_' + year +'.sav'
        try:
            self.model = pickle.load(open(self.f_model_name, 'rb'))
        except:
            self.fit()
            
    def fit(self):
        self.dtrain = xgb.DMatrix(self.x_train, label=self.y_train)
        dval = xgb.DMatrix(self.x_val, label=self.y_val)
        study = optuna.create_study()
        study.optimize(self.objective, n_trials=100)#50)
        
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
        y_pred_proba = self.model.predict(dval)
        y_pred = np.argmax(y_pred_proba, axis=1)
        accuracy = sum(self.y_val == y_pred) / len(self.y_val)
        print('accuracy:', accuracy)
        
    def objective(self, trial):
        self.params = {
            "silent": 1,
            "max_depth": trial.suggest_int("max_depth", 1, 9),
            "min_child_weight": 1,
            "eta": trial.suggest_loguniform("eta", 0.01, 1.0),
            "tree_method": "exact",
            "objective": "multi:softprob",
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