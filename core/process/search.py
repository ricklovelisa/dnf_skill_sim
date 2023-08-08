import json
from typing import Dict, Union, Tuple, List

from core.skill.action import SkillSet


class Search:

    def search_best_skill(self, strategy: str, actions: List[Dict], res_time) -> SkillSet:
        if strategy == 'res_cd':  # 根据剩余cd
            return self._search_best_skill_by_res_cd(actions, res_time)
        elif strategy == 'damage_by_past_time':  # 根据伤害/技能降临时间
            return self._search_best_skill_by_damage(actions, res_time)
        elif strategy == 'dps_by_past_time':
            return self._search_best_skill_by_dps(actions, res_time)
        elif strategy == 'both_damage_dps_by_past_time':
            return self._both_search_best_skill_by_damage_and_dps(actions, res_time)
        raise Exception(f'没有该技能选择策略：{strategy} 或 返回可用技能为空')

    @staticmethod
    def _search_best_skill_by_res_cd(actions: List[Dict], res_time):
        # print('actions:', actions)
        filtered_actions = [x for x in actions if res_time > x['past_time']]

        # 如果剩余时间能多释放一次该技能，则使用dps来进行选择，如果剩余时间只能释放一次该技能，则使用damage来筛选
        select_tag = 'dps'

        # 如果有很多cd为0的技能，则按照damage/past_time来排序
        zero_res_cd_actions = [x for x in filtered_actions if x['res_cd'] == 0]
        if zero_res_cd_actions:
            zero_res_cd_actions = [{'skill_set': x['skill_set'], 'dpp': x['dps'] / x['past_time']} for x in
                                   zero_res_cd_actions]
            sorted_zero_res_cd_actions = sorted(zero_res_cd_actions, key=lambda x: x['dpp'], reverse=True)
            return sorted_zero_res_cd_actions[0]['skill_set']

        sorted_filtered_actions = sorted(filtered_actions, key=lambda x: x['res_cd'], reverse=False)
        # print('sorted_filtered_actions: ', len(sorted_filtered_actions), sorted_filtered_actions)
        if len(sorted_filtered_actions) == 0:
            return None
        else:
            return sorted_filtered_actions[0]['skill_set']

    @staticmethod
    def _search_best_skill_by_damage(actions: List[Dict], res_time):
        filtered_actions = [x for x in actions if res_time > x['past_time']]
        sorted_actions = sorted(filtered_actions, key=lambda x: x['damage'] / x['past_time'], reverse=True)
        if len(sorted_actions) == 0:
            return None
        else:
            return sorted_actions[0]['skill_set']

    @staticmethod
    def _search_best_skill_by_dps(actions: List[Dict], res_time):
        filtered_actions = [x for x in actions if res_time > x['past_time']]
        sorted_actions = sorted(filtered_actions, key=lambda x: x['dps'] / x['past_time'], reverse=True)
        if len(sorted_actions) == 0:
            return None
        else:
            return sorted_actions[0]['skill_set']

    # @staticmethod
    # def _both_search_best_skill_by_damage_and_dps(actions: List[Dict], res_time):
    #     filtered_actions = [x for x in actions if res_time > x['past_time']]
    #     mixed_actions = []
    #     for action in filtered_actions:
    #         # 如果剩余时间，能够多释放一次该技能，则按照该技能的dps进行排序
    #         if res_time - action['res_cd'] > actions
    #
    #         if : # 如果剩余时间，只能释放1次该技能，则按照该技能的伤害排序
    #
    #     return sorted_actions[0]
