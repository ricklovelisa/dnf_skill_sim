from typing import Dict


class CDRInfo:
    lingtong_cd_map = {0.1: 4, 0.15: 3, 0.2: 2}
    op_ind_cdr_map = {0.99: [1, 5, 10, 15, 20, 25, 30],
                      0.98: [35, 40, 45, 60, 70],
                      0.95: [75, 80, 95, 100]}

    def __init__(self,
                 op_ind_cdr: float,
                 lingtong_pct: float,
                 red_fuwen: int,
                 blue_fuwen: int,
                 common_cdr: float,
                 common_cdrr: float,
                 op_cdr_coef: int = 1,
                 weapon_cdr: float = 1):
        # other_skill_cdr: float,
        # other_skill_cdrr: float):
        self._op_ind_cdr = op_ind_cdr
        self._lingtong_pct = lingtong_pct
        self._red_fuwen = red_fuwen
        self._blue_fuwen = blue_fuwen
        self._common_cdr = common_cdr
        self._common_cdrr = common_cdrr
        self._weapon_cdr = weapon_cdr
        self._op_cdr_coef = op_cdr_coef

    def get_cdr(self, is_op: bool, skill_times: int):

        # 手搓
        op_ind_and_weapon_cdr = self._weapon_cdr
        if is_op:  # 手搓和武器cdr是加算
            weapon_cdr = 1 - self._weapon_cdr
            op_ind_cdr = 1 - self._op_ind_cdr
            op_ind_and_weapon_cdr = 1 - (weapon_cdr + self._op_cdr_coef * op_ind_cdr)

        # final_cdr = self._common_cdr * self._other_skill_cdr * self._red_fuwen * self._blue_fuwen * op_ind_cdr
        # final_cdrr = self._common_cdrr + self._other_skill_cdrr
        final_cdr = self._common_cdr * self._red_fuwen * self._blue_fuwen * op_ind_and_weapon_cdr
        final_cdrr = self._common_cdrr

        # 灵通
        if self._lingtong_pct in self.lingtong_cd_map:
            cycle_times = self.lingtong_cd_map[self._lingtong_pct]
            curr_lingtong_cdrr = skill_times % (cycle_times + 1) * self._lingtong_pct
            final_cdrr += curr_lingtong_cdrr

        # cdr最多不超过0.3
        return max(final_cdr / (1 + final_cdrr), 0.3)


def make_cdr_info(skill_name: str, skill_level: int, cdr_info_json: Dict, fuwen_info: Dict):
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

    lingtong_pct = 0
    if str(skill_level) in lingtong_info:
        lingtong_pct = lingtong_info[str(skill_level)]

    final_red_fuwen_cdr = 1
    if 'red' in fuwen_info:
        if skill_name in fuwen_info['red']:
            final_red_fuwen_cdr *= 1.04 ** fuwen_info['red'][skill_name]
    # print(f'skill: {skill_name}, final_red_fuwen_cdr: {final_red_fuwen_cdr}')

    final_blue_fuwen_cdr = 1
    if 'blue' in fuwen_info:
        if skill_name in fuwen_info['blue']:
            final_blue_fuwen_cdr *= 0.95 ** fuwen_info['blue'][skill_name]
    # print(f'skill: {skill_name}, final_blue_fuwen_cdr: {final_blue_fuwen_cdr}')

    # final_other_skill_cdr = 1
    # if 'other_skill_cdr' in cdr_info_json:
    #     for other_skill_dict in cdr_info_json['other_skill_cdr']:
    #         if skill_name in other_skill_dict:
    #             for other_skill_cdr in other_skill_dict[skill_name]:
    #                 final_other_skill_cdr *= other_skill_cdr

    op_ind_cdr = 0.99
    for op_cdr, skill_level_list in CDRInfo.op_ind_cdr_map.items():
        if skill_level in skill_level_list:
            op_ind_cdr = op_cdr

    # weapon_cdr = 1
    # if 'weapon_cdr' in cdr_info_json:
    #     weapon_cdr = cdr_info_json['weapon_cdr']

    op_cdr_coef = 1
    if 'op_cdr_coef' in cdr_info_json:
        op_cdr_coef = cdr_info_json['op_cdr_coef']

    return CDRInfo(op_ind_cdr=op_ind_cdr,
                   lingtong_pct=lingtong_pct,
                   red_fuwen=final_red_fuwen_cdr,
                   blue_fuwen=final_blue_fuwen_cdr,
                   common_cdr=common_cdr,
                   common_cdrr=common_cdrr,
                   weapon_cdr=weapon_cdr,
                   op_cdr_coef=op_cdr_coef)
