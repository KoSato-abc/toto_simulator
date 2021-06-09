import numpy as np
import pandas as pd
import time
import datetime
import urllib.parse
import requests
from bs4 import BeautifulSoup
import re

import codes.common as c

class j_starting_member():
    
    def __init__(self):
        self.common = c.common()
        self.common.PY_NAME = 'j_starting_member'
        self.output_dir = 'data/scraping/j_league_data_site/'
        
    def  scraping(self):
        df_result =  pd.read_csv(self.output_dir+ 'j_starting_member.csv', index_col=0)
        
        columns_1 = ["日付", "キックオフ時刻", "スタジアム", "入場者数", "天候", "気温", "湿度"]
        columns_2 = ["H_team", "H_監督", "H_ポジション1", "H_選手1", "H_ポジション2", "H_選手2", "H_ポジション3", "H_選手3", "H_ポジション4", "H_選手4", "H_ポジション5", "H_選手5", "H_ポジション6", "H_選手6", "H_ポジション7", "H_選手7", "H_ポジション8", "H_選手8", "H_ポジション9", "H_選手9", "H_ポジション10", "H_選手10", "H_ポジション11", "H_選手11"]
        columns_3 = ["A_team", "A_監督", "A_ポジション1", "A_選手1", "A_ポジション2", "A_選手2", "A_ポジション3", "A_選手3", "A_ポジション4", "A_選手4", "A_ポジション5", "A_選手5", "A_ポジション6", "A_選手6", "A_ポジション7", "A_選手7", "A_ポジション8", "A_選手8", "A_ポジション9", "A_選手9", "A_ポジション10", "A_選手10", "A_ポジション11", "A_選手11"]
        columns = columns_1 + columns_2 + columns_3 + ["url"]

        now_year = self.common.get_now_year()
        from_year = now_year
        
        df_result = df_result[df_result['年度'] != now_year]
        match_card_id_list=[]
        for year in range(from_year, now_year+1):
            for frame_id in range(1,4):
                url = 'https://data.j-league.or.jp/SFMS01/search?competition_years='+str(year)+'&competition_frame_ids='+str(frame_id)+'&tv_relay_station_name='
                self.common.sleep()
                self.common.write_log(msg = 'match_card_idの取得:' + str(year) + ' J' + str(frame_id))
                self.common.write_log(msg = url)
                site = requests.get(url)
                soup = BeautifulSoup(site.text, 'html.parser')
                soup = str(soup.find_all('td', class_='al-c nowrap')).split('\n')
                for val in soup:
                    val = re.sub('>.*', '', val)
                    match_card_id = [re.findall("match_card_id=(\d*)", val)][0]
                    if len(match_card_id) == 0:
                        continue
                    match_card_id_list += match_card_id
        count = 0
        for i in match_card_id_list:
            count += 1
            df_tmp = pd.DataFrame(columns = columns, index = [i]).copy()
            url = "https://data.j-league.or.jp/SFMS02/?match_card_id=" + str(i)
            self.common.write_log(msg = "処理中：match_card_id = " + str(i) + '(' + str(count) + '/' + str(len(match_card_id_list)) + ')')
            self.common.write_log(msg = url)
            df_tmp["url"] = url
            getted_h_pleayer = False
            getted_h_coach = False
            self.common.sleep()
            try:
                data = pd.read_html(url)
            except:
                df_result = pd.concat([df_result, df_tmp])
                continue

            for j, i_df in enumerate(data):

                if i_df.shape[0]==0:
                    continue

                if j == 0:
                    df_tmp["H_team"] = i_df.iat[0,0]
                    df_tmp["A_team"] = i_df.iat[0,-1]

                if i_df.iat[0,0] == 'GK' and i_df.shape[0] == 11:
                    if not getted_h_pleayer:
                        H_position_list = i_df.iloc[:11, 0].values
                        H_player_list = i_df.iloc[:11, 2].values
                        getted_h_pleayer = True
                        for k in range(11):
                            df_tmp["H_選手"+str(k+1)] =  H_player_list[k]
                            df_tmp["H_ポジション"+str(k+1)] =  H_position_list[k]
                    else:
                        A_position_list = i_df.iloc[:11, 0].values
                        A_player_list = i_df.iloc[:11, 2].values
                        for k in range(11):
                            df_tmp["A_選手"+str(k+1)] =  A_player_list[k]
                            df_tmp["A_ポジション"+str(k+1)] =  A_position_list[k]

                if i_df.shape == (1,3) and getted_h_pleayer:
                    if not getted_h_coach:
                        df_tmp["H_監督"] = i_df.iat[0,-1]
                        getted_h_coach = True
                    else:
                        df_tmp["A_監督"] = i_df.iat[0,-1]

                if i_df.columns[0] == '日付':
                    df_tmp["日付"] = i_df["日付"].values[0]
                    df_tmp["キックオフ時刻"] = i_df["キックオフ時刻"].values[0]
                    df_tmp["スタジアム"] = i_df["スタジアム"].values[0]
                    df_tmp["入場者数"] = i_df["入場者数"].values[0]
                    df_tmp["天候"] = i_df["天候"].values[0]
                    df_tmp["気温"] = i_df["気温"].values[0]
                    df_tmp["湿度"] = i_df["湿度"].values[0]
            
            df_result = pd.concat([df_result, df_tmp])
        
        yyyy_list = []
        df_result = df_result.reset_index(drop = True)
        for i, row in df_result.iterrows():
            yyyy_list += [row["日付"][:4]]
        df_result = df_result.assign(年度 = yyyy_list)
        df_result.to_csv(self.output_dir + "j_starting_member.csv")
    
    def  clean(self):
        df = pd.read_csv(self.output_dir + 'j_starting_member.csv', index_col=0).dropna()

        yyyyMMdd_list = []
        for i, row in df.iterrows():
            yyyyMMdd_list += [row["日付"].replace('/', '')]

        df.drop(columns = ["日付"], inplace = True)
        df = df.assign(年月日 = yyyyMMdd_list)
        
        # データに含まれる%、()を削除
        dic = {'(':None, ')':None, '%':None, ',':None, '人':None}
        df["湿度"] = df["湿度"].apply(lambda x : x.translate(str.maketrans(dic)))
        df["入場者数"] = df["入場者数"].apply(lambda x : x.translate(str.maketrans(dic)))
        
        # チーム名の統一
        df = self.common.rename_team(df, 'H_team')
        df = self.common.rename_team(df, 'A_team')

        columns_list = ['年月日', 'キックオフ時刻', 'スタジアム', '入場者数', '天候', '気温', '湿度', 'H_team', 'H_監督',
               'A_team', 'A_監督',
               'H_ポジション1', 'H_選手1', 'H_ポジション2', 'H_選手2', 'H_ポジション3', 'H_選手3',
               'H_ポジション4', 'H_選手4', 'H_ポジション5', 'H_選手5', 'H_ポジション6', 'H_選手6',
               'H_ポジション7', 'H_選手7', 'H_ポジション8', 'H_選手8', 'H_ポジション9', 'H_選手9',
               'H_ポジション10', 'H_選手10', 'H_ポジション11', 'H_選手11', 
               'A_ポジション1', 'A_選手1', 'A_ポジション2', 'A_選手2', 'A_ポジション3', 'A_選手3',
               'A_ポジション4', 'A_選手4', 'A_ポジション5', 'A_選手5', 'A_ポジション6', 'A_選手6',
               'A_ポジション7', 'A_選手7', 'A_ポジション8', 'A_選手8', 'A_ポジション9', 'A_選手9',
               'A_ポジション10', 'A_選手10', 'A_ポジション11', 'A_選手11']
        df = df.reindex(columns=columns_list)
        df.to_csv(self.output_dir + 'j_starting_member_cleaned.csv')