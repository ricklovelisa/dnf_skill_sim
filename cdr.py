from typing import List

from skill import Skill


class CDRInfo:
    lingtong_cd_map = {0.1: 4, 0.15: 3, 0.2: 2}

    def __init__(self,
                 lingtong_pct: float,
                 red_fuwen: int,
                 blue_fuwen: int,
                 common_cdr: float,
                 common_cdrr: float,
                 other_cdr: float,
                 other_cdrr: float):
        self._lingtong_pct = lingtong_pct
        self._red_fuwen = red_fuwen
        self._blue_fuwen = blue_fuwen
        self._common_cdr = common_cdr
        self._common_cdrr = common_cdrr
        self._other_cdr = other_cdr
        self._other_cdrr = other_cdrr

    def get_final_cd(self, skill_info: Skill, skill_time: int):
        raw_cd = skill_info.cd

        final_cdr = self._common_cdr * self._other_cdr
        final_cdrr = self._common_cdrr + self._other_cdrr
        if self._lingtong_pct in self.lingtong_cd_map:
            cycle_times = self.lingtong_cd_map[self._lingtong_pct]
            curr_lingtong_cdrr = skill_time % cycle_times * self._lingtong_pct
            final_cdrr += curr_lingtong_cdrr
        print('final_cdr:', final_cdr, ', final_cdrr:', final_cdrr)
        return final_cdr / (1 + final_cdrr) * raw_cd
