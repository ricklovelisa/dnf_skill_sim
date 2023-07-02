class Skill:

    def __init__(self, level: int, name: str, cd: float, damage: float):
        self._level = level
        self._name = name
        self._cd = float(cd)
        self._damage = float(damage)

    @property
    def level(self):
        return self._level

    @property
    def name(self):
        return self._name

    @property
    def cd(self):
        return self._name

    @staticmethod
    def parse_skill(skill_info: dict):
        if 'level' in skill_info \
                and 'name' in skill_info \
                and 'cd' in skill_info \
                and 'damage' in skill_info:
            return Skill(skill_info['level'], skill_info['name'], skill_info['cd'], skill_info['damage'])
        else:
            return None


if __name__ == '__main__':
    print(Skill.parse_skill({'name': '大冰', 'cd': '20', 'level': 60, 'damage': 100}))
