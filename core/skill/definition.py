import copy
import json
from typing import Dict, List

from core.skill.cdr import CDRInfo, make_cdr_info


class Skill:

    def __init__(self, skill_name, skill_config_dict: dict, cdr_info: CDRInfo = None):
        self._name = skill_name
        self._level = skill_config_dict['level']
        self._cd = float(skill_config_dict['cd'])
        self._cast_time = float(skill_config_dict['cast_time'])
        self._during = float(skill_config_dict['during'])
        self._force_next_skill_time = {}
        if 'force_next_skill_time' in skill_config_dict:
            self._force_next_skill_time = skill_config_dict['force_next_skill_time']
        self._damage = float(skill_config_dict['damage'])
        self._damage_2 = 0
        if 'damage_2' in skill_config_dict:
            self._damage_2 = float(skill_config_dict['damage_2'])
        self._cdr_info = cdr_info

    def __str__(self):
        return self.detail

    def __repr__(self):
        return self.detail

    @property
    def level(self) -> int:
        return self._level

    @property
    def name(self) -> str:
        return self._name

    @property
    def cd(self) -> float:
        return self._cd

    @property
    def cast_time(self) -> float:
        return self._cast_time

    @property
    def action_time(self) -> float:
        return self._cast_time + self._during

    @property
    def during(self) -> float:
        return self._during

    @property
    def force_next_skill_time(self) -> Dict:
        return self._force_next_skill_time

    @property
    def damage(self) -> float:
        return self._damage

    @property
    def damage_2(self) -> float:
        return self._damage_2

    @property
    def detail(self) -> str:
        return f'name: {self.name}, level: {self.level}, cd: {self.cd}, cast_time: {self.cast_time}, ' \
               f'during: {self.during}, force_next_skill_time: {self.force_next_skill_time}, damage: {self.damage}'

    def add_cdr_info(self, cdr_info, fuwen_info):
        self._cdr_info = make_cdr_info(self.name, self.level, cdr_info, fuwen_info)

    def _generate_fuwen_damage_rate(self, fuwen_info):
        red_damage_rate = 1
        if 'red' in fuwen_info:
            if self.name in fuwen_info['red']:
                red_damage_rate *= 1.06 ** fuwen_info['red'][self.name]

        purple_damage_rate = 1
        if 'red' in fuwen_info:
            if self.name in fuwen_info['purple']:
                purple_damage_rate *= 1.04 ** fuwen_info['purple'][self.name]

        return red_damage_rate * purple_damage_rate

    def update_damage(self, damage_info: Dict, fuwen_info: Dict, skill_level_damage_rate_info: Dict):
        fuwen_rate = self._generate_fuwen_damage_rate(fuwen_info)
        skill_level_damage_rate = 1
        if skill_level_damage_rate_info and self.name in skill_level_damage_rate_info:
            skill_level_damage_rate = skill_level_damage_rate_info[self.name]

        # 更新技能倍率
        if 'skill' in damage_info and str(self.level) in damage_info['skill']:
            damage_1_rate = damage_info['skill'][str(self.level)]['damage_1']
            damage_2_rate = damage_1_rate
            if 'damage_2' in damage_info['skill'][str(self.level)]:
                damage_2_rate = damage_info['skill'][str(self.level)]['damage_2']
            self._damage = damage_1_rate * fuwen_rate * skill_level_damage_rate * self._damage
            self._damage_2 = damage_2_rate * fuwen_rate * skill_level_damage_rate * self._damage_2
        else:
            # 全局技能倍率
            self._damage = damage_info['global'] * fuwen_rate * skill_level_damage_rate * self._damage
            self._damage_2 = damage_info['global'] * fuwen_rate * skill_level_damage_rate * self._damage_2

    def get_final_cd(self, is_op: bool, times: int):
        return self.cd * self._cdr_info.get_cdr(is_op, times)

    def get_final_damage(self, time, times) -> float:
        if self._name == '雷云':
            # print(time / 2 * self._damage_2)
            # print(times * self._damage)
            return time / 2 * self._damage_2 + times * self._damage
        else:
            return self._damage * times

    @staticmethod
    def create_skill_with_stone(skill_name: str, skill_info: Dict, stone_info: Dict):
        new_skill_info = copy.deepcopy(skill_info)
        for key, value in stone_info.items():
            if key == 'damage':
                new_skill_info[key] = new_skill_info[key] * value
            else:
                new_skill_info[key] = value

        return Skill(skill_name, new_skill_info)


class SkillSet:
    """ 该类用于描述一些职业的所有的可执行技能组合，这些组合包括单个技能，以及多个相互间可柔化技能。

    例如[炸热、无双、不动]或[无为法]

    构建本对象，是为了方便进行针对技能组的数据统计，例如技能组的默认总伤，总耗时，总dps等
    """

    def __init__(self, skills: List[Skill]):
        self._skills = skills

    def __str__(self):
        return json.dumps([x.name for x in self._skills], ensure_ascii=False)

    def __repr__(self):
        return self.__str__()

    @property
    def skills(self):
        return self._skills

    @property
    def action_time(self):
        """ 该技能组合的最短action_time
        只考虑技能之间的柔化时间和最后一个技能的action时间
        :return:
        """
        skill_set_len = len(self._skills)
        if skill_set_len == 1:
            return self._skills[0].action_time
        else:
            action_time = 0
            for i in range(skill_set_len):
                skill = self._skills[i]
                if i < skill_set_len - 1:  # 如果不是最后一个技能，则累加下一个技能的柔化时间
                    next_skill = self._skills[i + 1]
                    action_time += skill.force_next_skill_time[next_skill.name]
                else:  # 如果是最后一个技能，则加上最后一个技能的action时间
                    action_time += skill.action_time
            return action_time

    # @staticmethod
    # def parse(skill_set: List[Skill], human_reflection=0.1):
    #     if len(skill_set) == 1:
    #         return SingleSkill(skill_set=skill_set, human_reflection=human_reflection)
    #     elif len(skill_set) >= 2:
    #         return ForcedSkillSet(skill_set=skill_set, human_reflection=human_reflection)
    #     else:
    #         raise Exception('skill set长度不能为0')


class SkillQueue:
    class LoopBody:
        def __init__(self, skill: Skill, skill_past_time: float, skill_next_cd: float):
            self.skill = skill
            self.skill_past_time = skill_past_time
            self.skill_next_cd = skill_next_cd

    def __init__(self):
        self._queue: List[Skill] = []
        self._skill_past_time_line: List[float] = []
        self._next_cd_list: List[float] = []

    def __str__(self):
        return json.dumps(self.skill_names, ensure_ascii=False)

    def __repr__(self):
        return self.__str__()

    @property
    def skill_names(self) -> List[str]:
        return [x.name for x in self._queue]

    @property
    def past_time(self) -> float:
        return sum(self._skill_past_time_line)

    @property
    def next_cd_list(self) -> List[float]:
        return self._next_cd_list

    @property
    def max_next_cd(self) -> float:
        return max(self._next_cd_list)

    @property
    def damage(self):
        return sum([x.damage for x in self._queue])

    @property
    def json(self):
        result = []
        total_time_line = 0
        for skill, skill_past_time, skill_next_cd in zip(self._queue, self._skill_past_time_line, self._next_cd_list):
            total_time_line += skill_past_time
            result.append(
                {'skill': skill.detail, 'skill_past_time': skill_past_time, 'total_time_line': total_time_line,
                 'skill_next_cd': skill_next_cd})
        return json.dumps(result, ensure_ascii=False)

    @property
    def loop_info(self):
        result = []
        for skill, skill_past_line, skill_next_cd in zip(self._queue, self._skill_past_time_line, self._next_cd_list):
            result.append(self.LoopBody(skill, skill_past_line, skill_next_cd))

        return result

    def add_skill(self, skill: Skill):
        self._queue.append(skill)

    def add_skill_past_time(self, past_time: float):
        self._skill_past_time_line.append(past_time)

    def add_skill_next_cd(self, res_cd: float):
        self._next_cd_list.append(res_cd)

    def plot(self, total_time):
        pass

    def compute_total_damage(self, total_time):
        active_skill_damage = sum([x.damage for x in self._queue])
        evn_skill_damage = [total_time // 2 * x.damage_2 for x in self._queue if x.name == '雷云'][0]

        return active_skill_damage + evn_skill_damage

    def compute_damage_by_skill(self, total_time):
        damage_dict = {}
        for skill in self._queue:
            if skill.name in damage_dict:
                damage_dict[skill.name]['times'] += 1
            else:
                damage_dict[skill.name] = {'times': 1}

        for skill in self._queue:
            damage = skill.get_final_damage(total_time, damage_dict[skill.name]['times'])
            damage_dict[skill.name]['damage'] = damage

        damage_list = [{'name': k, 'times': v['times'], 'damage': v['damage']} for k, v in damage_dict.items()]
        damage_list = sorted(damage_list, key=lambda x: x['damage'], reverse=True)

        return damage_list

    def append(self, obj):
        if isinstance(obj, SkillQueue):
            self._queue.extend(obj._queue)
            self._skill_past_time_line.extend(obj._skill_past_time_line)
            self._next_cd_list.extend(obj._next_cd_list)
        else:
            raise TypeError('obj不是SkillQueue类')

        # def __str__(self):
    #     return json.dumps(self.skill_name_list, ensure_ascii=False)
    #
    # def __repr__(self):
    #     return self.__str__()

    # def compute_total_damage(self):
    #     damage_by_skill = self.compute_damage_by_skill()
    #
    #     total_damage = 0
    #     for item in damage_by_skill:
    #         total_damage += item['damage']
    #     return total_damage
    #
    # def compute_damage_by_skill(self):
    #     damage_dict = {}
    #     for skill in self._queue:
    #         if skill.name in damage_dict:
    #             damage_dict[skill.name]['times'] += 1
    #         else:
    #             damage_dict[skill.name] = {'times': 1}
    #
    #     for skill in self._queue:
    #         damage = skill.get_final_damage(self._total_time, damage_dict[skill.name]['times'])
    #         damage_dict[skill.name]['damage'] = damage
    #
    #     damage_list = [{'name': k, 'times': v['times'], 'damage': v['damage']} for k, v in damage_dict.items()]
    #     damage_list = sorted(damage_list, key=lambda x: x['damage'], reverse=True)
    #
    #     return damage_list
    #
    # @property
    # def list(self):
    #     return self._queue
    #
    # @property
    # def skill_name_list(self):
    #     return [x.name for x in self._queue]


def deep_search_force_skill(skill: Skill, skill_info: Dict[str, Skill], path: List = None):
    if path is None:
        path = []
    paths = []
    current_path = path + [skill]
    if skill.force_next_skill_time:
        for next_skill_name, force_time in skill.force_next_skill_time.items():
            if next_skill_name in skill_info:
                next_skill = skill_info[next_skill_name]
                if not next_skill.force_next_skill_time:
                    paths.append(current_path + [next_skill])
                else:
                    for sub_path in deep_search_force_skill(skill=next_skill, skill_info=skill_info,
                                                            path=current_path):
                        paths.append(sub_path)
    else:
        paths.append(current_path)
    return paths


def make_force_set(skill_info: Dict[str, Skill]) -> List[SkillSet]:
    result = []
    # 针对有柔化技能的技能进行遍历，获得柔化技能组
    for _, skill in skill_info.items():
        result.extend(deep_search_force_skill(skill=skill, skill_info=skill_info))

    # 柔化技能组除最后一个技能外，其他技能都添加到set中
    other_skills = []
    for sets in result:
        if len(sets) >= 2:
            other_skills.extend(sets[0:-1])

    result.extend([[x] for x in set(other_skills)])

    return [SkillSet(x) for x in result]
