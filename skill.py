import copy
import json
from typing import Dict, List, Union

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


class SkillStatus:
    def __init__(self, skill_info: Dict):
        # {"炸热":{"res_cd":0.4,"cnt":1}}
        self._skill_status_map = self._init_status_map(skill_info)

    def _init_status_map(self, skill_info: Dict) -> Dict[str, Dict[str, Union[float, int]]]:
        result = {}
        for skill_name in skill_info:
            case = {'res_cd': 0.0, "cnt": 0}
            result[skill_info[skill_name].name] = case
        return result

    def get_status_by_name(self, skill_name: str):
        skill_status = self._skill_status_map[skill_name]
        return skill_status

    def get_all_status(self):
        return self._skill_status_map

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

    def add_skill_cnt(self, skill_name: str, cnt) -> int:
        self._skill_status_map[skill_name]['cnt'] += cnt
        return self._skill_status_map[skill_name]['cnt']


class SkillAction:

    def __init__(self, skill_info: Dict[str, Skill]):
        self._skill_list_with_force_skill_set = self._make_force_set(skill_info)

    def _deep_search_force_skill(self, skill: Skill, skill_info: Dict[str, Skill], path: List = None):
        if path is None:
            path = []
        paths = []
        current_path = path + [skill]
        if skill.force_next_skill_time:
            for next_skill_name, force_time in skill.force_next_skill_time.items():
                next_skill = skill_info[next_skill_name]
                if not next_skill.force_next_skill_time:
                    paths.append(current_path + [next_skill])
                else:
                    for sub_path in self._deep_search_force_skill(skill=next_skill, skill_info=skill_info,
                                                                  path=current_path):
                        paths.append(sub_path)
        else:
            paths.append(current_path)
        return paths

    def _make_force_set(self, skill_info: Dict[str, Skill]):
        result = []
        # 针对有柔化技能的技能进行遍历，获得柔化技能组
        for skill_name, skill in skill_info.items():
            result.extend(self._deep_search_force_skill(skill=skill, skill_info=skill_info))

        return result

    def run(self, skill_info: Dict[str, Skill], skill_status: SkillStatus):
        skill_actions = []
        for skill_name, skill in skill_info.items():
            # 获取技能cd状态 {"res_cd":0.4,"cnt":1}
            status = skill_status.get_status_by_name(skill_name)

            if skill.force_next_skill_time:
                force_skill_set = self._make_force_set(start)


if __name__ == '__main__':
    skill_info = {}
    with open('/Users/bytedance/WorkSpace/PythonProjects/qiuqiu_dev/dnf_skill_sim/data/test_sim_set/skill_info.json',
              'r', encoding='utf_8') as f:
        for skill_name, skill in json.load(f).items():
            skill_info[skill_name] = Skill(skill_name, skill)

    sa = SkillAction(skill_info)
