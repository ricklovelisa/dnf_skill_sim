import json
import random
from itertools import combinations, permutations
from typing import List, Dict, Union, Tuple

import tqdm

from core.skill.action import SkillStatus, SkillAction, SkillSet
from core.skill.definition import Skill
from core.skill.queue import SkillQueue
from search import Search

DATA_PATH = '../../data'


class Sim:

    def __init__(self, bias: Union[float, str] = 1, human_refletion=0.1, debug=False):
        self._bias = bias
        self._human_refletion = human_refletion
        self._debug = debug
        self._search = Search()

    # def run_with_time(self, skill_dict: Dict, cdr_info_json: Dict, time: int):
    #     # 先根据skill list和cdr_info_json生成对应技能的cdr
    #     result = parse_cdr_info(skill_dict, cdr_info_json)
    #
    #     # 根据skill_list和cdr_info生成每个技能的次数
    #     skill_apl = []
    #     for cdr_info in result:
    #         # print("=======================================")
    #         # print(cdr_info.skill.detail)
    #         time_cost = 0
    #         times = 0
    #         while True:
    #             if time_cost + 2 >= time:
    #                 break
    #             # print("++++++++++++++++++++++++++++++++++++++++++++++++++")
    #             times += 1
    #             real_cd = cdr_info.get_final_cd(times)
    #             time_cost += real_cd
    #             # print(f'time cost: {time_cost}')
    #             # print("++++++++++++++++++++++++++++++++++++++++++++++++++")
    #         # print("=======================================")
    #         # print()
    #         skill_apl.append(
    #             {'name': cdr_info.skill.name, 'n': times, 'damage': cdr_info.skill.get_final_damage(time, times)})
    #     # print(json.dumps(skill_apl, ensure_ascii=False, indent=4))
    #     return skill_apl

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
    def _create_skill_status(skill_pool: Dict) -> SkillStatus:
        return SkillStatus(skill_pool)

    @staticmethod
    def _create_skill(skill_list: List[str], skill_info: Dict, stone_set: List, stone_skill_info: Dict,
                      fuwen_info: Dict[str, Dict[str, int]], cdr_and_damage_info: Dict):
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
            skill.update_damage(cdr_and_damage_info['damage_info'], fuwen_info)
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

    def sim_best_skill_queue_by_search(self, start_skill_set: SkillSet, skill_action: SkillAction,
                                       skill_info: Dict[str, Skill], is_op: bool, total_time: float,
                                       search_strategy: str) -> SkillQueue:
        skill_status = self._create_skill_status(skill_info)
        time_line = 0

        skill_queue = []
        # 执行第一个技能
        _, _, _ = start_skill_set.compute_past_and_damage(is_op, skill_status)
        time_line = start_skill_set.execution(time_line, skill_status)
        skill_queue.extend(start_skill_set.skills)

        # 开始进行技能模拟
        while True:
            res_time = total_time - self._bias - time_line
            if res_time <= 0:
                break
            print(f'----------------------- start set: {start_skill_set} ---------------------------')
            # 根据search_strategy，寻找下一个最优的skill_set
            actions = skill_action.return_skill_set_with_skill_status(skill_status)
            next_best_skill = self._search.search_best_skill(search_strategy, actions, res_time)
            if next_best_skill is None:
                break
            print('当前time_line:', time_line, ', res_time:', res_time)
            print('当前skill_status:', skill_status.detail)
            print('下一个最优技能组是:', [x.detail for x in next_best_skill.skills])
            skill_queue.extend(next_best_skill.skills)
            # print('next_best_skill', [x.name for x in next_best_skill.skills])
            before_time_line = time_line
            time_line = next_best_skill.execution(time_line, skill_status)
            print('past:', time_line - before_time_line)
            print('执行最优技能后的skill_status:', skill_status.detail)
            print('--------------------------------------------------')
            print()

        print([x.name for x in skill_queue])
        return SkillQueue(skill_queue, total_time)

    def sim_best_skill_queue_by_random(self, skill_info: Dict[str, Skill], is_op: bool, total_time: float):
        skill_status = self._create_skill_status(skill_info)
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

        return SkillQueue(skill_queue, total_time)

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

        # 生成skill_action
        skill_action = SkillAction(skill_info=skill_info, human_reflection=self._human_refletion, is_op=is_op)
        # print('skill_action: ', skill_action)

        # 将每个技能组作为第一个技能，进行后续的搜索和模拟
        for skill_set in skill_action.skill_sets:
            skill_queue = self.sim_best_skill_queue_by_search(start_skill_set=skill_set, skill_action=skill_action,
                                                              is_op=is_op, total_time=total_time, skill_info=skill_info,
                                                              search_strategy=search_strategy)

            damage = skill_queue.compute_total_damage()
            print('start_set', skill_set, damage)
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

    def run(self, epochs: int, set_file_name: str, stone_sets: List, skill_sets: List, choice_type: str,
            time_range: Tuple, step: int, op_info: List[bool], fuwen_info_list: Dict = None):
        skill_info, stone_skill_info, cdr_and_damage_info = self._read_set_file(set_file_name)

        # 先根据护石信息，生成护石sets
        stone_set_list = self._get_stone_sets(stone_sets)

        max_result = {'damage': 0}
        # 根据skill信息，生成skill_list
        for total_time in range(time_range[0], time_range[1] + step, step):
            for is_op in op_info:
                for stone_set in stone_set_list:
                    # 根据护石组合，生成符文组合：
                    if not fuwen_info_list:
                        fuwen_info_list = self._create_fuwen_skill_set(stone_set)
                    for fuwen_info in fuwen_info_list:
                        # print('fuwen_info', fuwen_info)
                        for cdr_damage in cdr_and_damage_info:
                            skill_list = self._create_skill(skill_list=skill_sets, skill_info=skill_info,
                                                            stone_set=stone_set, stone_skill_info=stone_skill_info,
                                                            fuwen_info=fuwen_info, cdr_and_damage_info=cdr_damage)
                            best_skill_queue = self.sim(epochs=epochs, choice_type=choice_type, skill_info=skill_list,
                                                        total_time=total_time, is_op=is_op, search_strategy='res_cd')
                            # print(f'当前搭配，护石组合: {json.dumps(stone_set, ensure_ascii=False)}, 测试时长: {total_time}')
                            # print(f'当前搭配最高，是否手搓:{is_op}')
                            # print('当前搭配最高伤害的迭代数:', best_skill_queue['epoch'])
                            # print('当前搭配最高伤害的技能序列:',
                            #       json.dumps([i.name for i in best_skill_queue['skill_queue'].list], ensure_ascii=False))
                            # print('当前搭配最高伤害的技能伤害:',
                            #       json.dumps(best_skill_queue['skill_queue'].compute_damage_by_skill(), ensure_ascii=False))
                            # print('当前搭配最高伤害的技能伤害（总）:', best_skill_queue['skill_queue'].compute_total_damage())
                            # print()

                            if best_skill_queue['damage'] > max_result['damage']:
                                max_result['damage'] = best_skill_queue['damage']
                                max_result['skill_queue'] = best_skill_queue['skill_queue']
                                max_result['stone_set'] = stone_set
                                max_result['is_op'] = is_op
                                max_result['fuwen_info'] = fuwen_info
                                max_result['cdr_damage'] = cdr_damage

            print(f'测试时长: {total_time}')
            print(f'伤害最高的装备组合: {json.dumps(max_result["cdr_damage"], ensure_ascii=False)}')
            print(
                f'伤害最高的搭配，护石组合: {json.dumps(max_result["stone_set"], ensure_ascii=False)}')
            print(f'伤害最高的搭配，符文组合: {json.dumps(max_result["fuwen_info"], ensure_ascii=False)}')
            print(f'伤害最高搭配，是否手搓:{max_result["is_op"]}')
            print('伤害最高的搭配的技能序列:',
                  json.dumps([i.name for i in max_result['skill_queue'].list], ensure_ascii=False))
            print('伤害最高的搭配的技能伤害:',
                  json.dumps(max_result['skill_queue'].compute_damage_by_skill(), ensure_ascii=False))
            print('伤害最高的搭配的技能伤害（总）:', max_result['skill_queue'].compute_total_damage())
            print()


if __name__ == '__main__':
    # random.seed(19920125)
    sim = Sim(debug=False)
    sim.run(epochs=299999, set_file_name='test_sim_set',
            stone_sets=['炸热', '呀呀呀', '不动'],
            skill_sets=['邪光', '波爆', '小冰', '小火', '无双', '炸热',
                        '不动', '呀呀呀', '雷云', '无为法', '2觉', '3觉'],
            choice_type='search',
            time_range=(40, 40),
            fuwen_info_list=[{"red": {"呀呀呀": 3}, "purple": {"不动": 3}, "blue": {"炸热": 3}}],
            step=5,
            op_info=[True])
    # sim.run(set_file_name='set_0', max_time=60, step=5, records_file_name='无特化技能占比')
    # sim.run(set_file_name='set_1', max_time=60, step=5, records_file_name='无特化技能(雷云护石)占比')
    # sim.run(set_file_name='set_2', max_time=60, step=5, records_file_name='无特化技能(呀呀呀护石)占比')
