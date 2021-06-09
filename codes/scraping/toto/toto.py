import pandas as pd
import time
import codes.common as c

class toto():
    def __init__(self):
        self.common = c.common()
        self.common.PY_NAME = 'toto'
        
    def scraping_and_clean(self):
        self.scraping()
        self.clean()
    
    def scraping(self):
        
        df = pd.read_csv('data/scraping/toto/toto_info_cleaned.csv', index_col=0).reset_index(drop=True)
        n_start = df.sort_values(['第n回'], ascending=False)['第n回'][:1].values[0] - 5
        n_end = n_start + 10
        df_result = df[df['第n回'] < n_start].copy()
            
        for i in range(n_start, n_end+1):
            df_toto, df_mini_a, df_mini_b = None, None, None

            if i < 1000:
                n = '0' + str(i)
            else:
                n = str(i)
            base_url = 'https://store.toto-dream.com/dcs/subos/screen/pi04/spin011/PGSPIN01101LnkHoldCntLotResultLsttoto.form?holdCntId='
            base_url2 = 'https://store.toto-dream.com/dcs/subos/screen/pi01/spin000/PGSPIN00001DisptotoLotInfo.form?holdCntId='
            url = base_url + n
            self.common.write_log(msg = '処理中' + str(n))
            self.common.write_log(msg = url)
            self.common.sleep() # スリープ処理
            data = pd.read_html(url)

            if data[0].values[0][0] =='ご指定のくじ結果は表示できません。':
                url = base_url2 + n
                self.common.write_log(msg = '処理中' + str(n))
                self.common.write_log(msg = url)
                self.common.sleep() # スリープ処理
                data = pd.read_html(url)

            for j in range(len(data)):
                tar_str = data[j].values[0][0]
                if tar_str == '第' + str(i) + '回 toto\u3000くじ結果':
                    df_toto = self._get_toto_result(j+1, i, data)
                elif tar_str == '第' + str(i) + '回 mini toto-A組\u3000くじ結果':
                    df_mini_a = self._get_minitoto_result(j+1, i, data, 'A組')
                elif tar_str == '第' + str(i) + '回 mini toto-B組\u3000くじ結果':
                    df_mini_b = self._get_minitoto_result(j+1, i, data, 'B組')
                elif tar_str == '第' + str(i) + '回 toto くじ情報':
                    df_toto = self._get_toto_info(j+1, i, data, 'toto')
                elif tar_str == '第' + str(i) + '回 mini toto-A組 くじ情報':
                    df_mini_a = self._get_toto_info(j+1, i, data, 'mini toto-A組')
                elif tar_str == '第' + str(i) + '回 mini toto-B組 くじ情報':
                    df_mini_b = self._get_toto_info(j+1, i, data, 'mini toto-B組')

            if df_toto is None and df_mini_a is None and df_mini_b is None:
                continue
            df_tmp = pd.concat([df_toto, df_mini_a, df_mini_b])
            df_result = pd.concat([df_result, df_tmp])
        
        df_result.to_csv("data/scraping/toto/toto_info.csv")
        
    def clean(self):
        event_date_list = []
        win_money_list1, win_money_list2, win_money_list3 = [], [], []
        win_count_list1, win_count_list2, win_count_list3 = [], [], []
        over_money_list1, over_money_list2, over_money_list3 = [], [], []
        
        df = pd.read_csv('data/scraping/toto/toto_info.csv', index_col=0).reset_index(drop=True).fillna(0)

        for i, row in df.iterrows():
            year = row['販売開始日'][:4]
            event_date = row['開催日'].replace('/', '')
            event_date = event_date[len(event_date)-4:len(event_date)]
            event_date_list += [year + event_date]
            win_money_list1 += [str(row['当選金_1']).replace(',', '').replace('円', '')]
            win_money_list2 += [str(row['当選金_2']).replace(',', '').replace('円', '')]
            win_money_list3 += [str(row['当選金_3']).replace(',', '').replace('円', '')]
            over_money_list1 += [str(row['次回への繰越金_1']).replace(',', '').replace('円', '')]
            over_money_list2 += [str(row['次回への繰越金_2']).replace(',', '').replace('円', '')]
            over_money_list3 += [str(row['次回への繰越金_3']).replace(',', '').replace('円', '')]
            win_count_list1 += [str(row['当せん口数_1']).replace('口', '').replace(',', '')]
            win_count_list2 += [str(row['当せん口数_2']).replace('口', '').replace(',', '')]
            win_count_list3 += [str(row['当せん口数_3']).replace('口', '').replace(',', '')]

        df.drop(columns = ["開催日", '当選金_1', '当選金_2', '当選金_3', '次回への繰越金_1', '次回への繰越金_2', '次回への繰越金_3', '当せん口数_1', '当せん口数_2', '当せん口数_3'], inplace = True)
        df = df.assign(開催日 = event_date_list, 当選金_1= win_money_list1, 当選金_2= win_money_list2, 当選金_3= win_money_list3
                       , 次回への繰越金_1 = over_money_list1, 次回への繰越金_2 = over_money_list2, 次回への繰越金_3 = over_money_list3
                       , 当せん口数_1 = win_count_list1, 当せん口数_2 = win_count_list2, 当せん口数_3 = win_count_list3)

        columns = ['第n回', '種別', 'No', '開催日', 'ホーム', 'アウェイ', '試合結果', 'くじ結果', '当選金_1', '当選金_2', '当選金_3', '次回への繰越金_1', '次回への繰越金_2', '次回への繰越金_3', '当せん口数_1', '当せん口数_2', '当せん口数_3', '販売開始日', '販売終了日', '結果発表日', '払戻開始日', '払戻期限']
        df = df.reindex(columns=columns)
        df.to_csv("data/scraping/toto/toto_info_cleaned.csv")

    def _get_toto_info(self, n, n2, data, s):
        try:
            df1 = pd.DataFrame(data[n+1])
            df1 = df1[['Unnamed: 0', '開催日', '指定試合（ホームvsアウェイ）', '指定試合（ホームvsアウェイ）.2']]
            df1 = df1.rename(columns={'Unnamed: 0': 'No', '指定試合（ホームvsアウェイ）': 'ホーム', '指定試合（ホームvsアウェイ）.2': 'アウェイ'})# df1['種別'] = 'toto'
            df1['第n回'] = n2
            df1['種別'] = s
            l = data[n][1].values
            df1['販売開始日'] = l[0]
            df1['販売終了日'] = l[1]
            df1['結果発表日'] = l[2]
            df1['払戻開始日'] = data[n+3].values[0][1]
            df1['払戻期限'] = data[n+3].values[1][1]
            df1['試合結果'] = '未実施'
            df1['くじ結果'] = '未実施'
        except IndexError:
            # くじが中止の場合
            df1 = None
        return df1

    def _get_toto_result(self, n, n2, data):
        try:
            df1 = pd.DataFrame(data[n])
            df1 = pd.concat([df1['開催日'], df1['予想チーム']], axis = 1)
            df1['種別'] = 'toto'
            df1['第n回'] = n2
            l = data[n+2].values[0]
            df1['販売開始日'] = l[0]
            df1['販売終了日'] = l[1]
            df1['結果発表日'] = l[2]
            l = data[n+3].values[0]
            df1['払戻開始日'] = l[0]
            df1['払戻期限'] = l[1]

            columns = ['当選金_1', '当せん口数_1', '次回への繰越金_1', '当選金_2', '当せん口数_2', '次回への繰越金_2', '当選金_3', '当せん口数_3', '次回への繰越金_3']
            df2 = pd.DataFrame(data[n+1]['1等'].values.tolist() + data[n+1]['2等'].values.tolist() + data[n+1]['3等'].values.tolist(), index = columns).T
            df2['第n回'] = n2

            df_toto = pd.merge(df1, df2, 
                         on=['第n回'], how='left')
        except IndexError:
            # くじが中止の場合
            df_toto = None
        return df_toto
    
    def _get_minitoto_result(self, n, n2, data, s):
        try:
            df1 = pd.DataFrame(data[n])
            df1 = pd.concat([df1['開催日'], df1['予想チーム']], axis = 1)
            df1['種別'] = 'mini toto-' + s
            df1['第n回'] = n2
            l = data[n+2].values[0]
            df1['販売開始日'] = l[0]
            df1['販売終了日'] = l[1]
            df1['結果発表日'] = l[2]
            l = data[n+3].values[0]
            df1['払戻開始日'] = l[0]
            df1['払戻期限'] = l[1]

            columns = ['当選金_1', '当せん口数_1', '次回への繰越金_1']
            df2 = pd.DataFrame(data[n+1]['1等'].values.tolist(), index = columns).T
            df2['第n回'] = n2

            df_mini = pd.merge(df1, df2, 
                         on=['第n回'], how='left')
        except IndexError:
            # くじが中止の場合
            df_mini = None
        return df_mini