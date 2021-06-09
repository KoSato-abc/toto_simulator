import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
import codes.common as c

class preprocessing():
    def __init__(self):
        self.common = c.common()
        self.common.PY_NAME = 'preprocessing'
        
    '''
    test_keys
    [[年月日, チーム名]]
    example : [[20210623, '横浜Ｆ・マリノス'], [20210620, '鹿島アントラーズ'], [20210620, '浦和レッズ']]
    '''
    def all_preprocessing(self, test_keys):
        self.common.write_log(msg = '前処理１を実行')
        self.preprocessing1(test_keys)
        
    def preprocessing1(self, test_keys):
        min_date = 99999999
        for date, team in test_keys:
            if date < min_date:
                min_date = date
        columns_x = ['年度', '年月日', 'カテゴリ', '節', 'H_team', 'A_team', 'スタジアム', 'K/O時刻', 'H_rest_days', 'A_rest_days', 'H_監督', 'A_監督', 'H_ポジション1', 'H_選手1', 'H_ポジション2', 'H_選手2', 'H_ポジション3', 'H_選手3', 'H_ポジション4', 'H_選手4', 'H_ポジション5', 'H_選手5', 'H_ポジション6', 'H_選手6', 'H_ポジション7', 'H_選手7', 'H_ポジション8', 'H_選手8', 'H_ポジション9', 'H_選手9', 'H_ポジション10', 'H_選手10', 'H_ポジション11', 'H_選手11', 'A_ポジション1', 'A_選手1', 'A_ポジション2', 'A_選手2', 'A_ポジション3', 'A_選手3', 'A_ポジション4', 'A_選手4', 'A_ポジション5', 'A_選手5', 'A_ポジション6', 'A_選手6', 'A_ポジション7', 'A_選手7', 'A_ポジション8', 'A_選手8', 'A_ポジション9', 'A_選手9', 'A_ポジション10', 'A_選手10', 'A_ポジション11', 'A_選手11', 'H_順位', 'H_勝点', 'H_試合', 'H_勝', 'H_分', 'H_敗', 'H_得点', 'H_失点', 'H_得失点差', 'A_順位', 'A_勝点', 'A_試合', 'A_勝', 'A_分', 'A_敗', 'A_得点', 'A_失点', 'A_得失点差', 'train_test']
        columns_y = ['y_H_goal', 'y_A_goal', 'y_goal_deff', 'y_even_flg', 'y_H_result']
        
        # trainデータ読み込み
        df_train = pd.read_csv('data/marge/marge_for_train.csv', index_col=0)[columns_x + columns_y]
        df_train = df_train[df_train['年月日'] < min_date].reset_index(drop = True)
        # testデータ読み込み
        df_tmp = pd.read_csv('data/marge/marge_for_test.csv', index_col=0)[columns_x]
        df_test = None
        for keys in test_keys:
            df_test = pd.concat([df_test, df_tmp[(df_tmp['年月日'] ==  keys[0])&(df_tmp['H_team'] ==  keys[1])]])
        df_test = df_test.reset_index(drop = True)
        # 結合
        df = pd.concat([df_train, df_test])

        # H_team、A_teamをカウントエンコーディング
        team_list = [df['H_team'].values] + [df['A_team'].values]
        team_names, team_counts = np.unique(team_list, return_counts = True)
        continue_flg = True
        while continue_flg: # カテゴリ型にも対応させるため重複をなくすループ
            for i in range(len(team_counts)):
                if np.count_nonzero(team_counts == team_counts[i]) != 1:
                    team_counts[i] = team_counts[i] + 1
            if np.count_nonzero(1 != np.unique(team_counts, return_counts = True)[1]) ==0:
                continue_flg = False
        df['H_team'] = df['H_team'].apply(lambda x : team_counts[np.where(team_names == x)[0][0]])
        df['A_team'] = df['A_team'].apply(lambda x : team_counts[np.where(team_names == x)[0][0]])

        # H_監督、A_監督をカウントエンコーディング
        coach_list = [df['H_監督'].values] + [df['A_監督'].values]
        coach_names, coach_counts = np.unique(coach_list, return_counts = True)
        continue_flg = True
        while continue_flg: # カテゴリ型にも対応させるため重複をなくすループ
            for i in range(len(coach_counts)):
                if np.count_nonzero(coach_counts == coach_counts[i]) != 1:
                    coach_counts[i] = coach_counts[i] + 1
            if np.count_nonzero(1 != np.unique(coach_counts, return_counts = True)[1]) ==0:
                continue_flg = False
        df['H_監督'] = df['H_監督'].apply(lambda x : coach_counts[np.where(coach_names == x)[0][0]])
        df['A_監督'] = df['A_監督'].apply(lambda x : coach_counts[np.where(coach_names == x)[0][0]])
        
        # カテゴリ列の文字列を削除
        df['カテゴリ'] = df['カテゴリ'].apply(lambda x : x.replace('J', ''))
        # K/O時刻の分を削除
        df['K/O時刻'] = df['K/O時刻'].apply(lambda x : x[:2])
        # ポジション列をまとめる
        h_positions = ['H_ポジション1', 'H_ポジション2', 'H_ポジション3', 'H_ポジション4', 'H_ポジション5', 'H_ポジション6', 'H_ポジション7', 'H_ポジション8', 'H_ポジション9', 'H_ポジション10', 'H_ポジション11']
        a_positions = ['A_ポジション1', 'A_ポジション2', 'A_ポジション3', 'A_ポジション4', 'A_ポジション5', 'A_ポジション6', 'A_ポジション7', 'A_ポジション8', 'A_ポジション9', 'A_ポジション10', 'A_ポジション11']
        df['H_GK'] = (df[h_positions] == 'GK').sum(axis=1)
        df['H_DF'] = (df[h_positions] == 'DF').sum(axis=1)
        df['H_MF'] = (df[h_positions] == 'MF').sum(axis=1)
        df['H_FW'] = (df[h_positions] == 'FW').sum(axis=1)
        df['A_GK'] = (df[a_positions] == 'GK').sum(axis=1)
        df['A_DF'] = (df[a_positions] == 'DF').sum(axis=1)
        df['A_MF'] = (df[a_positions] == 'MF').sum(axis=1)
        df['A_FW'] = (df[a_positions] == 'FW').sum(axis=1)
        # 今年度のトレインデータを削除
        df = df[(df['年度'] < int(str(min_date)[:4]))|(df['train_test'] == 'test')]
        # 不要な列を削除
        player_cols = []
        for head in ['H_', 'A_']:
            for i in range(1, 12):
                player_cols += [head + '選手' + str(i)]
        drop_columns = ['年度', 'スタジアム'] + h_positions + a_positions + player_cols
        df.drop(columns = drop_columns, inplace = True)
        # 欠損値を0埋め(testデータの目的変数)
        df = df.fillna(0)
        # intに変換
        df['train_test'] = df['train_test'].apply(lambda x : x.replace('train', '0'))
        df['train_test'] = df['train_test'].apply(lambda x : x.replace('test', '1'))
        df = df.astype(int)
        df['train_test'] = df['train_test'].apply(lambda x : str(x).replace('0', 'train'))
        df['train_test'] = df['train_test'].apply(lambda x : str(x).replace('1', 'test'))
        # 出力
        df.to_csv("data/model/base_models/preprocessing/preprocessed_1.csv")