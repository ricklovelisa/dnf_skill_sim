import json
import os
from typing import List, Dict

import pandas as pd
import tqdm
import matplotlib.pyplot as plt

from cdr import CDRInfo, parse_cdr_info
from skill import Skill, parse_skill

DATA_PATH = 'data'


class Sim:

    def run_with_time(self, skill_list: List[Skill], cdr_info_json: dict, time: int):
        # 先根据skill list和cdr_info_json生成对应技能的cdr
        result = parse_cdr_info(skill_list, cdr_info_json)

        # 根据skill_list和cdr_info生成每个技能的次数
        skill_apl = []
        for cdr_info in result:
            # print("=======================================")
            # print(cdr_info.skill.detail)
            time_cost = 0
            times = 0
            while True:
                if time_cost + 2 >= time:
                    break
                # print("++++++++++++++++++++++++++++++++++++++++++++++++++")
                times += 1
                real_cd = cdr_info.get_final_cd(times)
                time_cost += real_cd
                # print(f'time cost: {time_cost}')
                # print("++++++++++++++++++++++++++++++++++++++++++++++++++")
            # print("=======================================")
            # print()
            skill_apl.append(
                {'name': cdr_info.skill.name, 'n': times, 'damage': cdr_info.skill.get_final_damage(time, times)})
        # print(json.dumps(skill_apl, ensure_ascii=False, indent=4))
        return skill_apl

    def analysis_total(self, total_result: Dict):
        total_damage_dict = {}
        for set_info, apl_time_list in total_result.items():
            time_list = []
            damage_list = []
            for apl_time in apl_time_list:
                apl_list = apl_time['apl']
                total_damage = 0
                for apl in apl_list:
                    total_damage += apl['damage']
                time_list.append(apl_time['time'])
                damage_list.append(total_damage)
            if 'time' not in total_damage_dict:
                total_damage_dict['time'] = time_list
            total_damage_dict[set_info] = damage_list
        df = pd.DataFrame(total_damage_dict)
        df.plot(x='time', kind='bar')
        plt.show()

    def analysis_skill_pct(self, total_result: Dict):
        for set_info, apl_time_list in total_result.items():
            df_dict = {'time': []}
            for apl_time in apl_time_list:
                apl_list = apl_time['apl']
                time = apl_time['time']
                df_dict['time'].append(time)
                for apl in apl_list:
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
                plt.bar(x=time, height=y/total)
                plt.title(col)
                plt.show()


if __name__ == '__main__':
    # from matplotlib import font_manager
    # for font in font_manager.fontManager.ttflist:
    #     查看字体名以及对应的字体文件名
        # print(font.name, '-', font.fname)

    set_list = os.listdir(DATA_PATH)
    sim = Sim()

    total_result = {}
    for set_file in tqdm.tqdm(set_list):
        if set_file not in ['set_0']:
            continue
        for time in tqdm.tqdm(range(10, 65, 5)):
            with open(f'{DATA_PATH}/{set_file}/set_info', 'r') as f:
                set_info = f.read()

            with open(f'{DATA_PATH}/{set_file}/skill_info.json', 'r') as f:
                skill_list = []
                for skill_info in json.load(f):
                    skill_list.append(parse_skill(skill_info))

            with open(f'{DATA_PATH}/{set_file}/cdr_info.json', 'r') as f:
                cdr_info_json = json.load(f)

            apl = sim.run_with_time(skill_list, cdr_info_json, time)
            case = {'apl': apl, 'time': time}

            if set_file in total_result:
                total_result[set_file].append(case)
            else:
                total_result[set_file] = [case]

    print(json.dumps(total_result, ensure_ascii=False))
    # sim.analysis_total(total_result)
    sim.analysis_skill_pct(total_result)
