import json
import os
from typing import List

from cdr import CDRInfo, parse_cdr_info
from skill import Skill, parse_skill

DATA_PATH = 'data'


class Sim:

    def run_with_time(self, skill_list: List[Skill], cdr_info_json: dict, time: int):
        # 先根据skill list和cdr_info_json生成对应技能的cdr
        result = parse_cdr_info(skill_list, cdr_info_json)

        # 根据skill_list和cdr_info生成每个技能的次数
        skill_apl = []
        for cdr_info in result:
            # print("=======================================")
            # print(cdr_info.skill.detail)
            time_cost = 0
            times = 0
            while True:
                if time_cost + 2 >= time:
                    break
                # print("++++++++++++++++++++++++++++++++++++++++++++++++++")
                times += 1
                real_cd = cdr_info.get_final_cd(times)
                time_cost += real_cd
                # print(f'time cost: {time_cost}')
                # print("++++++++++++++++++++++++++++++++++++++++++++++++++")
            # print("=======================================")
            # print()
            skill_apl.append(
                {cdr_info.skill.name: {'n': times, 'damage': cdr_info.skill.get_final_damage(time, times)}})
        # print(json.dumps(skill_apl, ensure_ascii=False, indent=4))
        return skill_apl


if __name__ == '__main__':
    set_list = os.listdir(DATA_PATH)
    sim = Sim()

    total_result = []
    for set_file in set_list:
        for time in range(10, 180, 5):
            with open(f'{DATA_PATH}/{set_file}/set_info', 'r') as f:
                set_info = f.read()

            with open(f'{DATA_PATH}/{set_file}/skill_info.json', 'r') as f:
                skill_list = []
                for skill_info in json.load(f):
                    skill_list.append(parse_skill(skill_info))

            with open(f'{DATA_PATH}/{set_file}/cdr_info.json', 'r') as f:
                cdr_info_json = json.load(f)

            apl = sim.run_with_time(skill_list, cdr_info_json, time)
            case = {'set_info': set_info, 'apl': apl, 'time': time}
            total_result.append(case)

    print(json.dumps(total_result, ensure_ascii=False))
