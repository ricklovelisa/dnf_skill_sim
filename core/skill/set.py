import json
from abc import abstractmethod
from typing import List

from core.skill.action import SkillStatus
from core.skill.definition import Skill


class SkillSet:
    """ 该类用于描述一些职业的所有的可执行技能组合，这些组合包括单个技能，以及多个相互间可柔化技能。

    例如[炸热、无双、不动]或[无为法]

    构建本对象，是为了方便进行针对技能组的数据统计，例如技能组的总伤，总耗时，总dps等
    """

    def __init__(self, human_reflection: float, skill_set: List[Skill]):
        self._skill_set = skill_set
        self._human_reflection = human_reflection

    @abstractmethod
    def compute_past_and_damage(self, is_op: bool, skill_status: SkillStatus):
        """ 计算该技能组根据实际skill_status下的past_time和总伤

        :param is_op:
        :param skill_status:
        :return: past_time, total_damage
        """
        pass

    @abstractmethod
    def execution(self, time_line: float, skill_status: SkillStatus):
        """ 执行，并更新skill_status中的技能cd和技能数

        :return:
        """
        pass

    @staticmethod
    def parse(skill_set: List[Skill], human_reflection=0.1):
        if len(skill_set) == 1:
            return SingleSkill(skill_set=skill_set, human_reflection=human_reflection)
        elif len(skill_set) >= 2:
            return ForcedSkillSet(skill_set=skill_set, human_reflection=human_reflection)
        else:
            raise Exception('skill set长度不能为0')


class SingleSkill(SkillSet):
    """ 单技能Set，等价于单个技能
    """

    def __init__(self, human_reflection: float, skill_set: List[Skill]):
        super().__init__(human_reflection, skill_set)
        self._status_info = {}
        self._past_time = None
        self._res_cd = None

    def compute_past_and_damage(self, is_op: bool, skill_status: SkillStatus):
        skill = self._skill_set[0]
        res_cd = skill_status.get_skill_res_cd(skill.name)
        self._past_time = res_cd + self._human_reflection + skill.action_time

        # 记录本次技能的技能次数和
        skill_cnt = skill_status.get_skill_cnt(skill.name) + 1
        next_skill_res_cd = skill.get_final_cd(is_op, skill_cnt)
        self._status_info[skill.name] = {'past_cd': next_skill_res_cd - skill.during, 'add_cnt': 1}
        return self._past_time, skill.damage

    def execution(self, time_line: float, skill_status: SkillStatus):
        # 本次技能组的技能进入cd，res_cd是实际
        skill_status.start_cooling_down()


class ForcedSkillSet(SkillSet):
    """ 多个有柔化技能的组合，在进行相关计算的时候

    """

    def compute_past_and_damage(self, skill_status: SkillStatus):
        # 执行技能组，并返回该技能组的总体past_time, total_damage
        # past_time = 各个技能的wait_time（也就是res_cd） + 前n-1个柔化time + 最后一个技能的action_time
        # 构建一个字典，用来存储每个技能在本次执行后，实际剩余的cd
        # {'炸热': {'past_cd':0.05, 'cnt':1}}
        past_time = 0
        total_damage = 0
        for i in range(len(self._skill_set)):
            skill = self._skill_set[i]

            # 该技能伤害，并汇总
            total_damage = total_damage + skill.damage

            # 该技能的剩余cd时间，实际的剩余时间需要减去之前的past_time
            status = skill_status.get_status_by_name(skill.name)
            res_cd = status['res_cd'] - past_time
            past_time = past_time + self._human_reflection + res_cd
            if i + 2 <= len(self._skill_set):  # 如果有下一个柔化技能，则action_time直接使用柔化时间
                next_skill = self._skill_set[i + 1]
                # 柔化技能可使用时间
                force_action_time = skill.force_next_skill_time[next_skill.name]
                # 累加整体时间，如果下一个技能的cd时间大于force_action_time，则累加下一个技能的cd时间
                past_time = past_time + self._human_reflection + force_action_time
            else:  # 如果是最后一个技能，则action_time使用该技能的
                # 该技能的剩余cd时间
                past_time = past_time + self._human_reflection + skill.action_time
        print('skill_set:', json.dumps(self._skill_set, ensure_ascii=False), 'past_time:', past_time)
        return past_time, total_damage

    def execution(self, skill_status: SkillStatus):
        pass
