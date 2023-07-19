import json
from typing import Dict, List


class Skill:

    def __init__(self, skill_config_dict: dict):
        self._level = skill_config_dict['level']
        self._name = skill_config_dict['name']
        self._cd = float(skill_config_dict['cd'])
        self._cast_time = float(skill_config_dict['cast_time'])
        self._during = float(skill_config_dict['during'])
        self._force_next_skill_time = {}
        if 'force_next_skill_time' in skill_config_dict:
            self._force_next_skill_time = skill_config_dict['force_next_skill_time']
        self._damage = float(skill_config_dict['damage'])
        self._damage_2 = 0
        if 'damage_2' in skill_config_dict:
            self._damage_2 = skill_config_dict['damage_2']

    @property
    def level(self):
        return self._level

    @property
    def name(self):
        return self._name

    @property
    def cd(self):
        return self._cd

    @property
    def cast_time(self):
        return self._cast_time

    @property
    def during(self):
        return self._during

    @property
    def force_next_skill_time(self):
        return self._force_next_skill_time

    @property
    def damage(self):
        return self._damage

    @property
    def damage_2(self):
        return self._damage_2

    @property
    def detail(self):
        return f'name: {self.name}, level: {self.level}, cd: {self.cd}, cast_time: {self.cast_time}, ' \
               f'during: {self.during}, force_next_skill_time: {self.force_next_skill_time}, damage: {self.damage}'

    def get_final_damage(self, time, times):
        if self._name == '雷云':
            # print(time / 2 * self._damage_2)
            # print(times * self._damage)
            return time / 2 * self._damage_2 + times * self._damage
        else:
            return self._damage * times

    def add_stone_info(self, skill_info_list: List[Dict], stone_skill_info_list: List[Dict]):
        for skill_info in skill_info_list:
            alted_skill_info = {}
            for stone_skill_info in stone_skill_info_list:
                if skill_info['name'] == stone_skill_info['name']:




if __name__ == '__main__':
    with open('C:/Users/QQ/PycharmProjects/阿修罗技能测试/data/basic_set/skill_info.json', 'r', encoding='utf_8') as f:
        for skill_info in json.load(f):
            print(Skill(skill_info).detail)
