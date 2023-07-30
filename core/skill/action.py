from typing import Dict, Union


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

    def __init__(self, skill_info: Dict[str, Skill], human_reflection: float):
        self._skill_list_with_force_skill_set: List[SkillActionSet] = self._make_force_set(skill_info)
        self._human_reflection = human_reflection

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
        for _, skill in skill_info.items():
            result.extend(self._deep_search_force_skill(skill=skill, skill_info=skill_info))

        return [SkillActionSet(self._human_reflection, x) for x in result]

    def _single_skill_action(self, skill: Skill, ):
        return skill.action_time,

    def exec(self, skill_status: SkillStatus):
        skill_actions = []
        for skill_set in self._skill_list_with_force_skill_set:
    # 获取技能cd状态 {"res_cd":0.4,"cnt":1}