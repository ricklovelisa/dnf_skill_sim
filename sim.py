import json
import os
from typing import List, Dict, Union

import pandas as pd
import tqdm
import matplotlib.pyplot as plt

from cdr import SkillCDRInfo, parse_cdr_info
from skill import Skill

DATA_PATH = 'data'


class SkillStatus:
    def __init__(self, skill_list: List[SkillCDRInfo]):
        # {"炸热":{"rest_cd":0.4,"cnt":1}}
        self._skill_status_map = self._init_status_map(skill_list)
        self._skill_cdr_info = skill_list

    def _init_status_map(self, skill_list: List[SkillCDRInfo]):
        result = {}
        for skill in skill_list:
            case = {'res_cd': 0.0, "cnt": 0}
            result[skill.skill.name] = case
        return result

    def cooling_down(self, ts: float, skill_name: str = None):
        if skill_name:
            current_res_cd = self._skill_status_map[skill_name]['res_cd']
            self._skill_status_map[skill_name]['res_cd'] = max(current_res_cd - ts, 0)
        else:
            for skill_name in self._skill_status_map:
                self.cooling_down(ts, skill_name)

    def find_available_skills(self):
        result = []
        for skill_name in self._skill_status_map:
            if self._skill_status_map[skill_name]['res_cd'] == 0:
                result.append(skill_name)

        return result

    def find_almost_available_skills(self):
        result = []
        diff_cds = 99999
        for skill_name in self._skill_status_map:
            if self._skill_status_map[skill_name]['res_cd'] < diff_cds:
                result = [skill_name]
                diff_cds = self._skill_status_map[skill_name]['res_cd']
            if self._skill_status_map[skill_name]['res_cd'] == diff_cds:
                result.append(skill_name)
        return result

    def start_cooling_down(self, skill_name):
        skill_status = self._skill_status_map[skill_name]


class Sim:

    def __init__(self, bias: Union[float, str] = None):
        if bias:
            self._bias = 1

    @staticmethod
    def create_skill_status(skill_pool: List[SkillCDRInfo]) -> SkillStatus:
        return SkillStatus(skill_pool)

    def sim_single(self, skill_pool: List[SkillCDRInfo], total_time: float):
        skill_status = self.create_skill_status(skill_pool)
        time_line = 0
        while True:
            if time_line >= total_time - self._bias:
                break

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

    def _read_set_file(self, set_file_name):
        with open(f'{DATA_PATH}/{set_file_name}/skill_info.json', 'r') as f:
            skill_list = []
            for skill_info in json.load(f):
                skill_list.append(skill_info)

        with open(f'{DATA_PATH}/{set_file_name}/cdr_info.json', 'r') as f:
            cdr_info = json.load(f)

        with open(f'{DATA_PATH}/{set_file_name}/stone_skill_info.json', 'r') as f:
            stone_skill_list = []
            for stone_skill_info in json.load(f):
                stone_skill_list.append(stone_skill_info)
        return skill_list, stone_skill_list, cdr_info

    def _make_skill_cdr_list_with_stone(self, stone_sets, skill_list, stone_skill_list, cdr_info):
        if len(stone_sets) > 3:
        else:
            stone_skill_dict = {}
            for stone_name in stone_sets:
                for stone_skill in stone_skill_list:


    def run(self, set_file_name, stone_sets, max_time, step, records_file_name):
        skill_list, stone_skill_list, cdr_info = self._read_set_file(set_file_name)



if __name__ == '__main__':
    sim = Sim()
    # sim.run(set_file_name='set_0', max_time=60, step=5, records_file_name='无特化技能占比')
    # sim.run(set_file_name='set_1', max_time=60, step=5, records_file_name='无特化技能(雷云护石)占比')
    # sim.run(set_file_name='set_2', max_time=60, step=5, records_file_name='无特化技能(呀呀呀护石)占比')
