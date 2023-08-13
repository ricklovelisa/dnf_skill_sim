import json
from copy import copy, deepcopy
from typing import Dict, Union, Tuple, List

from core.skill.action import SkillSet, SkillStatus, SkillSetAction
from core.skill.definition import SkillQueue


class Search:

    def __init__(self):
        self._zero_bias = 0.000000000001

    def search_best_skill(self, strategy: str, actions: List[SkillSetAction], skill_status: SkillStatus,
                          res_time) -> SkillSetAction:
        if strategy == 'res_cd':  # 根据剩余cd
            # return self._search_best_skill_by_res_cd(actions, res_time)
            return self._search_best_skill_by_res_cd(actions, skill_status, res_time)
        # elif strategy == 'res_cd_2':  # 根据伤害/技能降临时间
        #     return self._search_best_skill_by_res_cd_2(actions, 0.1, res_time)
        # elif strategy == 'res_cd_3':
        #     return self._search_best_skill_by_res_cd_3(actions, res_time)
        # elif strategy == 'both_damage_dps_by_past_time':
        #     return self._both_search_best_skill_by_damage_and_dps(actions, res_time)
        raise Exception(f'没有该技能选择策略：{strategy} 或 返回可用技能为空')

    # def _search_best_skill_by_res_cd(self, actions: List[Dict], res_time: float):
    #     # print('actions:', actions)
    #     filtered_actions = [x for x in actions if res_time > x['past_time']]
    #
    #     # 如果有很多cd为0的技能，则按照damage/past_time来排序
    #     zero_res_cd_actions = [x for x in filtered_actions if x['res_cd'] == 0]
    #     if zero_res_cd_actions:
    #         zero_res_cd_actions = [{'skill_set': x['skill_set'], 'dpp': x['damage'] / x['past_time']} for x in
    #                                zero_res_cd_actions]
    #         sorted_zero_res_cd_actions = sorted(zero_res_cd_actions, key=lambda x: x['dpp'], reverse=True)
    #         return sorted_zero_res_cd_actions[0]['skill_set']
    #
    #     sorted_filtered_actions = sorted(filtered_actions, key=lambda x: x['res_cd'], reverse=False)
    #     # print('sorted_filtered_actions: ', len(sorted_filtered_actions), sorted_filtered_actions)
    #     if len(sorted_filtered_actions) == 0:
    #         return None
    #     else:
    #         return sorted_filtered_actions[0]['skill_set']

    @staticmethod
    def _search_best_skill_by_res_cd(skill_actions: List[SkillSetAction], skill_status: SkillStatus, res_time: float):
        # print('actions:', actions)
        # filtered_actions = [x for x in skill_action_queue if res_time > x['past_time']]
        filtered_actions = [x for x in skill_actions if res_time > x.queue.past_time]
        if len(filtered_actions) == 0:
            return None

        # 如果有很多cd为0的技能，则按照damage/past_time来排序
        actions_and_res_cd = []
        for action in filtered_actions:
            if len(action.queue.skill_names) == 1:
                res_cd = skill_status.get_skill_res_cd(action.queue.skill_names[0])
            else:
                res_cd = max([skill_status.get_skill_res_cd(x) for x in action.queue.skill_names])
            actions_and_res_cd.append((action, res_cd))

        zero_res_cd_actions = [x[0] for x in actions_and_res_cd if x[1] == 0]
        if len(zero_res_cd_actions) > 1:
            sorted_zero_res_cd_actions = []
            for action in zero_res_cd_actions:
                next_cd = action.queue.max_next_cd
                if res_time > next_cd + action.human_reflection + action.skill_set.action_time:
                    sorted_zero_res_cd_actions.append((action, action.queue.damage / action.queue.past_time))
                else:
                    sorted_zero_res_cd_actions.append((action, action.queue.damage / next_cd / action.queue.past_time))

            # zero_res_cd_actions = [{'skill_set': x['skill_set'], 'dpp': x['damage'] / x['past_time']} for x in
            #                        zero_res_cd_actions]
            sorted_zero_res_cd_actions = sorted(sorted_zero_res_cd_actions, key=lambda x: x[1], reverse=True)
            return sorted_zero_res_cd_actions[0][0]

        sorted_filtered_actions = sorted(actions_and_res_cd, key=lambda x: x[1], reverse=False)
        # print('sorted_filtered_actions: ', len(sorted_filtered_actions), sorted_filtered_actions)
        return sorted_filtered_actions[0][0]

    def _search_best_skill_by_res_cd_2(self, actions: List[Dict], human_reflection: float, res_time: float):
        # print('actions:', actions)
        filtered_actions = [x for x in actions if res_time > x['past_time']]

        # 如果剩余时间能多释放一次该技能，则使用dps来进行选择，如果剩余时间只能释放一次该技能，则使用damage来筛选
        sorted_filtered_actions = []
        for raw_action in filtered_actions:
            action = deepcopy(raw_action)
            past_time = action['past_time']
            curr_res_cd = action['res_cd']
            next_cd = action['next_cd']
            # 判断当前技能使用的比对的条件，是dps，还是damage
            # 判断剩余时间是否能放2个及以上技能
            if res_time - past_time - human_reflection - next_cd > 0.5:  # 先暂时设定一个0.5作为阈值，后续需要更加精细化的计算
                action['sortation'] = action['dps'] / action['past_time']
            else:
                action['sortation'] = action['damage'] / action['past_time']

            # 如果当前技能cd为0，则需用zero_bias来提升重要性
            if action['res_cd'] == 0:
                action['sortation'] = action['sortation'] / self._zero_bias

            sorted_filtered_actions.append(action)
        # # 如果有很多cd为0的技能，则按照damage/past_time来排序
        # zero_res_cd_actions = [x for x in filtered_actions if x['res_cd'] == 0]
        # if zero_res_cd_actions:
        #     zero_res_cd_actions = [{'skill_set': x['skill_set'], 'dpp': x['dps'] / x['past_time']} for x in
        #                            zero_res_cd_actions]
        #     sorted_zero_res_cd_actions = sorted(zero_res_cd_actions, key=lambda x: x['dpp'], reverse=True)
        #     return sorted_zero_res_cd_actions[0]['skill_set']

        sorted_filtered_actions = sorted(sorted_filtered_actions, key=lambda x: x['sortation'], reverse=True)
        # print('sorted_filtered_actions: ', len(sorted_filtered_actions), sorted_filtered_actions)
        if len(sorted_filtered_actions) == 0:
            return None
        else:
            return sorted_filtered_actions[0]['skill_set']

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
