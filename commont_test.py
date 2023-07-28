dic = {'a': {'res_cd': 1, 'cnt': 2}, 'b': {'res_cd': 3, 'cnt': 2}, 'c': {'res_cd': 2, 'cnt': 2}}

sorted_skill_status_list = sorted(dic.items(), key=lambda x: x[1]['res_cd'], reverse=True)
print(sorted_skill_status_list[0][0])
