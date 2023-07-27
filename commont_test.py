def max_damage(skill_cooldowns, skill_damages, time):
    skill_sqeue = []
    dp = [0] * (time + 1)
    for i in range(1, time + 1):
        for j in range(len(skill_cooldowns)):
            if i >= skill_cooldowns[j]:
                old = dp[i]
                new = dp[i - skill_cooldowns[j]] + skill_damages[j]
                dp[i] = max(old, new)
                if new > old:
                    skill_sqeue.append(skill_damages[j])
                else:
                    skill_sqeue.append('')
    return dp[time], skill_sqeue

skill_cooldowns = [1, 2, 5, 10]
skill_damages = [10, 15, 30, 50]
time = 30

print(max_damage(skill_cooldowns, skill_damages, time))
