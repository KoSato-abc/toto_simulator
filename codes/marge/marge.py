import numpy as np
import pandas as pd
import datetime
import re
import codes.common as c

class marge():
    
    def __init__(self):
        self.common = c.common()
        self.common.PY_NAME = 'marge'
        
    def marge_csv(self):
        self.common.write_log(msg = 'marge_for_train.csv作成')
        df = self.make_marge_csv_for_train()
        self.common.write_log(msg = 'marge_for_test.csv作成')
        self.make_marge_csv_for_test(df)
        self.common.write_log(msg = 'toto_info.csv作成')
        self.make_toto_info_csv()

    def make_marge_csv_for_train(self):
        # 読み込み
        df_starting_member = pd.read_csv('data/scraping/j_league_data_site/j_starting_member_cleaned.csv', index_col=0)
        df_rank_table = pd.read_csv('data/scraping/j_league_data_site/j_rank_table_cleaned.csv', index_col=0)
        df_schedule = pd.read_csv('data/scraping/j_league_data_site/j_match_schedule_cleaned.csv', index_col=0)
        # 2012年〜現在のデータを抽出
        df_starting_member = df_starting_member[df_starting_member['年月日']>20120000]
        df_schedule = df_schedule[df_schedule['年月日'] != '未定'].astype({'年月日': int})
        df_schedule = df_schedule[df_schedule['年月日']>20120000]
        #  中止の試合を削除
        df_schedule = df_schedule[df_schedule['スコア'] != '中止']
        df_schedule = df_schedule.sort_values('年月日', ascending= False).reset_index(drop = True)

        # スコアを整理
        df_schedule_future = df_schedule[df_schedule['スコア'] == '未実施'].reset_index(drop = True)
        df_schedule_past = df_schedule[df_schedule['スコア'] != '未実施'].reset_index(drop = True)
        df_schedule_past['スコア'] = df_schedule_past['スコア'].apply(lambda x : re.findall('(\d*-\d*)', x)[0])

        h_goals, a_goals, goal_deffs = [], [], []
        for i, row in df_schedule_past.iterrows():
            h_goal = row['スコア'].split('-')[0]
            a_goal = row['スコア'].split('-')[1]
            h_goals += [h_goal]
            a_goals += [a_goal]
            goal_deffs += [int(h_goal) - int(a_goal)]
        df_tmp1 = pd.DataFrame(h_goals, columns = ['y_H_goal'])
        df_tmp2 = pd.DataFrame(a_goals, columns = ['y_A_goal'])
        df_tmp3 = pd.DataFrame(goal_deffs, columns = ['y_goal_deff'])
        df_schedule_past = pd.concat([df_schedule_past, df_tmp1, df_tmp2, df_tmp3],axis=1)

        df_schedule_past.loc[df_schedule_past['y_H_goal'] == df_schedule_past['y_A_goal'], 'y_even_flg'] = 1
        df_schedule_past.loc[df_schedule_past['y_H_goal'] != df_schedule_past['y_A_goal'], 'y_even_flg'] = 0
        df_schedule_past.loc[df_schedule_past['y_H_goal'] == df_schedule_past['y_A_goal'], 'y_H_result'] = 0
        df_schedule_past.loc[df_schedule_past['y_H_goal'] > df_schedule_past['y_A_goal'], 'y_H_result'] = 1
        df_schedule_past.loc[df_schedule_past['y_H_goal'] < df_schedule_past['y_A_goal'], 'y_H_result'] = 2

        df_schedule = pd.concat([df_schedule_past, df_schedule_future]).reset_index(drop = True)
        df_schedule.drop(columns = ['スコア'], inplace = True)

        # カラム「rest_days」を作成
        H_A_rest_days = []
        for head in ['H_', 'A_']:
            rest_days = []
            for i, row in df_schedule.iterrows():
                team = row[head + 'team']
                match_day = row['年月日']
                try:
                    past_match_day = df_schedule[((df_schedule['H_team']==team)|(df_schedule['A_team']==team)) &(df_schedule['年月日']<match_day) ].iloc[:1]['年月日'].values[0]
                    past_match_day = str(past_match_day)
                    match_day = str(match_day)

                    dt1 = datetime.datetime(year=int(match_day[:4]), month=int(match_day[4:6]), day=int(match_day[6:8]))
                    dt2 = datetime.datetime(year=int(past_match_day[:4]), month=int(past_match_day[4:6]), day=int(past_match_day[6:8]))
                    dt = dt1 - dt2
                    rest_days += [dt.days]
                except IndexError:
                    rest_days += [5]
            H_A_rest_days += [rest_days]
        df_schedule = df_schedule.assign(H_rest_days = H_A_rest_days[0], A_rest_days = H_A_rest_days[1] )

        # df_scheduleからJリーグの試合だけ抽出
        df_schedule = df_schedule[(df_schedule['カテゴリ'] == 'J1')|(df_schedule['カテゴリ'] == 'J2')|(df_schedule['カテゴリ'] == 'J3')]

        # df_scheduleとdf_starting_memberをマージ
        df_marge = pd.merge(df_schedule, df_starting_member, on=['年月日', 'H_team', 'A_team'], how='left')

        # df_marge にyearを追加
        year_list = []
        for i, row in df_marge.iterrows():
            year = str(row["年月日"])[:4]
            year_list += [int(year)]
        df_marge = df_marge.assign(year = year_list)
        df_marge['節'] = df_marge['節'].astype(int)

        # df_rank_tableをdf_rank_table_Hとdf_rank_table_Aにコピー
        df_rank_columns_H = df_rank_table.columns.values.copy()
        for i, col in enumerate(df_rank_columns_H):
            df_rank_columns_H[i] =  "H_" + col
        df_rank_table_H = df_rank_table.set_axis(df_rank_columns_H, axis='columns').copy()

        df_rank_columns_A = df_rank_table.columns.values.copy()
        for i, col in enumerate(df_rank_columns_A):
            df_rank_columns_A[i] =  "A_" + col
        df_rank_table_A = df_rank_table.set_axis(df_rank_columns_A, axis='columns').copy()

        # df_margeとdf_rank_table_Hをマージ
        df_marge = pd.merge(df_marge, df_rank_table_H, 
                 left_on=['year', '節', 'H_team'],
                 right_on=['H_年度', 'H_節', 'H_チーム'], how='left').drop(columns=['H_年度', 'H_節', 'H_チーム'])

        # df_margeとdf_rank_table_Aをマージ
        df_marge = pd.merge(df_marge, df_rank_table_A, 
                 left_on=['year', '節', 'A_team'],
                 right_on=['A_年度', 'A_節', 'A_チーム'], how='left').drop(columns=['A_年度', 'A_節', 'A_チーム'])

        df_marge.rename(columns={'スタジアム_x': 'スタジアム'}, inplace=True)
        df_marge.drop(columns=['スタジアム_y', '入場者数_x', '入場者数_y', 'インターネット中継・TV放送', 'キックオフ時刻'
                              , '天候', '気温', '湿度', 'year', 'H_カテゴリ', 'A_カテゴリ'], inplace=True)

        # インデックスの振り直し
        df_marge.reset_index(drop = True)
        
        return df_marge
    
    def make_marge_csv_for_test(self, df):
        
        df_marge_for_train = df.reset_index(drop = True).copy()

        # df_tmp作成
        df_tmp1 = df_marge_for_train[['年月日', 'H_team', 'H_監督', 'H_ポジション1', 'H_選手1', 'H_ポジション2', 'H_選手2', 'H_ポジション3', 'H_選手3', 'H_ポジション4', 'H_選手4', 'H_ポジション5', 'H_選手5', 'H_ポジション6', 'H_選手6', 'H_ポジション7', 'H_選手7', 'H_ポジション8', 'H_選手8', 'H_ポジション9', 'H_選手9', 'H_ポジション10', 'H_選手10', 'H_ポジション11', 'H_選手11']]
        df_tmp1.rename(columns={'H_team': 'team', 'H_監督': '監督', 'H_ポジション1': 'ポジション1', 'H_選手1': '選手1', 'H_ポジション2': 'ポジション2', 'H_選手2': '選手2', 'H_ポジション3': 'ポジション3', 'H_選手3': '選手3', 'H_ポジション4': 'ポジション4', 'H_選手4': '選手4', 'H_ポジション5': 'ポジション5', 'H_選手5': '選手5', 'H_ポジション6': 'ポジション6', 'H_選手6': '選手6', 'H_ポジション7': 'ポジション7', 'H_選手7': '選手7', 'H_ポジション8': 'ポジション8', 'H_選手8': '選手8', 'H_ポジション9': 'ポジション9', 'H_選手9': '選手9', 'H_ポジション10': 'ポジション10', 'H_選手10': '選手10', 'H_ポジション11': 'ポジション11', 'H_選手11': '選手11'}, inplace=True)
        df_tmp2 = df_marge_for_train[['年月日', 'A_team', 'A_監督', 'A_ポジション1', 'A_選手1', 'A_ポジション2', 'A_選手2', 'A_ポジション3', 'A_選手3', 'A_ポジション4', 'A_選手4', 'A_ポジション5', 'A_選手5', 'A_ポジション6', 'A_選手6', 'A_ポジション7', 'A_選手7', 'A_ポジション8', 'A_選手8', 'A_ポジション9', 'A_選手9', 'A_ポジション10', 'A_選手10', 'A_ポジション11', 'A_選手11']]
        df_tmp2.rename(columns={'A_team': 'team', 'A_監督': '監督', 'A_ポジション1': 'ポジション1', 'A_選手1': '選手1', 'A_ポジション2': 'ポジション2', 'A_選手2': '選手2', 'A_ポジション3': 'ポジション3', 'A_選手3': '選手3', 'A_ポジション4': 'ポジション4', 'A_選手4': '選手4', 'A_ポジション5': 'ポジション5', 'A_選手5': '選手5', 'A_ポジション6': 'ポジション6', 'A_選手6': '選手6', 'A_ポジション7': 'ポジション7', 'A_選手7': '選手7', 'A_ポジション8': 'ポジション8', 'A_選手8': '選手8', 'A_ポジション9': 'ポジション9', 'A_選手9': '選手9', 'A_ポジション10': 'ポジション10', 'A_選手10': '選手10', 'A_ポジション11': 'ポジション11', 'A_選手11': '選手11'}, inplace=True)
        df_tmp = pd.concat([df_tmp1, df_tmp2]).sort_values(['年月日'], ascending=False).reset_index(drop = True)

        # テストデータのスタメン、監督を直前の試合と同じだと仮定してテスト用データ作成
        re_val_cols = ['監督', 'ポジション1', '選手1', 'ポジション2', '選手2', 'ポジション3', '選手3', 'ポジション4', '選手4', 'ポジション5', '選手5', 'ポジション6', '選手6', 'ポジション7', '選手7', 'ポジション8', '選手8', 'ポジション9', '選手9', 'ポジション10', '選手10', 'ポジション11', '選手11']
        df_marge_for_test = None
        for i, row in df_marge_for_train.iterrows():
            past_row_H = df_tmp[(df_tmp['team'] == row['H_team'])&(df_tmp['年月日'] < row['年月日'])][:1]
            past_row_A = df_tmp[(df_tmp['team'] == row['A_team'])&(df_tmp['年月日'] < row['年月日'])][:1]
            if past_row_H.shape[0] == 1:
                for col in re_val_cols:
                    row['H_' + col] = past_row_H[col].values[0]
            if past_row_A.shape[0] == 1:
                for col in re_val_cols:
                    row['A_' + col] = past_row_A[col].values[0]
            df_marge_for_test = pd.concat([df_marge_for_test, pd.DataFrame(row).T])

        df_marge_for_test.drop(columns = ['y_H_goal', 'y_A_goal', 'y_goal_deff', 'y_even_flg', 'y_H_result'], inplace = True)
        df_marge_for_test.dropna(how='any', inplace = True)
        df_marge_for_train.dropna(how='any', inplace = True)
        df_marge_for_test['train_test'] = 'test'
        df_marge_for_train['train_test'] = 'train'
        df_marge_for_test = df_marge_for_test.reset_index(drop = True)
        df_marge_for_train = df_marge_for_train.reset_index(drop = True)

        df_marge_for_train.to_csv("data/marge/marge_for_train.csv")
        df_marge_for_test.to_csv("data/marge/marge_for_test.csv")
        
    def make_toto_info_csv(self):
        df = pd.read_csv('data/scraping/toto/toto_info_cleaned.csv', index_col=0).reset_index(drop = True).copy()
        # チーム名の統一
        df = self.common.rename_team(df, 'ホーム')
        df = self.common.rename_team(df, 'アウェイ')

        drop_n_list = []
        drop_kind_list = []
        for i, row in df.iterrows():
            has_h = False
            has_a = False
            for i, team_list in enumerate(self.common.M_TEAM_NAMES):
                if row['ホーム'] in team_list:
                    has_h = True
                if row['アウェイ'] in team_list:
                    has_a = True
            if has_a and has_h:
                pass
            else:
                drop_n_list += [row['第n回']]
                drop_kind_list += [row['種別']]
        for i in range(len(drop_n_list)):
            df = df[(df['第n回'] != drop_n_list[i]) | (df['種別'] != drop_kind_list[i])].copy()

        df = df.reset_index(drop = True)
        df.to_csv("data/marge/toto_info.csv")