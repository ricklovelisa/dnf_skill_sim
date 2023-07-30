from typing import Dict, Union

from core.skill import Skill, SkillStatus


class Search:

    def search_best_skill(self, strategy: str, skill_info: Dict[str, Skill], skill_status: SkillStatus, is_op: bool):
        all_status = skill_status.get_all_status()
        if strategy == 'res_cd':  # 根据剩余cd
            return self._search_best_skill_by_res_cd(all_status=all_status)
        elif strategy == 'damage_by_past_time':  # 根据伤害/技能降临时间
            return self._search_best_skill_by_damage(all_status=all_status, skill_info=skill_info)
        elif strategy == 'dps_by_past_time':
            return self._search_best_skill_by_dps(all_status=all_status, skill_info=skill_info, is_op=is_op)
        raise Exception(f'没有该技能选择策略：{strategy} 或 返回可用技能为空')

    @staticmethod
    def _search_best_skill_by_res_cd(all_status: Dict[str, Dict[str, Union[float, int]]]):
        sorted_skill_status_list = sorted(all_status.items(), key=lambda x: x[1]['res_cd'], reverse=True)
        sorted_skill_status_list = [x[0] for x in sorted_skill_status_list]
        return sorted_skill_status_list

    @staticmethod
    def _search_best_skill_by_damage(all_status: Dict[str, Dict[str, Union[float, int]]], skill_info: Dict[str, Skill]):
        # ('炸热', res_cd, action_time, damage)
        skill_status_list = [(skill_name, status['res_cd'], skill_info[skill_name].action_time,
                              skill_info[skill_name].damage) for skill_name, status in all_status.items()]
        sorted_skill_status_list = sorted(skill_status_list, key=lambda x: x[3] / (x[1] + x[2]), reverse=True)
        sorted_skill_status_list = [x[0] for x in sorted_skill_status_list]
        return sorted_skill_status_list

    @staticmethod
    def _search_best_skill_by_dps(all_status: Dict[str, Dict[str, Union[float, int]]], skill_info: Dict[str, Skill],
                                  is_op: bool):
        # ('炸热', res_cd, action_time, damage, 本次释放后的cd)
        skill_status_list = [(skill_name, status['res_cd'], skill_info[skill_name].action_time,
                              skill_info[skill_name].damage,
                              skill_info[skill_name].get_final_cd(is_op=is_op, times=status['cnt']))
                             for skill_name, status in all_status.items()]
        sorted_skill_status_list = sorted(skill_status_list, key=lambda x: x[3] / x[4] / (x[1] + x[2]),
                                          reverse=True)
        sorted_skill_status_list = [x[0] for x in sorted_skill_status_list]
        return sorted_skill_status_list
