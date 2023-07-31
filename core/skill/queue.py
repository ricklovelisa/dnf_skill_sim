from typing import List

from core.skill.definition import Skill


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