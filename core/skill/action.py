import json
import random
from abc import abstractmethod
from typing import Dict, Union, List

from core.skill.definition import Skill, SkillSet, SkillQueue


class SkillStatus:
    def __init__(self, skill_info: Dict, init_cnt: Dict = None):
        # {"炸热":{"res_cd":0.4,"cnt":1}}
        self._skill_status_map = self._init_status_map(skill_info)
        if init_cnt:
            for skill_name, cnt in init_cnt.items():
                self._skill_status_map[skill_name]['cnt'] = cnt

    def _init_status_map(self, skill_info: Dict) -> Dict[str, Dict[str, Union[float, int]]]:
        result = {}
        for skill_name in skill_info:
            case = {'res_cd': 0.0, "cnt": 0}
            result[skill_info[skill_name].name] = case
        return result

    # def get_status_by_name(self, skill_name: str):
    #     skill_status = self._skill_status_map[skill_name]
    #     return skill_status
    #
    # def get_all_status(self):
    #     return self._skill_status_map

    @property
    def detail(self):
        return json.dumps(self._skill_status_map, ensure_ascii=False)

    def cooling_down(self, ts: float, except_skill_name_list: List[str]):
        for skill_name in self._skill_status_map:
            if skill_name not in except_skill_name_list:
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

    def get_skill_cnt(self, skill_name: str):
        return self._skill_status_map[skill_name]['cnt']

    def add_skill_cnt(self, skill_name: str, cnt) -> int:
        self._skill_status_map[skill_name]['cnt'] += cnt
        return self._skill_status_map[skill_name]['cnt']

    def get_skill_res_cd(self, skill_name):
        return self._skill_status_map[skill_name]['res_cd']


# class SkillAction:
#
#     def __init__(self, skill_info: Dict[str, Skill], human_reflection: float, is_op: bool):
#         self._human_reflection = human_reflection
#         self._is_op = is_op
#         self._skill_list_with_force_skill_set: List[SkillSet] = self._make_force_set(skill_info)
#
#     def __str__(self):
#         result = []
#         for skill_set in self._skill_list_with_force_skill_set:
#             result.append([x.name for x in skill_set.skills])
#         return json.dumps({'human_reflection': self._human_reflection, 'is_op': self._is_op,
#                            'skill_set': result}, ensure_ascii=False)
#
#     def __repr__(self):
#         return self.__str__()
#
#
#
#     @property
#     def skill_sets(self):
#         return self._skill_list_with_force_skill_set
#
#     def return_skill_set_with_skill_status(self, skill_status: SkillStatus):
#         """ 根据实际的skill_status，计算每个技能的past_time，和实际伤害、各个技能的实际秒伤
#
#         """
#
#         result = []
#         for skill_set in self._skill_list_with_force_skill_set:
#             past_time, damage, dps, next_cd = skill_set.compute_past_and_damage(self._is_op, skill_status)
#             # 获取这个技能组的max(res_cd)作为 res_cd,
#             max_res_cd = 0
#             for skill in skill_set.skills:
#                 max_res_cd = max(skill_status.get_skill_res_cd(skill.name), max_res_cd)
#             # 获取技能组中每个技能的当前使用次数
#             curr_cnt = [skill_status.get_skill_cnt(x.name) for x in skill_set.skills]
#             result.append(
#                 {'skill_set': skill_set, 'res_cd': max_res_cd, 'past_time': past_time, 'damage': damage, 'dps': dps,
#                  'curr_cnt': curr_cnt, 'next_cd': next_cd})
#
#         return result


class SkillSetAction:

    def __init__(self, is_op: bool, human_reflection: float, skill_set: SkillSet):
        self._is_op = is_op
        self._human_reflection = human_reflection
        self._skill_set = skill_set
        self._queue = None

    @abstractmethod
    def compute_past_and_damage(self, skill_status: SkillStatus):
        """ 计算该技能组根据实际skill_status下的past_time、总伤、秒伤的和

        :param is_op:
        :param skill_status:
        :return: past_time, total_damage
        """
        pass

    @abstractmethod
    def execution(self, skill_queue: SkillQueue, skill_status: SkillStatus):
        """ 执行，更新skill_status中的技能cd和技能数，并返回时间轴

        :return:
        """
        pass

    @property
    def queue(self):
        return self._queue


class SingleSkillAction(SkillSetAction):
    """ 单技能Set，等价于单个技能
    """

    def __init__(self, is_op: bool, human_reflection: float, skill_set: SkillSet):
        # 本次技能组整体耗时
        super().__init__(is_op, human_reflection, skill_set)
        # self._past_time = None
        # # 本次技能组技能释放完后的剩余cd数
        # self._res_cd = None
        # # 本次技能组技能增加技能次数
        # self._skill_cnt = None

    def compute_past_and_damage(self, skill_status: SkillStatus):
        skill_queue = []
        skill_time_line = []
        res_cd_list = []

        skill = self._skill_set.skills[0]
        skill_queue.append(skill)

        res_cd = skill_status.get_skill_res_cd(skill.name)
        # 释放本次技能组需要的总时间，本技能的剩余cd，人的反应，以及本技能的action_time
        past_time = res_cd + self._human_reflection + skill.action_time
        skill_time_line.append(past_time)

        # 记录本次技能的技能次数和技能剩余cd
        skill_cnt = skill_status.get_skill_cnt(skill.name) + 1
        next_cd = skill.get_final_cd(self._is_op, skill_cnt)
        res_cd = next_cd - skill.during
        res_cd_list.append(res_cd)
        self._queue = SkillQueue(skill_queue=skill_queue, skill_time_line=skill_time_line, res_cd_list=res_cd_list)

        # return past_time, skill.damage, skill.damage / next_cd, next_cd

    def execution(self, executed_skill_queue: SkillQueue, skill_status: SkillStatus):
        # 将本次技能组的queue合并入executed_skill_queue
        executed_skill_queue.append(self._queue)

        # 更新skill_status信息
        for info in self._queue.loop_info:
            skill_name = info.skill.name
            skill_res_cd = info.skill_res_cd
            skill_status.start_cooling_down(skill_name, skill_res_cd)

            skill_status.add_skill_cnt(skill_name, 1)

        total_past_time = self._queue.
        skill_status.cooling_down(self._past_time, )

        # this_skill_name = self._skill_set[0].name
        # # 本次技能组的技能进入cd，res_cd是实际剩余的cd数
        # skill_status.start_cooling_down(this_skill_name, self._res_cd)
        #
        # # 本次技能组的技能技能数
        # add_cnt = self._skill_cnt - skill_status.get_skill_cnt(this_skill_name)
        # skill_status.add_skill_cnt(this_skill_name, add_cnt)
        #
        # # 其他技能进行cd，时间是本次技能的past_time
        # skill_status.cooling_down(self._past_time, [this_skill_name])

        # 最后返回整体的time_line
        # return time_line + self._past_time

    def queue(self):
        return self._queue


class ForcedSkillSetAction(SkillSetAction):
    """ 多个有柔化技能的组合，在进行相关计算的时候

    """

    def __init__(self, is_op: bool, human_reflection: float, skill_set: SkillSet):
        super().__init__(is_op, human_reflection, skill_set)
        self._skill_status = {}
        # 本次技能组整体耗时
        self._past_time = 0

    def compute_past_and_damage(self, skill_status: SkillStatus):
        # 执行技能组，并返回该技能组的总体past_time, total_damage
        # past_time = 各个技能的wait_time（也就是res_cd） + 前n-1个柔化time + 最后一个技能的action_time
        total_damage = 0
        total_dps = 0
        max_next_cd = 0
        for i in range(len(self._skill_set)):
            skill = self._skill_set[i]

            # 该技能伤害，并汇总
            total_damage = total_damage + skill.damage

            # 获取本次技能的通用信息
            res_cd = skill_status.get_skill_res_cd(skill.name)
            skill_cnt = skill_status.get_skill_cnt(skill.name) + 1
            next_cd = skill.get_final_cd(is_op, skill_cnt)

            # 该技能组的秒伤汇总
            total_dps = total_dps + skill.damage / next_cd

            if i == 0:  # 如果是第一个技能，则直接加上第一个技能的剩余cd，反应速度
                self._past_time = self._past_time + res_cd + self._human_reflection

            else:  # 如果不是第一个技能，则判断第一个技能释放完后需要等待下一个技能释放的时间
                force_time = self._skill_set[i - 1].force_next_skill_time[skill.name]
                real_res_cd = max(force_time, res_cd - self._past_time)
                self._past_time = self._past_time + real_res_cd + self._human_reflection

            # 记录下本次技能开始计算cd的时间，最后用next_cd - (完整的past_time - start_cd_time)，就是该技能剩余的cd数
            self._skill_status[skill.name] = {'start_cd_time': self._past_time + skill.cast_time,
                                              'next_time_cd': next_cd, 'skill_cnt': skill_cnt}

            # 用技能组中的最大的next_cd作为整体的这个技能组的next_cd
            max_next_cd = max(max_next_cd, next_cd)
        return self._past_time, total_damage, total_dps, max_next_cd

    def execution(self, skill_queue: SkillQueue, skill_status: SkillStatus):
        # 根据每个技能情况，分别设置技能的res_cd
        for skill_name, status_info in self._skill_status.items():
            # 用完整的past_time - start_cd_time就是该技能走过的时间，然后再用下一次的实际cd-该值就是实际剩余cd
            skill_past = self._past_time - self._skill_status[skill_name]['start_cd_time']
            res_cd = self._skill_status[skill_name]['next_time_cd'] - skill_past

            # 本次技能组的技能进入cd，res_cd是实际剩余的cd数
            skill_status.start_cooling_down(skill_name, res_cd)

            # 本次技能组的技能技能数
            add_cnt = self._skill_status[skill_name]['skill_cnt'] - skill_status.get_skill_cnt(skill_name)
            skill_status.add_skill_cnt(skill_name, add_cnt)

        # 其他技能进行cd，时间是本次技能的past_time
        skill_status.cooling_down(self._past_time, [x.name for x in self._skill_set])

        # 最后返回整体的time_line
        # return time_line + self._past_time

    def queue(self):
        return self._queue
