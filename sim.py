import json
import os
import random
from itertools import combinations
from typing import List, Dict, Union, Tuple

import pandas as pd
import tqdm
import matplotlib.pyplot as plt

from cdr import SkillCDRInfo, parse_cdr_info
from skill import Skill, SkillQueue

DATA_PATH = 'data'


class SkillStatus:
    def __init__(self, skill_info: Dict):
        # {"炸热":{"rest_cd":0.4,"cnt":1}}
        self._skill_status_map = self._init_status_map(skill_info)
        self._skill_cdr_info = skill_info

    def _init_status_map(self, skill_info: Dict):
        result = {}
        for skill_name in skill_info:
            case = {'res_cd': 0.0, "cnt": 0}
            result[skill_info[skill_name].skill.name] = case
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
                result[res_cd].append(skill_name)
        return result

    def start_cooling_down(self, skill_name: str, cd: float):
        self._skill_status_map[skill_name]['res_cd'] = cd

    def add_skill_cnt(self, skill_name: str, cnt):
        self._skill_status_map[skill_name]['cnt'] += cnt
        return self._skill_status_map[skill_name]['cnt']


class Sim:

    def __init__(self, bias: Union[float, str] = 1, human_refletion=0.1, debug=False):
        self._bias = bias
        self._human_refletion = human_refletion
        self._debug = debug

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
        with open(f'{DATA_PATH}/{set_file_name}/skill_info.json', 'r', encoding='utf_8') as f:
            skill_info = json.load(f)

        with open(f'{DATA_PATH}/{set_file_name}/cdr_info.json', 'r', encoding='utf_8') as f:
            cdr_info = json.load(f)

        with open(f'{DATA_PATH}/{set_file_name}/stone_skill_info.json', 'r', encoding='utf_8') as f:
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
        cd = skill_cdr.get_final_cd(cnt)

        # 更新该技能的cd状态
        real_cd = skill.cast_time + cd - skill.during
        skill_status.start_cooling_down(skill.name, real_cd)

        # 返回本次执行技能的耗时，需要同时考虑cast 和 during
        return skill.cast_time + skill.during

    def _get_a_skill(self, skill_status: SkillStatus):
        aval_skills = skill_status.find_almost_available_skills()
        wait_time = list(aval_skills.keys())[0]
        skills = aval_skills[wait_time]
        if len(skills) == 1:
            return wait_time, skills[0]
        else:
            return wait_time, random.choice(skills)

    @staticmethod
    def _force_process(last_skill_force_info: Skill, current_skill: Skill) -> float:
        if last_skill_force_info and last_skill_force_info.force_next_skill_time:
            if current_skill.name in last_skill_force_info.force_next_skill_time:
                force_time = last_skill_force_info.force_next_skill_time[current_skill.name]
                reduce_time = last_skill_force_info.cast_time + last_skill_force_info.during - force_time
                return reduce_time
            else:
                return 0.0
        else:
            return 0.0

    def sim_with_random(self, skill_pool: Dict[str, SkillCDRInfo], total_time: float):
        skill_status = self._create_skill_status(skill_pool)
        time_line = 0
        force_skill_info = None

        skill_queue = []
        while True:
            # 随机选择一个技能
            wait_time, skill_name = self._get_a_skill(skill_status)
            skill_cdr = skill_pool[skill_name]

            # 判断是否为柔化技能
            force_time_reduce = self._force_process(force_skill_info, skill_cdr.skill)

            # 执行技能
            action_time = self._action(skill_cdr, skill_status)

            # 判断执行完这个技能，是否会超过time line限制
            past_time = - force_time_reduce + wait_time + self._human_refletion + action_time
            if time_line + past_time > total_time - self._bias:
                break

            # 更新时间轴
            time_line = time_line + past_time

            # 更新所有技能的cd状态，以供下一次循环时使用
            skill_status.cooling_down(past_time, skill_name)

            # 更新柔化技能信息
            force_skill_info = skill_cdr.skill

            if self._debug:
                if force_time_reduce:
                    print(
                        f'本次模拟，柔化释放技能【{skill_name}】, wait_time:{wait_time}, action_time:{action_time}, '
                        f'force_time:{force_time_reduce}, human reflection:{self._human_refletion}, time line: {time_line}')
                else:
                    print(
                        f'本次模拟，释放技能【{skill_name}】, wait_time:{wait_time}, action_time:{action_time}, '
                        f'human reflection:{self._human_refletion}, time line: {time_line}')
            skill_queue.append(skill_cdr.skill)

        return SkillQueue(skill_queue, total_time)

    def sim(self, epochs, skill_pool, total_time):
        max_skill_queue = {'damage': 0, 'skill_queue': None}
        for i in tqdm.tqdm(range(epochs), desc='开始进行最优技能模拟'):
            if self._debug:
                print('---------------------------------------------')

            skill_queue = self.sim_with_random(skill_pool, total_time)
            damage = skill_queue.compute_total_damage()
            if damage > max_skill_queue['damage']:
                max_skill_queue['damage'] = damage
                max_skill_queue['skill_queue'] = skill_queue

            if self._debug:
                print('---------------------------------------------')
                print()

        return max_skill_queue

    def run(self, epochs, set_file_name, stone_sets, skill_list, time_range, step):
        skill_info, stone_skill_info, cdr_info = self._read_set_file(set_file_name)

        # 先根据护石信息，生成护石sets
        stone_set_list = self._get_stone_sets(stone_sets)

        # 根据skill信息，生成skill_list
        for total_time in range(time_range[0], time_range[1] + step, step):
            for stone_set in stone_set_list:
                skill_cdr_info = self._create_skill_cdr_info(skill_list=skill_list, skill_info=skill_info,
                                                             stone_set=stone_set, stone_skill_info=stone_skill_info,
                                                             cdr_info=cdr_info)
                best_skill_queue = self.sim(epochs, skill_pool=skill_cdr_info, total_time=total_time)
                print(f'当前搭配，护石组合: {json.dumps(stone_set, ensure_ascii=False)}, 测试时长: {total_time}')
                print('当前搭配最高伤害的技能序列:',
                      json.dumps([i.name for i in best_skill_queue['skill_queue'].list], ensure_ascii=False))
                print('当前搭配最高伤害的技能伤害:',
                      json.dumps(best_skill_queue['skill_queue'].compute_damage_by_skill(), ensure_ascii=False))
                print('当前搭配最高伤害的技能伤害（总）:', best_skill_queue['skill_queue'].compute_total_damage())



if __name__ == '__main__':
    random.seed(19920125)
    sim = Sim(debug=False)
    sim.run(epochs=100000, set_file_name='basic_set',
            stone_sets=['炸热', '雷云', '呀呀呀', '不动'],
            skill_list=['邪光', '波爆', '小冰', '小火', '无双', '炸热',
                        '不动', '呀呀呀', '雷云', '无为法', '2觉', '3觉'],
            time_range=(40, 40),
            step=5)
    # sim.run(set_file_name='set_0', max_time=60, step=5, records_file_name='无特化技能占比')
    # sim.run(set_file_name='set_1', max_time=60, step=5, records_file_name='无特化技能(雷云护石)占比')
    # sim.run(set_file_name='set_2', max_time=60, step=5, records_file_name='无特化技能(呀呀呀护石)占比')
