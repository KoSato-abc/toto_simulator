import numpy as np
import pandas as pd
import urllib.parse
import codes.common as c
import time
import re

class j_match_schedule():
    
    def __init__(self):
        self.common = c.common()
        self.common.PY_NAME = 'j_match_schedule'
        self.output_dir = 'data/scraping/j_league_data_site/'
        
    def scraping(self):
        self.common.write_log(msg = 'スクレイピング開始')
        URL_HEAD = "https://data.j-league.or.jp/SFMS01/search?competition_years="
        URL_FOOT = "&tv_relay_station_name="
        now_year = self.common.get_now_year()
        
        df_result = None
        
        for year in range(self.common.FROM_YEAR, now_year+1):
            
            url = URL_HEAD + str(year) + URL_FOOT
            self.common.write_log(msg = '処理中：' + str(year))
            self.common.write_log(msg = 'url=' + url)
            self.common.sleep() # スリープ処理
            df_tmp = pd.DataFrame(pd.read_html(url)[0]) # データ取得

            df_result = pd.concat([df_result, df_tmp])
            
        self.common.write_log(msg = 'スクレイピング終了')
        df_result.to_csv( self.output_dir + "j_match_schedule.csv")
        
    def clean(self):
        self.common.write_log(msg = 'お掃除開始')
        df = pd.read_csv(self.output_dir + "j_match_schedule.csv", index_col=0)
        
        section_list = []
        yyyyMMdd_list = []
        for i, row in df.iterrows():
            section = row["節"]
            year = str(row["年度"])
            day = row["試合日"]

            if section is np.nan:
                section_list += [0]
            else:
                section_m = re.findall('第(.*)節', section)
                if len(section_m) == 0:
                    section_list += [0]
                else:
                    section_list += section_m

            if day == "未定":
                yyyyMMdd_list += [day]
            else:
                month = re.findall('(.*)/', day)[0]
                day = re.findall('/(.*)\(', day)[0]
                yyyyMMdd_list += [year+month+day]

        df.drop(columns = ["節", "試合日"], inplace = True)
        df = df.assign(節 = section_list, 試合日 = yyyyMMdd_list)
        
        # チーム名の統一
        df = self.common.rename_team(df, 'ホーム')
        df = self.common.rename_team(df, 'アウェイ')
        # 表記統一
        df['大会'] = df['大会'].apply(lambda x : x.replace('Ｊ１ １ｓｔ', 'J1').replace('Ｊ１ ２ｎｄ', 'J1').replace('Ｊ１', 'J1'))
        df['大会'] = df['大会'].apply(lambda x : x.replace('Ｊ２', 'J2'))
        df['大会'] = df['大会'].apply(lambda x : x.replace('Ｊ３', 'J3'))
        df['スコア'] = df['スコア'].apply(lambda x : x.replace('vs', '未実施'))
        # 欠損値処理
        df.fillna({'インターネット中継・TV放送': 'なし', '入場者数': 0, 'K/O時刻': '00:00'}, inplace = True)
        df = df.rename(columns={'試合日': '年月日', 'ホーム': 'H_team', 'アウェイ': 'A_team', '大会': 'カテゴリ'})
        # 整理
        columns_list = ['年度', '年月日', 'カテゴリ', '節', 'H_team', 'A_team', 'スコア', 'スタジアム', 'K/O時刻', '入場者数', 'インターネット中継・TV放送']
        df = df.reindex(columns=columns_list)
        df = df.reset_index(drop=True).copy()
        # 出力
        df.to_csv(self.output_dir + "j_match_schedule_cleaned.csv")
        self.common.write_log(msg = 'お掃除終了')