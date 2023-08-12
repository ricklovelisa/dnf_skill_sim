import json
from typing import Dict

import pandas as pd
from matplotlib import pyplot as plt


class Analysis:

    def read_records(self, record_file_name) -> Dict:
        with open(f'records/{record_file_name}.json', 'r') as f:
            return json.load(f)

    def analysis_skill_pct(self, file_name):
        total_result = self.read_records(file_name)

        df_dict = {'time': []}
        for apl_time in total_result:
            df_dict['time'].append(apl_time['time'])
            for apl in apl_time['apl']:
                apl_name = apl['name']
                damage = apl['damage']
                if apl_name in df_dict:
                    df_dict[apl_name].append(damage)
                else:
                    df_dict[apl_name] = [damage]
        df = pd.DataFrame(df_dict)
        # plt.rcParams['font.sans-serif'] = ['SimHei']
        # plt.rcParams['axes.unicode_minus'] = False
        # df.plot(x='time', kind='bar')
        # plt.show()

        total = df[
            ['邪光', '波爆', '小冰', '无双', '小火', '炸热', '不动', '大冰', '大火', '呀呀呀', '雷云',
             '无为法']].sum(axis=1)
        time = df['time']
        for col in ['邪光', '波爆', '小冰', '无双', '小火', '炸热', '不动', '大冰', '大火', '呀呀呀', '雷云',
                    '无为法']:
            y = df[col]
            plt.rcParams['font.sans-serif'] = ['Songti SC']
            plt.rcParams['axes.unicode_minus'] = False
            plt.bar(x=time, height=y / total)
            plt.title(col)
            plt.show()

    def _trans_to_df(self, records, value_tag):
        df_dict = {'time': []}
        for record in records:
            apl_list = record['apl']
            df_dict['time'].append(record['time'])
            for apl in apl_list:
                name = apl['name']
                if name in df_dict:
                    df_dict[name].append(apl[value_tag])
                else:
                    df_dict[name] = [apl[value_tag]]
        df = pd.DataFrame(df_dict)
        df[f'total_{value_tag}'] = df[df.columns[1:]].sum(axis=1)
        return df

    def compare(self, base_record_file_name, target_record_file_name, skill_name):
        base_df = self._trans_to_df(self.read_records(base_record_file_name), 'damage')
        target_df = self._trans_to_df(self.read_records(target_record_file_name), 'damage')
        incr_df = (target_df[[skill_name]] - base_df[[skill_name]]) / base_df[[skill_name]]
        incr_df['time'] = base_df['time']
        incr_df['total_incr'] = (target_df['total_damage'] - base_df['total_damage']) / base_df['total_damage']

        print(incr_df)


if __name__ == '__main__':
    # anal = Analysis()
    # # anal.analysis_skill_pct('无特化技能(雷云护石)占比')
    # anal.compare('无特化技能占比', '无特化技能(雷云护石)占比', '雷云')
    # anal.compare('无特化技能占比', '无特化技能(呀呀呀护石)占比', '呀呀呀')
    df = pd.read_csv(
        'C:/Users\QQ\PycharmProjects\阿修罗技能测试/records\不动加点_实际有的配装_record_2023_08_13_01_56_43.csv')
    print(df.columns)
    skill_list = json.loads(df[df['时间轴'] == 40].sort_values(by="总伤", ascending=False)['技能队列'].iloc[0])
    skill_damage = 0
    damage_list = []
    for item in skill_list:
        # print(item)
        skill_damage += item['damage']
        damage_list.append(skill_damage)

    import matplotlib.pyplot as plt

    plt.plot(damage_list)
    plt.show()
