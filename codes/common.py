import pandas as pd
import numpy as np
import datetime
import time

class common():
    
    def __init__(self):
        self.FROM_YEAR = 2012
        self.M_TEAM_NAMES = pd.read_csv('data/master/TEAM_NAMES.csv').values.tolist()
        self.PY_NAME = ''

    def get_now_year(self):
        dt_now = datetime.datetime.now()
        return int(dt_now.year)

    def sleep(self, wait_time = 1):
        time.sleep(wait_time)

    def write_log(self, level = 'info', msg = ''):
        now_time = str(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S '))
        s = now_time + '［' + self.PY_NAME + '.py］' + msg
        f = open('log/log_' + level + '.txt', 'a', encoding='UTF-8')
        f.write(s + '\n')
        f.close()
        
        print(msg)

    def rename_team(self, df, tar_col):
        df = df.reset_index(drop = True).copy()
        new_name_list = []

        for i, row in df.iterrows():
            count_change = 0

            if row[tar_col] is np.nan:
                new_name_list += ['-']
                count_change += 1
            else:
                for i, team_list in enumerate(self.M_TEAM_NAMES):
                    if row[tar_col] in team_list:
                        new_name_list += [team_list[0]]
                        count_change += 1

            if count_change == 1:
                pass
            elif count_change == 0:
                new_name_list += [row[tar_col]]
                self.write_log('warning', 'TEAM_NAMES.csvに記載なし：'+str({row[tar_col]}))
            else:
                self.write_log('error', 'TEAM_NAMES.csvを修正してください：' + str({row[tar_col]}))

        df.drop(columns = [tar_col], inplace = True)

        df_tmp = pd.DataFrame(new_name_list, columns = [tar_col])

        df = pd.concat([df, df_tmp],axis=1)
        return df
        
    def drop_y_col(self, df, y_col):
        df = df.copy()
        drop_columns = []
        for col in df.columns:
            if (col[:2] == 'y_') & (col != y_col):
                drop_columns += [col]
        return df.drop(columns = drop_columns)