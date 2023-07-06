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

    def run(self, set_file_name, max_time, step, records_file_name):
        total_result = []
        for time in tqdm.tqdm(range(10, max_time + step, step)):
            with open(f'{DATA_PATH}/{set_file_name}/skill_info.json', 'r') as f:
                skill_list = []
                for skill_info in json.load(f):
                    skill_list.append(parse_skill(skill_info))

            with open(f'{DATA_PATH}/{set_file_name}/cdr_info.json', 'r') as f:
                cdr_info_json = json.load(f)

            apl = sim.run_with_time(skill_list, cdr_info_json, time)
            case = {'apl': apl, 'time': time}
            total_result.append(case)

        with open(f'records/{records_file_name}.json', 'w') as f:
            json.dump(total_result, f, ensure_ascii=False)
            print(json.dumps(total_result, ensure_ascii=False))


if __name__ == '__main__':
    sim = Sim()
    # sim.run(set_file_name='set_0', max_time=60, step=5, records_file_name='无特化技能占比')
    # sim.run(set_file_name='set_1', max_time=60, step=5, records_file_name='无特化技能(雷云护石)占比')
    # sim.run(set_file_name='set_2', max_time=60, step=5, records_file_name='无特化技能(呀呀呀护石)占比')
