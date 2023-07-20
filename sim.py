import json
import os
import random
from itertools import combinations
from typing import List, Dict, Union, Tuple

import pandas as pd
import tqdm
import matplotlib.pyplot as plt

from cdr import SkillCDRInfo, parse_cdr_info
from skill import Skill

DATA_PATH = 'data'


class SkillStatus:
    def __init__(self, skill_info: Dict):
        # {"炸热":{"rest_cd":0.4,"cnt":1}}
        self._skill_status_map = self._init_status_map(skill_info)
        self._skill_cdr_info = skill_info

    def _init_status_map(self, skill_info: Dict):
        result = {}
        for skill in skill_info:
            case = {'res_cd': 0.0, "cnt": 0}
            result[skill.skill.name] = case
        return result

    def cooling_down(self, ts: float, except_skill_name: str):
        for skill_name in self._skill_status_map:
            if skill_name != except_skill_name:
                current_res_cd = self._skill_status_map[skill_name]['res_cd']
                self._skill_status_map[skill_name]['res_cd'] = max(current_res_cd - ts, 0)

    def find_almost_available_skills(self) -> Dict[float, List[str]]:
        result = {}
        diff_cds = 99999
        for skill_name in self._skill_status_map:
            res_cd = self._skill_status_map[skill_name]['res_cd']
            if res_cd < diff_cds:
                result = {res_cd: [skill_name]}
                diff_cds = res_cd
            elif res_cd == diff_cds:
                result[res_cd].append[skill_name]
        return result

    def start_cooling_down(self, skill_name: str, cd: float):
        self._skill_status_map[skill_name]['res_cd'] = cd

    def add_skill_cnt(self, skill_name: str, cnt):
        self._skill_status_map[skill_name]['cnt'] += cnt
        return self._skill_status_map[skill_name]['cnt']


class Sim:

    def __init__(self, bias: Union[float, str] = 1, human_refletion=0.1):
        self._bias = bias
        self._human_refletion = human_refletion

    def run_with_time(self, skill_dict: Dict, cdr_info_json: Dict, time: int):
        # 先根据skill list和cdr_info_json生成对应技能的cdr
        result = parse_cdr_info(skill_dict, cdr_info_json)

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
            skill_info = json.load(f)

        with open(f'{DATA_PATH}/{set_file_name}/cdr_info.json', 'r') as f:
            cdr_info = json.load(f)

        with open(f'{DATA_PATH}/{set_file_name}/stone_skill_info.json', 'r') as f:
            stone_skill_info = json.load(f)
        return skill_info, stone_skill_info, cdr_info

    def _get_stone_sets(self, stone_sets: List[str]) -> List[Union[Tuple, List]]:
        if len(stone_sets) > 3:
            return list(combinations(stone_sets, 3))
        else:
            return [stone_sets]

    @staticmethod
    def _create_skill_status(skill_pool: Dict) -> SkillStatus:
        return SkillStatus(skill_pool)

    def _create_skill_cdr_info(self, skill_list, skill_info: Dict, stone_set: List, stone_skill_info: Dict,
                               cdr_info: Dict):
        fianl_skill_info = {}
        for skill_name in skill_list:
            # 获取仅能信息
            # 如果技能有护石，则更新护石信息
            raw_info = skill_info[skill_name]
            if skill_name in stone_set and skill_name in stone_skill_info:
                stone_info = stone_skill_info[skill_name]
                skill = Skill.create_skill_with_stone(skill_name, raw_info, stone_info)
                fianl_skill_info[skill_name] = skill
            else:
                fianl_skill_info[skill_name] = Skill(skill_name, raw_info)

        return parse_cdr_info(fianl_skill_info, cdr_info)

    def _action(self, skill_cdr: SkillCDRInfo, skill_status: SkillStatus):
        # 模拟执行
        skill = skill_cdr.skill
        # 获取该技能cd
        cnt = skill_status.add_skill_cnt(skill.name, 1)
        cd = skill.get_final_cd(cnt)

        # 更新该技能的cd状态
        real_cd = skill.skill.cast_time + cd
        skill_status.start_cooling_down(skill.name, real_cd)

        # 判断是否有可柔化的技能
        next_skill_list = []
        if skill.skill.force_next_skill_time:
            next_skill_list.extend(list(skill.skill.force_next_skill_time.keys))

        # 返回本次执行技能的耗时，需要同时考虑cast 和 during
        return skill.skill.cast_time + skill.skill.during, next_skill_list

    def _get_a_skill(self, skill_status: SkillStatus):
        aval_skills = skill_status.find_almost_available_skills()
        wait_time = list(aval_skills.keys())[0]
        skills = aval_skills[wait_time]
        if len(skills) == 1:
            return wait_time, skills[0]
        else:
            return wait_time, random.choice(skills, 1)

    def _force_process(self, last_skill_info: Dict, current_skill: Skill):
        if last_skill_info:
            last_skill = last_skill_info['last']
            next_skill_list = last_skill_info['next']

        else:
            return 0

    def sim_with_random(self, skill_pool: Dict[str, SkillCDRInfo], total_time: float):
        skill_status = self._create_skill_status(skill_pool)
        time_line = 0
        last_skill_info = {}
        while True:
            if time_line >= total_time - self._bias:
                break

            # 随机选择一个技能
            wait_time, skill_name = self._get_a_skill(skill_status)
            skill_cdr = skill_pool[skill_name]

            # 判断是否为柔化技能
            force_time_reduce = self._force_process(last_skill_info, skill_cdr.skill)
            time_line = time_line - force_time_reduce

            # 执行技能
            action_time, next_skill = self._action(skill_cdr, skill_status)
            time_line = time_line + wait_time + self._human_refletion + action_time

            # 更新所有技能的cd状态，以供下一次循环时使用
            skill_status.cooling_down(, skill_name)

    def run(self, set_file_name, stone_sets, skill_list, max_time, step):
        skill_info, stone_skill_info, cdr_info = self._read_set_file(set_file_name)

        # 先根据护石信息，生成护石sets
        stone_set_list = self._get_stone_sets(stone_sets)

        # 根据skill信息，生成skill_list
        for total_time in range(10, max_time + step, step):
            for stone_set in stone_set_list:
                skill_cdr_info = self._create_skill_cdr_info(skill_list=skill_list, skill_info=skill_info,
                                                             stone_set=stone_set, stone_skill_info=stone_skill_info,
                                                             cdr_info=cdr_info)
                self.sim(skill_pool=skill_cdr_info, total_time=total_time)


if __name__ == '__main__':
    random.seed(19920125)
    sim = Sim()
    # sim.run(set_file_name='set_0', max_time=60, step=5, records_file_name='无特化技能占比')
    # sim.run(set_file_name='set_1', max_time=60, step=5, records_file_name='无特化技能(雷云护石)占比')
    # sim.run(set_file_name='set_2', max_time=60, step=5, records_file_name='无特化技能(呀呀呀护石)占比')
