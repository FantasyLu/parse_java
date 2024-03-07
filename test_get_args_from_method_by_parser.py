import os
import re
import javalang
import javalang.tree
from javalang.parser import JavaSyntaxError
import time
import pandas as pd


def parse_java_project(project_path, method_name, param_index, get_from_list):
    """
    解析Java工程中特定方法参数的值 —— 使用javalang库

    @param project_path 工程路径
    @param method_name 要查找的方法名
    @param param_index 方法参数的索引（从0开始）
    @param get_from_list 是否从列表中获取参数值
    @return 返回一个元组，包含结果列表和错误文件集合
    """
    res = []
    error_set = set()
    for root, dirs, files in os.walk(project_path):
        for file in files:
            if file.endswith('.java'):
                with open(os.path.join(root, file), 'r') as java_file:
                    print(java_file)
                    # 忽略已出错的文件
                    if java_file.name in error_set:
                        continue
                    code = java_file.read()
                    try:
                        tree = javalang.parse.parse(code)
                    except JavaSyntaxError:
                        # 记录无法解析的文件
                        print('error parsing file: ' + java_file.name)
                        error_set.add(java_file.name)
                        continue
                    # 查找方法调用
                    for path, node in tree.filter(javalang.tree.MethodInvocation):
                        extract_arg_value_from_file(error_set, file, get_from_list, method_name, node, param_index,
                                                    project_path, res, root, tree)
    res = sorted(res, key=lambda x: (x[0] is None, x))
    # res = sorted(res, key=lambda x: int(x[2]))
    return res, error_set


def extract_arg_value_from_file(error_set, file, get_from_list, method_name, node, param_index, project_path, res, root,
                                tree):
    """
    从文件中提取特定方法参数的值。

    @param error_set 出错文件集合
    @param file 当前处理的文件名
    @param get_from_list 是否从列表中获取参数值
    @param method_name 要查找的方法名
    @param node 当前解析的节点
    @param param_index 方法参数的索引（从0开始）
    @param project_path 工程路径
    @param res 结果集合
    @param root 当前文件所在的目录
    @param tree 当前文件的语法树
     """
    if node.member == method_name:
        param = node.arguments[param_index]
        literal_value = None
        list_args_value = []
        if not get_from_list:
            # 非列表方式获取参数值
            if isinstance(param, javalang.tree.Literal):
                literal_value = extract_literal_value(literal_value, param)
            elif isinstance(param, javalang.tree.MemberReference):
                # 需要进一步解析非字面量的来源
                literal_value = find_literal_assignment(tree, param.member, get_from_list)
                if literal_value is None:
                    # 在整个工程中查找
                    literal_value = find_literal_assignment_in_project(project_path, param.member,
                                                                       get_from_list, error_set)
        else:
            # 从列表中获取参数值
            if isinstance(param, javalang.tree.MemberReference):
                list_args_value = find_literal_assignment(tree, param.member, get_from_list)
                if len(list_args_value) == 0:
                    # 在整个工程中查找
                    list_args_value = find_literal_assignment_in_project(project_path, param.member,
                                                                         get_from_list, error_set)
            elif isinstance(param, javalang.tree.MethodInvocation):
                # 特殊处理List的构造方法
                if param.member in ['newArrayList', 'asList'] or (param.member == 'of' and param.qualifier == 'List'):
                    member_value = [arg for arg in param.arguments]
                    for value in member_value:
                        if isinstance(value, javalang.tree.Literal):
                            list_args_value.append(extract_literal_value(None, value))
                        else:
                            list_args_value.append(find_literal_assignment(tree, value.member, get_from_list))

        # 根据获取方式，添加结果
        if get_from_list:
            for value in list_args_value:
                res.append((value, os.path.join(root, file), node.position.line))
        else:
            res.append((literal_value, os.path.join(root, file), node.position.line))


def extract_literal_value(literal_value, param):
    """
    提取字面量值。
    @param literal_value 当前字面量值
    @param param 参数节点
    @return 提取的字面量值
    """
    if isinstance(param.value, str):
        literal_value = param.value
    elif isinstance(param.value, list):
        literal_value = [element.value for element in param.value]
    return literal_value


def find_literal_assignment_in_project(project_path, variable_name, get_from_list, error_set):
    """
    在整个工程中查找字面量的赋值。

    @param project_path 工程路径
    @param variable_name 变量名
    @param get_from_list 是否从列表中获取
    @param error_set 出错文件集合
    @return 字面量的值，如果未找到返回None
    """
    for root, dirs, files in os.walk(project_path):
        for file in files:
            if file.endswith('.java'):
                with open(os.path.join(root, file), 'r') as java_file:
                    if java_file.name in error_set:
                        continue
                    code = java_file.read()
                    try:
                        tree = javalang.parse.parse(code)
                    except JavaSyntaxError:
                        print('error parsing file while find literal assignment in project: ' + java_file.name)
                        error_set.add(java_file.name)
                        continue
                    literal_value = find_literal_assignment(tree, variable_name, get_from_list)
                    if literal_value is not None:
                        return literal_value
    return None


def find_literal_assignment(tree, variable_name, get_from_list):
    """
    在给定的语法树中查找字面量的赋值。

    @param tree 语法树
    @param variable_name 变量名
    @param get_from_list 是否从列表中获取
    @return 字面量的值，如果未找到返回None
     """
    # 存储已检查过的节点路径，避免无限循环
    checked_nodes = set()

    def find_literal_recursively(node, get_from_list):
        if node in checked_nodes:
            return None
        checked_nodes.add(node)

        # 检查当前节点是否是Assignment，且目标与目标变量名匹配
        if isinstance(node, javalang.tree.Assignment) and getattr(node.expressionl, 'member', None) == variable_name:
            # 如果是一个字面量则返回
            if isinstance(node.value, javalang.tree.Literal):
                return extract_literal_value(None, node.value)
            # 否则尝试递归查找
            else:
                for sub_node in node.value.filter(javalang.tree.Assignment):
                    result = find_literal_recursively(sub_node, get_from_list)
                    if result is not None:
                        return result
        if isinstance(node, javalang.tree.LocalVariableDeclaration):
            for declarator in node.declarators:
                if declarator.name == variable_name and isinstance(declarator.initializer, javalang.tree.Literal):
                    value = extract_literal_value(None, declarator.initializer)
                    if value is not None:
                        return value
                if (declarator.name == variable_name) and isinstance(declarator.initializer,
                                                                     javalang.tree.MethodInvocation):
                    if get_from_list:
                        list_args_value = []
                        param = declarator.initializer
                        if (param.member in ['newArrayList', 'asList']
                                or (param.member == 'of' and param.qualifier == 'List')):
                            member_value = [arg for arg in param.arguments]
                            for value in member_value:
                                if isinstance(value, javalang.tree.Literal):
                                    list_args_value.append(extract_literal_value(None, value))
                                else:
                                    list_args_value.append(find_literal_assignment(tree, value.member, get_from_list))
                        return list_args_value
                    else:
                        # 来源于方法调用
                        return None
                if (declarator.name == variable_name) and isinstance(declarator.initializer,
                                                                     javalang.tree.MemberReference):
                    return find_literal_assignment(tree, declarator.initializer.member, get_from_list)
        # 检查当前节点是否是FieldDeclaration，且变量名匹配
        if isinstance(node, javalang.tree.FieldDeclaration):
            for declarator in node.declarators:
                if declarator.name == variable_name and isinstance(declarator.initializer, javalang.tree.Literal):
                    value = extract_literal_value(None, declarator.initializer)
                    if value is not None:
                        return value

        # 递归遍历子节点
        for path, child_node in node.filter(javalang.tree.Node):
            result = find_literal_recursively(child_node, get_from_list)
            if result is not None:
                return result

    # 在整个AST中寻找字面量赋值
    return find_literal_recursively(tree, get_from_list)


def find_string_in_file(file_path_set, string_list):
    result = []
    for file_path in file_path_set:
        with open(file_path, 'r') as file:
            for number, line in enumerate(file, start=1):
                for string in string_list:
                    if string in line and not is_comment_line(line):
                        result.append((string, file_path, number))
    return result


def is_comment_line(line):
    pattern = r'^\s*\/\/'
    return bool(re.match(pattern, line))


def parse_java_project_list(project_path_list, target_method_list):
    result = []
    param_indices = [method_name[0] for method_name in target_method_list]
    for project_path in project_path_list:
        find_error_path_set = set()
        literal_list = []
        for method_name, param_index, get_from_list in target_method_list:
            res, error_set = parse_java_project(project_path, method_name, param_index, get_from_list)
            literal_list.extend(res)
            find_error_path_set = find_error_path_set.union(error_set)
        error_path = find_string_in_file(find_error_path_set, param_indices)
        result.append((project_path, literal_list, error_path))
    return result


def generate_table(list_result):
    df_list = []
    for project_path, result, _ in list_result:
        result_df = pd.DataFrame(result, columns=['Literal Value', 'File Path', 'Line Number'])

        result_df['Project Path'] = project_path

        df_list.append(result_df)

    df = pd.concat(df_list, ignore_index=True)
    df.to_excel('output_racing.xlsx', index=False)


def test_parse_java_project():
    project_path_list = ['live-admin-service', 'live-base-api', 'pangu', 'push-peregrine', 'rec-gemini', 'search-leo']
    # project_path_list = ['/Users/luhao/IdeaProjects/racing']
    # project_path_list = ['test_parser']
    method_name_1 = 'getFlagValueByDeviceAndFlagNames'
    param_index_1 = 1
    get_from_list_1 = True

    method_name_2 = 'getIntFlagValueOrDefaultValueByUser'
    param_index_2 = 1
    get_from_list_2 = False

    target_method_list = [(method_name_1, param_index_1, get_from_list_1),
                          (method_name_2, param_index_2, get_from_list_2)]

    start_time = time.time()
    list_result = parse_java_project_list(project_path_list, target_method_list)
    end_time = time.time()
    execution_time = end_time - start_time
    print(f"代码执行耗时: {execution_time} 秒")

    for project_path, result, error_set in list_result:
        print('=' * 200)
        print(project_path)
        print(len(result))
        print('\n'.join(map(str, result)))

        if error_set:
            print("如下包含方法的类未能成功解析:")
            print('\n'.join(map(str, error_set)))
    # generate_table(list_result)


if __name__ == '__main__':
    test_parse_java_project()
