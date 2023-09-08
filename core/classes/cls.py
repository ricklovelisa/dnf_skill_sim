from abc import abstractmethod
from typing import List

from core.skill.definition import Skill, SkillQueue


class DnfCls:

    def __init__(self):
        self._weapon_cdr = 1
        self._talent_cdr = 1
        self._skills = None
        self._queue = None

    @property
    def skills(self):
        return self._skills

    @property
    def queue(self):
        return self._queue

    def _update_cdr_info(self):


    def update_weapon_cdr(self, weapon_cdr):
        self._weapon_cdr = weapon_cdr
        self._update_cdr_info()


    def set_skills(self, skills: List[Skill]):
        self._skills = skills

    def set_queue(self, skill_queue: SkillQueue):
        self._queue = skill_queue

    @abstractmethod
    def compute_total_damage(self, total_time):
        active_skill_damage = sum([x.damage for x in self._queue])
        return active_skill_damage

    @abstractmethod
    def compute_damage_by_skill(self, total_time):
        damage_dict = {}
        for skill in self._queue:
            if skill.name in damage_dict:
                damage_dict[skill.name]['times'] += 1
            else:
                damage_dict[skill.name] = {'times': 1}

        for skill in self._queue:
            damage = skill.damage * total_time
            damage_dict[skill.name]['damage'] = damage

        damage_list = [{'name': k, 'times': v['times'], 'damage': v['damage']} for k, v in damage_dict.items()]
        damage_list = sorted(damage_list, key=lambda x: x['damage'], reverse=True)

        return damage_list
