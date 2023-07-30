import json
from typing import List, Dict

import matplotlib.pyplot as plt
import numpy as np

from core.skill import Skill

DATA_PATH = '../../data'


class Calc:
    def compute_cdr_line(self, start, end, waste_time, cdrr):
        raw_cd = np.linspace(start, end, 500)
        final_cd = 1 - (waste_time + (raw_cd - waste_time) / (1 + cdrr)) / raw_cd

        plt.plot(raw_cd, final_cd)
        plt.show()

    def _check_fuwen(self, color, result_skill_set: List[Dict]):
        pass

    def _check_final_cd_diff(self, waste_time):
        pass

    def _check_tiemo(self, ):
        pass

    def _sample_global_cdr(self, n):

        pass

    def compute_cd_set(self, set_file_name, skill_pool: List):
        with open(f'{DATA_PATH}/{set_file_name}/skill_info.json', 'r') as f:
            skill_dict = {}
            for skill_info in json.load(f):
                skill = Skill(skill_info)


if __name__ == '__main__':
    c = Calc()
    c.compute_cdr_line(start=20, end=60, waste_time=10, cdrr=8)
