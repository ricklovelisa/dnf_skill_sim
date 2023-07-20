from typing import List, Dict

from skill import Skill


class SkillCDRInfo:
    lingtong_cd_map = {0.1: 4, 0.15: 3, 0.2: 2}
    op_ind_cdr_map = {0.99: [1, 5, 10, 15, 20, 25, 30],
                      0.98: [35, 40, 45, 60, 70],
                      0.95: [75, 80, 95]}

    def __init__(self,
                 skill: Skill,
                 lingtong_pct: float,
                 red_fuwen: int,
                 blue_fuwen: int,
                 common_cdr: float,
                 common_cdrr: float,
                 other_skill_cdr: float,
                 other_skill_cdrr: float):
        self._skill = skill
        self._lingtong_pct = lingtong_pct
        self._red_fuwen = red_fuwen
        self._blue_fuwen = blue_fuwen
        self._common_cdr = common_cdr
        self._common_cdrr = common_cdrr
        self._other_skill_cdr = other_skill_cdr
        self._other_skill_cdrr = other_skill_cdrr

    @property
    def skill(self):
        return self._skill

    def get_final_cd(self, skill_times: int):
        op_ind_cdr = 1
        for k, v in self.op_ind_cdr_map.items():
            if self._skill.level in v:
                op_ind_cdr = k
        final_cdr = self._common_cdr * self._other_skill_cdr * self._red_fuwen * self._blue_fuwen * op_ind_cdr
        final_cdrr = self._common_cdrr + self._other_skill_cdrr
        # print(self._lingtong_pct)
        # print(self.lingtong_cd_map)
        if self._lingtong_pct in self.lingtong_cd_map:
            cycle_times = self.lingtong_cd_map[self._lingtong_pct]
            curr_lingtong_cdrr = skill_times % (cycle_times + 1) * self._lingtong_pct
            final_cdrr += curr_lingtong_cdrr
        final_cd = final_cdr / (1 + final_cdrr) * self._skill.cd
        # print(f'final_cdr: {final_cdr}, final_cdrr: {final_cdrr}, final_cd: {final_cd}')
        return final_cd


def parse_cdr_info(skill_dict: Dict, cdr_info_json: dict) -> Dict:
    lingtong_info = {}
    if 'lingtong_info' in cdr_info_json:
        lingtong_info = cdr_info_json['lingtong_info']

    common_cdr = 1
    if 'common_cdr' in cdr_info_json:
        for cdr in cdr_info_json['common_cdr']:
            common_cdr *= cdr
    # print('common_cdr:', common_cdr)

    common_cdrr = 0
    if 'common_cdrr' in cdr_info_json:
        for cdrr in cdr_info_json['common_cdrr']:
            common_cdrr += cdrr
    # print('common_cdrr:', common_cdrr)

    result = {}
    for skill_name, skill in skill_dict.items():
        # print('===============================================================')
        # print(skill.detail)
        lingtong_pct = 0
        if str(skill.level) in lingtong_info:
            lingtong_pct = lingtong_info[str(skill.level)]

        final_red_fuwen_cdr = 1
        if 'red_fuwen' in cdr_info_json:
            for red_fuwen_dict in cdr_info_json['red_fuwen']:
                if skill.name in red_fuwen_dict:
                    for red_fuwen_cdr in range(red_fuwen_dict[skill.name]):
                        final_red_fuwen_cdr *= 1.04
        # print('final_red_fuwen_cdr:', final_red_fuwen_cdr)

        final_blue_fuwen_cdr = 1
        if 'blue_fuwen' in cdr_info_json:
            for blue_fuwen_dict in cdr_info_json['blue_fuwen']:
                if skill.name in blue_fuwen_dict:
                    for red_fuwen_cdr in range(blue_fuwen_dict[skill.name]):
                        final_blue_fuwen_cdr *= 0.95
        # print('final_blue_fuwen_cdr', final_blue_fuwen_cdr)

        final_other_skill_cdr = 1
        if 'other_skill_cdr' in cdr_info_json:
            for other_skill_dict in cdr_info_json['other_skill_cdr']:
                if skill.name in other_skill_dict:
                    for other_skill_cdr in other_skill_dict[skill.name]:
                        final_other_skill_cdr *= other_skill_cdr

        cdr_info = SkillCDRInfo(skill=skill,
                                lingtong_pct=lingtong_pct,
                                red_fuwen=final_red_fuwen_cdr,
                                blue_fuwen=final_blue_fuwen_cdr,
                                common_cdr=common_cdr,
                                common_cdrr=common_cdrr,
                                other_skill_cdr=final_other_skill_cdr,
                                other_skill_cdrr=0)
        result[skill_name] = cdr_info
        # print('===============================================================')
        # print()
    return result
