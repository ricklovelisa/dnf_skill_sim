import json
import os
from typing import Dict, List

import numpy as np
import pandas as pd
import tqdm
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

    @staticmethod
    def read_all_records():
        path = 'C:/Users\QQ\PycharmProjects\阿修罗技能测试/records/'
        all_files = os.listdir(path)
        total_df = None
        for file in [x for x in all_files if 'csv' in x]:
            df = pd.read_csv(f'{path}/{file}')
            df = df[['时间轴', '是否手搓', '护石组合', '符文组合', 'cdr配装信息', '技能队列', '技能伤害', '总伤']]
            df['cdr配装名称'] = df['cdr配装信息'].apply(lambda x:json.loads(x)['name'])
            tag = file.split('_')[0]
            etype = file.split('_')[1]
            df['加点'] = tag
            df['配装类型'] = etype

            if total_df is None:
                total_df = df
            else:
                total_df = pd.concat([total_df, df], axis=0)
        return total_df

    @staticmethod
    def _top_n(grouped_df: pd.DataFrame, n):
        top_n = grouped_df.sort_values(by=['总伤'], ascending=False).iloc[0:n]
        # print(top_n.to_markdown(index=False))
        # print(top_n.shape)
        return top_n

    @staticmethod
    def _statics(grouped_df: pd.DataFrame, col):
        avg_damapge = grouped_df[col].mean()
        median_damage = grouped_df[col].median()

        return pd.Series([avg_damapge, median_damage], index=[f'avg_{col}', f'median_{col}'])

    def _compute_damage_curv(self, skill_damage_list: List[Dict], max_time_line):
        damage_df = {'time_line': [], 'cumulative_damage': []}
        step = 1
        for i in np.arange(0, max_time_line + step, step):
            skill_damage = 0
            for item in skill_damage_list:
                if item['total_time_line'] <= i:
                    skill_damage += item['damage']
            damage_df['time_line'].append(i)
            damage_df['cumulative_damage'].append(skill_damage)

        return pd.DataFrame(damage_df)

    def time_line_analysis(self, df: pd.DataFrame):
        # 根据各个时间轴获取最优候选
        tops_by_time_line = df.groupby(by=['时间轴']).apply(self._top_n, 1)
        print(tops_by_time_line.columns)
        print(tops_by_time_line[
            ['时间轴', '是否手搓', '加点', '护石组合', '符文组合', '配装类型', 'cdr配装信息']].to_markdown(
            index=False))
        # print(max_time_line)
        # print(tops_by_time_line)
        # 根据top1，画出每个时间轴的伤害曲线
        for i in range(tops_by_time_line.shape[0]):
            row = tops_by_time_line.iloc[i]
            time_line = row['时间轴']
            skill_damage_list = json.loads(row['技能队列'])
            damage_curv = self._compute_damage_curv(skill_damage_list, time_line)
            # print(damage_curv['cumulative_damage'].tolist())
            plt.plot(damage_curv['time_line'].tolist(), damage_curv['cumulative_damage'].tolist())
        plt.show()

    def group_analysis(self, df: pd.DataFrame, by: List[str], rank_by=None):
        sort_col = '总伤'
        group_col = by
        if rank_by:
            group_col = by + rank_by
        group_df = df.groupby(by=group_col).apply(self._statics, sort_col).reset_index()
        if rank_by:  # 如果有排序需求，则根据需要排序的字段，加一列排序列
            group_df['rank'] = group_df.groupby(by=rank_by)[f'avg_{sort_col}'].rank(ascending=False)
        group_df = group_df.sort_values(by=f'avg_{sort_col}', ascending=False)
        print(group_df.to_markdown(index=False))

        # 计算平均rank
        if rank_by:
            avg_group_df = group_df.groupby(by=by).apply(self._statics, 'rank').reset_index().sort_values(
                by=f'avg_rank')
            print(avg_group_df.to_markdown(index=False))
        print()


if __name__ == '__main__':
    anal = Analysis()
    # # anal.analysis_skill_pct('无特化技能(雷云护石)占比')
    # anal.compare('无特化技能占比', '无特化技能(雷云护石)占比', '雷云')
    # anal.compare('无特化技能占比', '无特化技能(呀呀呀护石)占比', '呀呀呀')
    # df = anal.read_all_records()
    df = pd.read_csv('../records/不动加点_实际有的配装_record_2023_08_13_03_06_30.csv')
    df['cdr配装名称'] = df['cdr配装信息'].apply(lambda x: json.loads(x)['name'])
    df['加点'] = '不动加点'
    df['配装类型'] = '实际有的配装'

    # 整体时间轴分析
    anal.time_line_analysis(df)

    # 护石符文分析
    anal.group_analysis(df, by=['护石组合'], rank_by=['时间轴'])

    # 加点分析
    anal.group_analysis(df, by=['加点'], rank_by=['时间轴'])

    # 配装分析
    anal.group_analysis(df, by=['配装类型', 'cdr配装名称'], rank_by=['时间轴'])

    # # 交叉分析
    # # 护石+加点分析
    # anal.group_analysis(df, by=['护石组合', '加点'])
    # # 护石+配装分析
    # anal.group_analysis(df, by=['护石组合', '配装类型', 'cdr配装信息'])
    # # 加点+配装分析
    # anal.group_analysis(df, by=['加点', '配装类型', 'cdr配装信息'])
    # # 护石+加点+配装
    # anal.group_analysis(df, by=['护石组合', '加点', '配装类型', 'cdr配装信息'])

    # df = anal.read_all_records()
    # df.to_csv('total_data', encoding='utf_8_sig', index=False)
    #
    # # 先做时间轴分析，分析各个时间轴上，最优护石组合、最优符文组合、最优cdr配装信息、最优加点
    # anal.time_line_analysis(df)

    # df = pd.read_csv(
    #     'C:/Users\QQ\PycharmProjects\阿修罗技能测试/records\不动加点_实际有的配装_record_2023_08_13_01_56_43.csv')
    # print(df.columns)
    # skill_list = json.loads(df[df['时间轴'] == 40].sort_values(by="总伤", ascending=False)['技能队列'].iloc[0])
    # skill_damage = 0
    # damage_list = []
    # for item in skill_list:
    #     # print(item)
    #     skill_damage += item['damage']
    #     damage_list.append(skill_damage)
    #
    # import matplotlib.pyplot as plt
    #
    # plt.plot(damage_list)
    # plt.show()
