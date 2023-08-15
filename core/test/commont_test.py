import numpy as np
import matplotlib.pyplot as plt

# 类别名称
categories = ['Category 1', 'Category 2', 'Category 3', 'Category 4']

# 分组数据
group_A = [10, 15, 17, 12]
group_B = [12, 16, 16, 15]
group_C = [14, 12, 14, 18]
group_D = [19, 11, 17, 13]
# 组宽度设置
bar_width = 0.1

# 创建索引
index = np.arange(len(categories))

# 画条形图
plt.bar(index, group_A, bar_width, label='Group A')
plt.bar(index + bar_width, group_B, bar_width, label='Group B')
plt.bar(index + 2 * bar_width, group_C, bar_width, label='Group C')
plt.bar(index + 3 * bar_width, group_D, bar_width, label='Group D')

# 设置X轴和Y轴标签
plt.xlabel('Category')
plt.ylabel('Value')

# 设置图例
plt.legend()

# 设置条形图的标题
plt.title('Grouped Bar Plot in Python')

# 设置x轴刻度标签
# plt.xticks(index + bar_width, categories)

# 显示图形
plt.show()
