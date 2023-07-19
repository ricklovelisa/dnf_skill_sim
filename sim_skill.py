from typing import List, Union

from cdr import SkillCDRInfo


class SkillStatus:
    def __init__(self, skill_list: List[SkillCDRInfo]):
        # {"炸热":{"rest_cd":0.4,"cnt":1}}
        self._skill_status_map = self._init_status_map(skill_list)
        self._skill_cdr_info = skill_list

    def _init_status_map(self, skill_list: List[SkillCDRInfo]):
        result = {}
        for skill in skill_list:
            case = {'res_cd': 0.0, "cnt": 0}
            result[skill.skill.name] = case
        return result

    def cooling_down(self, ts: float, skill_name: str = None):
        if skill_name:
            current_res_cd = self._skill_status_map[skill_name]['res_cd']
            self._skill_status_map[skill_name]['res_cd'] = max(current_res_cd - ts, 0)
        else:
            for skill_name in self._skill_status_map:
                self.cooling_down(ts, skill_name)

    def find_available_skills(self):
        result = []
        for skill_name in self._skill_status_map:
            if self._skill_status_map[skill_name]['res_cd'] == 0:
                result.append(skill_name)

        return result

    def find_almost_available_skills(self):
        result = []
        diff_cds = 99999
        for skill_name in self._skill_status_map:
            if self._skill_status_map[skill_name]['res_cd'] < diff_cds:
                result = [skill_name]
                diff_cds = self._skill_status_map[skill_name]['res_cd']
            if self._skill_status_map[skill_name]['res_cd'] == diff_cds:
                result.append(skill_name)
        return result

    def start_cooling_down(self, skill_name):
        skill_status = self._skill_status_map[skill_name]
        


class SimSkill:
    def __init__(self, bias: Union[float, str] = None):
        if bias:
            self._bias =

    @staticmethod
    def create_skill_status(self, skill_pool: List[SkillCDRInfo]) -> SkillStatus:
        return SkillStatus(skill_pool)

    def sim_single(self, skill_pool: List[SkillCDRInfo], total_time: float):
        skill_status = self.create_skill_status(skill_pool)
        time_line = 0
        while True:
            if time_line >= total_time -
