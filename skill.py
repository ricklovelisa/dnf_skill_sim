import copy
import json
from typing import Dict, List

from cdr import CDRInfo, make_cdr_info


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

    def __str__(self):
        return self.detail

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

    def update_damage(self, damage_info: Dict, fuwen_info):
        fuwen_rate = self._generate_fuwen_damage_rate(fuwen_info)

        # 全局技能倍率
        self._damage = damage_info['global'] * fuwen_rate * self._damage
        self._damage_2 = damage_info['global'] * fuwen_rate * self._damage_2

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


class SkillQueue:
    def __init__(self, skill_queue: List[Skill], total_time: float):
        self._queue = skill_queue
        self._total_time = total_time

    def compute_total_damage(self):
        damage_by_skill = self.compute_damage_by_skill()

        total_damage = 0
        for skill_name, info in damage_by_skill.items():
            total_damage += info['damage']
        return total_damage

    def compute_damage_by_skill(self):
        damage_dict = {}
        for skill in self._queue:
            if skill.name in damage_dict:
                damage_dict[skill.name]['times'] += 1
            else:
                damage_dict[skill.name] = {'times': 1}

        for skill in self._queue:
            damage = skill.get_final_damage(self._total_time, damage_dict[skill.name]['times'])
            damage_dict[skill.name]['damage'] = damage

        return damage_dict

    @property
    def list(self):
        return self._queue


if __name__ == '__main__':
    with open('C:/Users/QQ/PycharmProjects/阿修罗技能测试/data/basic_set/skill_info.json', 'r', encoding='utf_8') as f:
        for skill_name, skill_info in json.load(f).items():
            print(Skill(skill_name, skill_info).detail)
