import matplotlib.pyplot as plt
import numpy as np
DATA_PATH = 'data'

class Calc:
    def compute_cdr_line(self, start, end, waste_time, cdrr):
        raw_cd = np.linspace(start, end, 500)
        final_cd = 1 - (waste_time + (raw_cd - waste_time) / (1 + cdrr)) / raw_cd

        plt.plot(raw_cd, final_cd)
        plt.show()

    def compute_cd_set(self, ):
        with open(f'{DATA_PATH}/{set_file_name}/skill_info.json', 'r') as f:
            skill_list = []
            for skill_info in json.load(f):
                skill_list.append(parse_skill(skill_info))


if __name__ == '__main__':
    c = Calc()
    c.compute_cdr_line(start=20, end=60, waste_time=10, cdrr=8)
