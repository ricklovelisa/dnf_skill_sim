class Skill:

    def __init__(self, level: int, name: str, cd: float, damage: float, damage_2: float = 0):
        self._level = level
        self._name = name
        self._cd = float(cd)
        self._damage = float(damage)
        self._damage_2 = float(damage_2)

    @property
    def level(self):
        return self._level

    @property
    def name(self):
        return self._name

    @property
    def cd(self):
        return self._cd

    @property
    def damage(self):
        return self._damage

    @property
    def detail(self):
        return f'name: {self._name}, level: {self._level}, cd: {self._cd}, damage: {self._damage}'

    def get_final_damage(self, time, times):
        if self._name == '雷云':
            print(time / 2 * self._damage_2)
            print(times * self._damage)
            return time / 2 * self._damage_2 + times * self._damage
        else:
            return self._damage * times


def parse_skill(skill_info: dict):
    if 'level' in skill_info \
            and 'name' in skill_info \
            and 'cd' in skill_info \
            and 'damage' in skill_info \
            and 'damage_2' in skill_info:

        return Skill(level=skill_info['level'],
                     name=skill_info['name'],
                     cd=skill_info['cd'],
                     damage=skill_info['damage'],
                     damage_2=skill_info['damage_2'])
    elif 'level' in skill_info \
            and 'name' in skill_info \
            and 'cd' in skill_info \
            and 'damage' in skill_info:

        return Skill(level=skill_info['level'],
                     name=skill_info['name'],
                     cd=skill_info['cd'],
                     damage=skill_info['damage'])
    else:
        return None


if __name__ == '__main__':
    result = parse_skill({'name': '大冰', 'cd': 20, 'level': 60, 'damage': 100})
    print(result)
