import json
import random
from datetime import datetime
from itertools import combinations, permutations
from typing import List, Dict, Union, Tuple

import pandas as pd
import tqdm

from core.skill.action import SkillStatus, SkillSet, SkillSetAction
from core.skill.definition import Skill, make_force_set, SkillQueue
from core.skill.queue import SkillQueue as OldSkillQueue
from search import Search

DATA_PATH = '../../data'


class Sim:

    def __init__(self, max_bias: Union[float, str] = 1, human_refletion=0.1, debug=False):
        self._max_bias = max_bias
        self._human_refletion = human_refletion
        self._debug = debug
        self._search = Search()
        self._bias = None

    def _get_bias(self, total_time):
        return min(self._max_bias, total_time / 40)

    def _read_set_file(self, set_file_name):
        with open(f'{DATA_PATH}/{set_file_name}/skill_info.json', 'r', encoding='utf_8') as f:
            skill_info = json.load(f)

        # with open(f'{DATA_PATH}/{set_file_name}/cdr_info.json', 'r', encoding='utf_8') as f:
        #     cdr_info = json.load(f)

        with open(f'{DATA_PATH}/{set_file_name}/stone_skill_info.json', 'r', encoding='utf_8') as f:
            stone_skill_info = json.load(f)

        with open(f'{DATA_PATH}/{set_file_name}/cdr_and_damage_info.jsonl', 'r', encoding='utf_8') as f:
            cdr_and_damage_info = []
            for line in f.readlines():
                cdr_and_damage_info.append(json.loads(line))

        # with open(f'{DATA_PATH}/{set_file_name}/damage_rate.json', 'r', encoding='utf_8') as f:
        #     damage_rate_info = json.load(f)
        # return skill_info, stone_skill_info, cdr_info, damage_rate_info
        return skill_info, stone_skill_info, cdr_and_damage_info

    def _get_stone_sets(self, stone_sets: List[str]) -> List[Union[Tuple, List]]:
        if len(stone_sets) > 3:
            return list(combinations(stone_sets, 3))
        else:
            return [stone_sets]

    @staticmethod
    def _create_skill(skill_list: List[str], skill_info: Dict, stone_set: List, stone_skill_info: Dict,
                      fuwen_info: Dict[str, Dict[str, int]], cdr_and_damage_info: Dict, skill_level_damage_rate: Dict):
        fianl_skill_info = {}
        for skill_name in skill_list:
            # 获取技能信息
            # 如果技能有护石，则更新护石信息
            raw_info = skill_info[skill_name]
            if skill_name in stone_set and skill_name in stone_skill_info:
                stone_info = stone_skill_info[skill_name]
                skill = Skill.create_skill_with_stone(skill_name, raw_info, stone_info)
            else:
                skill = Skill(skill_name, raw_info)

            skill.add_cdr_info(cdr_and_damage_info['cdr_info'], fuwen_info)
            skill.update_damage(cdr_and_damage_info['damage_info'], fuwen_info, skill_level_damage_rate)
            fianl_skill_info[skill_name] = skill
        return fianl_skill_info

    @staticmethod
    def _action(skill: Skill, skill_status: SkillStatus, is_op):
        # 模拟执行
        # 获取该技能cd
        cnt = skill_status.add_skill_cnt(skill.name, 1)
        cd = skill.get_final_cd(is_op, cnt)
        # print(f'技能: {skill.name}, cd: {cd}, damage: {skill.get_final_damage(40, 1)}')

        # 更新该技能的cd状态
        real_cd = skill.cast_time + cd - skill.during
        skill_status.start_cooling_down(skill.name, real_cd)

        # 返回本次执行技能的耗时，需要同时考虑cast 和 during
        return skill.action_time

    @staticmethod
    def _random_a_skill(skill_status: SkillStatus):
        aval_skill_names = skill_status.find_almost_available_skills()
        wait_time = list(aval_skill_names.keys())[0]
        skill_names = aval_skill_names[wait_time]
        if len(skill_names) == 1:
            return wait_time, skill_names[0]
        else:
            return wait_time, random.choice(skill_names)

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

    @staticmethod
    def read_skill_and_stone_sets():
        with open(f'{DATA_PATH}/skill_and_stone_sets.json', 'r', encoding='utf_8') as f:
            return json.load(f)

    def sim_best_skill_queue_by_search(self, start_skill_set: SkillSet, skill_sets: List[SkillSet],
                                       skill_info: Dict[str, Skill], is_op: bool, total_time: float,
                                       search_strategy: str) -> SkillQueue:
        skill_status = SkillStatus(skill_info)
        # skill_status = SkillStatus(skill_info, {"无为法": 1})

        skill_queue = SkillQueue()
        # 执行第一个技能
        skill_action = SkillSetAction.make(skill_set=start_skill_set, is_op=is_op,
                                           human_reflection=self._human_refletion)
        # 计算并执行
        skill_action.compute_past_and_damage(skill_status).execution(skill_queue, skill_status)

        # 开始进行技能模拟
        while True:
            res_time = total_time - self._bias - skill_queue.past_time
            if res_time <= 0:
                break
            # 根据search_strategy，寻找下一个最优的skill_set
            # 将所有skill_set都封装成skill_action
            skill_actions = [
                SkillSetAction.make(x, is_op, self._human_refletion).compute_past_and_damage(skill_status)
                for x in skill_sets]
            # actions = skill_action.return_skill_set_with_skill_status(skill_status)
            next_best_skill_action = self._search.search_best_skill(search_strategy, skill_actions, skill_status,
                                                                    res_time)
            if next_best_skill_action is None:
                break
            next_best_skill_action.execution(skill_queue, skill_status)

        return skill_queue

    def sim_best_skill_queue_by_random(self, skill_info: Dict[str, Skill], is_op: bool, total_time: float):
        skill_status = SkillStatus(skill_info)
        time_line = 0
        force_skill_info = None

        skill_queue = []
        while True:
            # 随机选择一个技能
            wait_time, skill_name = self._random_a_skill(skill_status)
            skill = skill_info[skill_name]

            # 判断是否为柔化技能
            force_time_reduce = self._force_process(force_skill_info, skill)

            # 执行技能
            action_time = self._action(skill, skill_status, is_op)

            # 判断执行完这个技能，是否会超过time line限制
            past_time = - force_time_reduce + wait_time + self._human_refletion + action_time
            if time_line + past_time > total_time - self._bias:
                break

            # 更新时间轴
            time_line = time_line + past_time

            # 更新所有技能的cd状态，以供下一次循环时使用
            skill_status.cooling_down(past_time, [skill.name])

            # 更新柔化技能信息
            force_skill_info = skill

            if self._debug:
                if force_time_reduce:
                    print(
                        f'本次模拟，柔化释放技能【{skill.name}】, wait_time:{wait_time}, action_time:{action_time}, '
                        f'force_time_reduce:{force_time_reduce}, human reflection:{self._human_refletion}, time line: {time_line}')
                else:
                    print(
                        f'本次模拟，释放技能【{skill.name}】, wait_time:{wait_time}, action_time:{action_time}, '
                        f'human reflection:{self._human_refletion}, time line: {time_line}')
            skill_queue.append(skill)

        return OldSkillQueue(skill_queue, total_time)

    def _random_sim(self, epochs: int, skill_info: Dict[str, Skill], is_op: bool, total_time: int) -> Dict:
        max_skill_queue = {'damage': 0}
        for i in tqdm.tqdm(range(epochs), desc='开始进行最优技能模拟'):
            if self._debug:
                print('---------------------------------------------')

            skill_queue = self.sim_best_skill_queue_by_random(skill_info=skill_info, is_op=is_op, total_time=total_time)

            damage = skill_queue.compute_total_damage()
            if damage > max_skill_queue['damage']:
                max_skill_queue['damage'] = damage
                max_skill_queue['skill_queue'] = skill_queue
                max_skill_queue['epoch'] = i

            if self._debug:
                print('---------------------------------------------')
                print()

        return max_skill_queue

    def _search_sim(self, skill_info: Dict[str, Skill], is_op: bool, total_time: int, search_strategy: str) -> Dict:
        max_skill_queue = {'damage': 0}

        skill_sets = make_force_set(skill_info)
        # print('skill_action: ', skill_action)

        # 将每个技能组作为第一个技能，进行后续的搜索和模拟
        for skill_set in skill_sets:
            # if len(skill_set.skills) == 1:
            #     continue
            # print(f'============================== start set: {skill_set} ==============================')
            skill_queue = self.sim_best_skill_queue_by_search(start_skill_set=skill_set, is_op=is_op,
                                                              skill_sets=skill_sets, total_time=total_time,
                                                              skill_info=skill_info, search_strategy=search_strategy)

            damage = skill_queue.compute_total_damage(total_time=total_time)
            if damage > max_skill_queue['damage']:
                max_skill_queue['damage'] = damage
                max_skill_queue['skill_queue'] = skill_queue

        return max_skill_queue

    def sim(self, epochs: int, skill_info: Dict[str, Skill], choice_type: str, is_op: bool, total_time: int,
            search_strategy: str = None):
        if choice_type == 'random':
            return self._random_sim(epochs=epochs, skill_info=skill_info, is_op=is_op, total_time=total_time)

        if choice_type == 'search':
            return self._search_sim(skill_info=skill_info, is_op=is_op, total_time=total_time,
                                    search_strategy=search_strategy)

    @staticmethod
    def _create_fuwen_skill_set(fuwen_skill_sets: List):
        colors = ['red', 'blue', 'purple']
        # 将每个技能都复制3个
        fuwen_skill_pool = [x for x in fuwen_skill_sets for i in range(3)]

        fuwen_result = []
        for fuwen_skill_set in set(combinations(fuwen_skill_pool, 3)):
            # 求该set的排列，并与color 11对应生成符文组合
            for fuwen_set in set(permutations(fuwen_skill_set, 3)):
                case = {}
                for i in range(len(colors)):
                    color = colors[i]
                    skill = fuwen_set[i]
                    case[color] = {skill: 3}
                fuwen_result.append(case)

        return fuwen_result

    def run(self, cls: str, epochs: int, set_file_name: str, stone_and_skill_sets: Dict, choice_type: str,
            time_range: Tuple, step: int, op_info: List[bool], fuwen_info_list: Dict = None):
        skill_info, stone_skill_info, cdr_and_damage_info = self._read_set_file(set_file_name)

        # skill_sys
        skill_sys_name = stone_and_skill_sets['name']
        stone_sets = stone_and_skill_sets['stone_sets']
        skill_sets = stone_and_skill_sets['skill_sets']
        skill_level_damage_rate = None
        if 'skill_level_damage_rate' in stone_and_skill_sets:
            skill_level_damage_rate = stone_and_skill_sets['skill_level_damage_rate']

        # 先根据护石信息，生成护石sets
        stone_set_list = self._get_stone_sets(stone_sets)

        # 生成所有待计算的组合
        all_sim_sets = []
        for is_op in op_info:
            for stone_set in stone_set_list:
                if not fuwen_info_list:
                    fuwen_info_list = self._create_fuwen_skill_set(stone_set)
                for fuwen_info in fuwen_info_list:
                    # print('fuwen_info', fuwen_info)
                    for cdr_damage in cdr_and_damage_info:
                        all_sim_sets.append((is_op, stone_set, fuwen_info, cdr_damage))

        total_sim_result = {'时间轴': [], '是否手搓': [], '护石组合': [], '符文组合': [], 'cdr配装信息': [],
                            '技能队列': [], '技能伤害': [], '总伤': []}
        # 根据skill信息，生成skill_list
        time_steps = range(time_range[0], time_range[1] + step, step)
        total_loop_cnt = len(time_steps) * len(all_sim_sets)
        with tqdm.tqdm(total=total_loop_cnt, desc=f'{skill_sys_name} {set_file_name} 进行组合模拟') as pbar:
            for total_time in time_steps:
                # 生成本次total_time下的bias
                self._bias = self._get_bias(total_time)
                max_result = {'damage': 0}
                for is_op, stone_set, fuwen_info, cdr_damage in all_sim_sets:
                    skill_list = self._create_skill(skill_list=skill_sets, skill_info=skill_info, stone_set=stone_set,
                                                    stone_skill_info=stone_skill_info, fuwen_info=fuwen_info,
                                                    cdr_and_damage_info=cdr_damage,
                                                    skill_level_damage_rate=skill_level_damage_rate)
                    best_skill_queue = self.sim(epochs=epochs, choice_type=choice_type, skill_info=skill_list,
                                                total_time=total_time, is_op=is_op, search_strategy='res_cd')
                    total_sim_result['时间轴'].append(total_time)
                    total_sim_result['是否手搓'].append(is_op)
                    total_sim_result['护石组合'].append(json.dumps(stone_set, ensure_ascii=False))
                    total_sim_result['符文组合'].append(json.dumps(fuwen_info, ensure_ascii=False))
                    total_sim_result['cdr配装信息'].append(json.dumps(cdr_damage, ensure_ascii=False))
                    total_sim_result['技能队列'].append(best_skill_queue['skill_queue'].json)
                    total_sim_result['技能伤害'].append(
                        json.dumps(best_skill_queue['skill_queue'].compute_damage_by_skill(total_time),
                                   ensure_ascii=False))
                    total_sim_result['总伤'].append(best_skill_queue['skill_queue'].compute_total_damage(total_time))
                    # print(
                    #     f'当前搭配，护石组合: {json.dumps(stone_set, ensure_ascii=False)}, 测试时长: {total_time}')
                    # print(f'当前搭配，符文组合: {json.dumps(fuwen_info, ensure_ascii=False)}')
                    # print(f'当前搭配，配装信息:{json.dumps(cdr_damage, ensure_ascii=False)}')
                    # print(f'当前搭配最高，是否手搓:{is_op}')
                    # # print('当前搭配最高伤害的迭代数:', best_skill_queue['epoch'])
                    # print('当前搭配最高伤害的技能序列:',
                    #       json.dumps([i.name for i in best_skill_queue['skill_queue'].list],
                    #                  ensure_ascii=False))
                    # print('当前搭配最高伤害的技能伤害:',
                    #       json.dumps(best_skill_queue['skill_queue'].compute_damage_by_skill(),
                    #                  ensure_ascii=False))
                    # print('当前搭配最高伤害的技能伤害（总）:',
                    #       best_skill_queue['skill_queue'].compute_total_damage())
                    # print()

                    if best_skill_queue['damage'] > max_result['damage']:
                        max_result['damage'] = best_skill_queue['damage']
                        max_result['skill_queue'] = best_skill_queue['skill_queue']
                        max_result['stone_set'] = stone_set
                        max_result['is_op'] = is_op
                        max_result['fuwen_info'] = fuwen_info
                        max_result['cdr_damage'] = cdr_damage
                    pbar.update(1)

                tqdm.tqdm.write(f'\n测试时长: {total_time}')
                tqdm.tqdm.write(f'伤害最高的装备组合: {json.dumps(max_result["cdr_damage"], ensure_ascii=False)}')
                tqdm.tqdm.write(
                    f'伤害最高的搭配，护石组合: {json.dumps(max_result["stone_set"], ensure_ascii=False)}')
                tqdm.tqdm.write(f'伤害最高的搭配，符文组合: {json.dumps(max_result["fuwen_info"], ensure_ascii=False)}')
                tqdm.tqdm.write(f'伤害最高搭配，是否手搓: {max_result["is_op"]}')
                tqdm.tqdm.write(
                    f'伤害最高的搭配的技能序列: {max_result["skill_queue"].json}')
                tqdm.tqdm.write(
                    f'伤害最高的搭配的技能伤害: {json.dumps(max_result["skill_queue"].compute_damage_by_skill(total_time), ensure_ascii=False)}')
                tqdm.tqdm.write(
                    f'伤害最高的搭配的技能伤害（总）: {max_result["skill_queue"].compute_total_damage(total_time)}')
                tqdm.tqdm.write('')

        now = datetime.now()
        pd.DataFrame(total_sim_result).to_csv(
            f'../../records/{skill_sys_name}_{set_file_name}_record_{now.strftime("%Y_%m_%d_%H_%M_%S")}.csv',
            encoding='utf_8_sig')

    def run_from_config(self, cls, epochs, choice_type, time_range, step, op_info):
        skill_and_stone_sets = sim.read_skill_and_stone_sets()
        for skill_and_stone_set in skill_and_stone_sets:
            for set_file_name in ['实际有的配装', '完美自定义配装']:
            # for set_file_name in ['实际有的配装']:
            # for set_file_name in ['完美自定义配装']:
                self.run(cls=cls, epochs=epochs, set_file_name=set_file_name,
                         choice_type=choice_type, time_range=time_range,
                         stone_and_skill_sets=skill_and_stone_set, step=step, op_info=op_info)


if __name__ == '__main__':
    random.seed(19920125)
    sim = Sim(debug=False)
    sim.run_from_config(cls='阿修罗', epochs=299999, choice_type='search', time_range=(20, 60), step=5,
                        op_info=[True, False])
    # sim.run(cls='阿修罗', epochs=299999, set_file_name='test_sim_set',
    #         choice_type='search', time_range=(40, 40),
    #         stone_and_skill_sets={"name": "不动加点", "stone_sets": ["炸热", "不动", "呀呀呀", "雷云"],
    #                               "skill_sets": ["邪光", "波爆", "小冰", "小火", "无双", "炸热", "不动", "呀呀呀",
    #                                              "雷云", "无为法", "2觉", "3觉"]}
    #         , step=5, op_info=[True]
    #         # fuwen_info_list=[{"red": {"呀呀呀": 3}, "purple": {"不动": 3}, "blue": {"炸热": 3}}],
    #         # fuwen_info_list=[{"red": {"炸热": 3}, "blue": {"炸热": 3}, "purple": {"炸热": 3}}]
    #         )
