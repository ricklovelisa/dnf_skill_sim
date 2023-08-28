from core.classes.cls import DnfCls
from core.skill.definition import SkillQueue


class Asura(DnfCls):
    def __init__(self):
        super().__init__()

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
            damage = skill.damage * total_time + skill.damage_2 * total_time // 2
            damage_dict[skill.name]['damage'] = damage

        damage_list = [{'name': k, 'times': v['times'], 'damage': v['damage']} for k, v in damage_dict.items()]
        damage_list = sorted(damage_list, key=lambda x: x['damage'], reverse=True)

        return damage_list
