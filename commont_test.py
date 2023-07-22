from itertools import combinations, product, permutations

colors = ['red', 'blue', 'purple']
fuwen_skill_sets = ['呀呀呀', '不动', '炸热']
# 将每个技能都复制3个
fuwen_skill_pool = [x for x in fuwen_skill_sets for i in range(3)]
print(fuwen_skill_pool)

fuwen_result = []
for fuwen_skill_set in set(combinations(fuwen_skill_pool, 3)):
    # 求该set的排列，并与color 11对应生成符文组合
    for fuwen_set in set(permutations(fuwen_skill_set, 3)):
        case = {}
        for i in range(len(colors)):
            color = colors[i]
            skill = fuwen_set[i]
            case[color] = {skill: 3}
        fuwen_result.append(case)
print(fuwen_result)
