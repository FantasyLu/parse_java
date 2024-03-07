import re

"""
解析Java文件中特定方法参数的值 —— 使用javalang库
"""
def extract_string(arg, from_list, file_path):
    arg = arg.strip()
    if not from_list:
        if arg.startswith('"') and arg.endswith('"'):
            return arg
        else:
            with open(file_path, 'r', encoding='utf-8') as file:
                content = read_content_without_comment(file)
                pattern = rf'String\s+{arg}\s*=\s*"(.*?)";'
                match = re.search(pattern, content)
                if match:
                    return match.group(1)
                else:
                    pattern = r'String\s+\w+\s*=\s*(\w+);'
                    match = re.search(pattern, content)
                    if match:
                        var = match.group(1)
                        return extract_string(var, from_list, file_path)
                    else:
                        return None

    else:
        if arg.startswith('Lists.newArrayList(') or arg.startswith('Arrays.asList(') or arg.startswith('List.of('):
            str = arg[arg.index('(') + 1: arg.rindex(')')].split(',')
            return extract_values_from_list(file_path, str)
        else:
            # 从文件中查找
            with open(file_path, 'r', encoding='utf-8') as file:
                content = read_content_without_comment(file)
                # 匹配 List<String> arg = Lists.newArrayList(....); 或 Arrays.asList() 或 List.of()
                pattern = rf'List<String>\s+{arg}\s*=\s*(?:Lists\.newArrayList\(|Arrays\.asList\(|List\.of\()\s*(.*?)(?:\)|;)'
                # pattern = rf'List<String>\s+{arg}\s*=\s*Lists\.newArrayList\((.*?)\);'
                match = re.search(pattern, content)
                if match:
                    extracted_list = match.group(1).split(',')
                    return extract_values_from_list(file_path, extracted_list)
                else:
                    return None


def read_content_without_comment(file):
    content = file.read()
    content = re.sub(r'//.*?\n|/\*.*?\*/', '', content, flags=re.MULTILINE | re.DOTALL)
    return content


def extract_values_from_list(file_path, extracted_list):
    list = []
    for item in extracted_list:
        if "\"" in item:
            list.append(item.strip())
        else:
            list.append(extract_string(item, False, file_path))
    return list


def find_nested_parens_content(method_call):
    stack = []
    start_index = None

    for i, char in enumerate(method_call):
        if char == '(':
            if not stack:
                start_index = i
            stack.append(char)
        elif char == ')':
            if stack and stack[-1] == '(':
                if len(stack) == 1:
                    return method_call[start_index + 1:i]
                else:
                    stack.pop()
    raise ValueError("Invalid string. No matching closing parenthesis found.")


def find_arg_by_param_index(full_args_string, param_index):
    # 找到第param_index和param_index+1个不在()中的逗号的位置
    stack = []
    comma_indices = []
    for i, char in enumerate(full_args_string):
        if char == '(':
            stack.append(char)
        elif char == ')':
            if stack and stack[-1] == '(':
                stack.pop()
        elif char == ',' and len(stack) == 0:
            comma_indices.append(i)
    return full_args_string[comma_indices[param_index-1]+1: comma_indices[param_index]]


def find_flag_values(file_path, target_strings):
    results = []

    with open(file_path, 'r', encoding='utf-8') as file:
        content = read_content_without_comment(file)

        for target, param_index, from_list in target_strings:
            pattern = rf'({target}\s*\(.*?\);)'
            matches = re.findall(pattern, content, re.DOTALL)

            for match in matches:
                method_call = match.strip()

                # 解析出第index个参数
                full_args_string = find_nested_parens_content(method_call)
                call_arg = find_arg_by_param_index(full_args_string, param_index)
                target_arg = extract_string(call_arg, from_list, file_path)

                line_num = content.count('\n', 0, content.find(match)) + 1

                results.append({
                    'target': target,
                    'line_number': line_num,
                    'method_call': method_call,
                    'second_argument': target_arg
                })

    return results


target_methods = [('getFlagValueByDeviceAndFlagNames', 1, True), ('getIntFlagValueOrDefaultValueByUser', 1, False)]
file_path = '../parse_java/test_parser/BaseExpManager.java'

found_results = find_flag_values(file_path, target_methods)

for result in found_results:
    print(f"Target: {result['target']}")
    print(f"Line Number: {result['line_number']}")
    print(f"Method Call: {result['method_call']}")
    print(f"Second Argument: {result['second_argument']}\n")
