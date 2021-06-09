import numpy as np
import pandas as pd
import requests
from bs4 import BeautifulSoup
import re
import urllib.parse

import codes.common as c

class j_rank_table():

    def __init__(self):
        self.common = c.common()
        self.common.PY_NAME = 'j_rank_table'
        self.COMPE_LABEL_LIST_1 = ["J1", "Ｊリーグ　ディビジョン１", "明治安田生命Ｊ１リーグ １ｓｔ", "明治安田生命Ｊ１リーグ ２ｎｄ", "明治安田生命Ｊ１リーグ"]
        self.COMPE_LABEL_LIST_2 = ["J2", "Ｊリーグ　ディビジョン２", "明治安田生命Ｊ２リーグ"]
        self.COMPE_LABEL_LIST_3 = ["J3", "明治安田生命Ｊ３リーグ", "明治安田生命　Ｊ３リーグ"]
        self.output_dir = 'data/scraping/j_league_data_site/'
        
    def scraping(self):
        now_year = self.common.get_now_year()
        from_year = now_year
        
        df_result = pd.read_csv(self.output_dir + 'j_rank_table.csv', index_col=0)
        df_result = df_result[df_result['年度'] != now_year]
        
        for year in range(from_year, now_year + 1):
            url = 'https://data.j-league.or.jp/SFRT01/?competitionSectionIdLabel=%E2%86%90%E9%81%B8%E6%8A%9E%E3%81%97%E3%81%A6%E3%81%8F%E3%81%A0%E3%81%95%E3%81%84&competitionIdLabel=%E2%96%BC&yearIdLabel=' + str(year) + '%E5%B9%B4&yearId=' + str(year) + '&competitionId=&competitionSectionId=&search=search'

            self.common.sleep() # スリープ処理
            self.common.write_log(msg = 'competitionIdの取得:' + str(year))
            self.common.write_log(msg = url)
            site = requests.get(url)
            soup = BeautifulSoup(site.text, 'html.parser')

            competitionId_list = str(soup.find(id='competitionId')).split('\n')

            competition_Id_list = []
            competition_label_list = []
            for val in competitionId_list:
                competition_Id = re.findall('<option value="(.*)"', val)
                competition_label = [re.findall('>(.*)<', val)]
                try:
                    if competition_label[0][0] in self.COMPE_LABEL_LIST_1 + self.COMPE_LABEL_LIST_2 + self.COMPE_LABEL_LIST_3:
                        competition_Id_list += [int(competition_Id[0])]
                        competition_label_list += [competition_label[0][0]]
                    else:
                        continue
                except:
                    continue

            for i in range(len(competition_label_list)):
                competition_label = urllib.parse.quote(competition_label_list[i])
                url = 'https://data.j-league.or.jp/SFRT01/?competitionSectionIdLabel=%E2%96%BC&competitionIdLabel='
                url += competition_label
                url += '&yearIdLabel=' + str(year) + '%E5%B9%B4&yearId=' + str(year)
                url += '&competitionId=' + str(competition_Id_list[i]) + '&competitionSectionId=&search=search'

                self.common.sleep() # スリープ処理
                self.common.write_log(msg = 'competitionSectionIdの取得:' + str(year) +' '+ competition_label_list[i])
                self.common.write_log(msg = url)
                site = requests.get(url)
                soup = BeautifulSoup(site.text, 'html.parser')
                competitionSectionId_list = str(soup.find(id='competitionSectionId')).split('\n')

                section_id_list = []
                for c_id in competitionSectionId_list:
                    section_id = re.findall('>(.*)<', c_id)
                    try:
                        if '第' in section_id[0]:
                            section_id_list += [section_id[0]]
                    except:
                        pass

                for j in range(len(section_id_list)):
                    n_sec = str(int(re.findall('第(.*)節', section_id_list[j])[0]))
                    url = 'https://data.j-league.or.jp/SFRT01/?competitionSectionIdLabel='
                    url += urllib.parse.quote(section_id_list[j])
                    url += '&competitionIdLabel=' + competition_label
                    url += '&yearIdLabel=' + str(year) + '%E5%B9%B4&yearId=' + str(year)
                    url += '&competitionId=' + str(competition_Id_list[i])
                    url += '&competitionSectionId=' + str(int(re.findall('第(.*)節', section_id_list[j])[0])) + '&search=search'
                    
                    self.common.sleep() # スリープ処理             
                    self.common.write_log(msg = 'データ取得:' + str(year) +' '+ competition_label_list[i]+' '+section_id_list[j])
                    self.common.write_log(msg = url)
                    
                    df_tmp = pd.DataFrame(pd.read_html(url)[0])

                    df_tmp['年度'] = year
                    df_tmp['カテゴリ'] = competition_label_list[i]
                    df_tmp['節'] = n_sec

                    df_result = pd.concat([df_result, df_tmp])
        
        # csv出力
        df_result.to_csv(self.output_dir + 'j_rank_table.csv')
        
    def clean(self):
        self.common.write_log(msg = 'お掃除開始')
        # 読み込み
        df = pd.read_csv(self.output_dir + 'j_rank_table.csv', index_col=0)
        # チーム名の統一
        df = self.common.rename_team(df, 'チーム')
        # カラム抽出
        columns = ['年度', 'カテゴリ', '節', 'チーム', '順位','勝点', '試合', '勝', '分', '敗', '得点', '失点', '得失点差', '年間勝点順位', '総勝点']
        df = df[columns]
        # 不要な文字列の削除
        df['順位'] = df['順位'].apply(lambda x : x.replace('※', ''))
        # カテゴリ列の表記統一
        df['stage'] = '0'
        df.loc[df['カテゴリ'] == '明治安田生命Ｊ１リーグ １ｓｔ' , 'stage'] = '1'
        df.loc[df['カテゴリ'] == '明治安田生命Ｊ１リーグ ２ｎｄ' , 'stage'] = '2'
        category_list = []
        for i, row in df.iterrows():
            category = row["カテゴリ"]
            if category in self.COMPE_LABEL_LIST_1:
                category_list += ['J1']
            elif category in self.COMPE_LABEL_LIST_2:
                category_list += ['J2']
            else:
                category_list += ['J3']
        df.drop(columns = ["カテゴリ"], inplace = True)
        df = df.assign(カテゴリ = category_list)
        # 1st, 2ndに分割されている試合を統合
        df_st = df[df['stage'] != '0']
        df = df[df['stage'] == '0']
        df_st = df_st.reset_index(drop=True)
        df_result = None
        for i, row in df_st.iterrows():
            if row['stage'] == '1':
                pass
            else:
                row_past = df_st[(df_st['年度'] == row["年度"]) & (df_st['stage'] == '1') & (df_st['チーム'] == row["チーム"])].sort_values(['節'], ascending = False).iloc[:1]

                row["節"] = row["節"] + row_past["節"].values[0]
                row["順位"] = row["年間勝点順位"]
                row["勝点"] = row["総勝点"]
                row["試合"] = row["試合"] + row_past["試合"].values[0]
                row["勝"] = row["勝"] + row_past["勝"].values[0]
                row["分"] = row["分"] + row_past["分"].values[0]
                row["敗"] = row["敗"] + row_past["敗"].values[0]
                row["得点"] = row["得点"] + row_past["得点"].values[0]
                row["失点"] = row["失点"] + row_past["失点"].values[0]
                row["得失点差"] = row["得失点差"] + row_past["得失点差"].values[0]
            df_tmp = pd.DataFrame([row])
            df_result = pd.concat([df_result, df_tmp],axis=0)
        df_st = df_result
        df = pd.concat([df, df_st])
        df.drop(columns = ["年間勝点順位", "総勝点", 'stage'], inplace = True)
        # 試合結果が反映されている値を試合前の値に修正
        df.reset_index(drop=True)
        df_result = None
        for i, row in df.iterrows():
            if row['順位'] =='':
                row['順位'] = 10
            tar_sec = row['節']
            newest_sec = df[(df['チーム'] == row['チーム'])&(df['年度'] == row['年度'])].sort_values(['節'], ascending = False).iloc[:1]['節'].values[0]
            if tar_sec != newest_sec:
                row['節'] += 1
                df_tmp = pd.DataFrame([row])
                df_result = pd.concat([df_result, df_tmp],axis=0)
            else:
                row2 = row.copy()
                row2['節'] = 1
                row2['順位'] = 10
                row2['勝点'] = 0
                row2['試合'] = 0
                row2['勝'] = 0
                row2['分'] = 0
                row2['敗'] = 0
                row2['得点'] = 0
                row2['失点'] = 0
                row2['得失点差'] = 0
                df_tmp = pd.DataFrame([row2])
                df_result = pd.concat([df_result, df_tmp],axis=0)
                if row['年度'] == self.common.get_now_year():
                    row['節'] += 1
                    df_tmp = pd.DataFrame([row])
                    df_result = pd.concat([df_result, df_tmp],axis=0)
            
        # 並び替え
        df_result = df_result.sort_values(['年度', 'カテゴリ', '節', '順位'], ascending = True)
        df_result = df_result.reset_index(drop=True)
        # csv出力
        df_result.to_csv(self.output_dir + 'j_rank_table_cleaned.csv')
        self.common.write_log(msg = 'お掃除終了')