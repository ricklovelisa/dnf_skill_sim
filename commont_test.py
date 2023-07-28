# 定义一个简单的树节点类
class Node:
    def __init__(self, value, left=None, right=None):
        self.value = value
        self.left = left
        self.right = right

# 定义遍历树的函数
def traverse_tree(root, path=''):
    # 如果节点为空，则直接返回
    if root is None:
        return []
    # 将当前节点添加到路径上
    path += str(root.value)
    # 如果当前节点是叶子节点，则返回当前路径
    if root.left is None and root.right is None:
        return [path]
    else:
        # 否则，递归遍历左子树和右子树，并将结果合并
        return traverse_tree(root.left, path+'->') + traverse_tree(root.right, path+'->')

# 建立一个树来测试
root = Node(1)
root.left = Node(2)
root.right = Node(3)
root.left.left = Node(4)
root.left.right = Node(5)

# 输出所有路径
print(traverse_tree(root))