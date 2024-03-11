解析Java文件中特定方法参数的值：
1. test_get_args_from_method_by_parser:使用javalang库解析
2. test_parser_string_method:字符串解析(仅实现单文件)


![image](https://github.com/FantasyLu/parse_java/assets/24392339/9adccdda-be7c-4af4-91df-8e7470f1c59f)
对于单个工程而言：
1. 遍历工程文件，找java文件并解析为AST
2. 寻找与目标方法名相同的方法调用
3. 按照规则查找方法中的参数，看是否是字面量，如果是则获得取值添加到结果中，返回1，否则到4
4. 在本java文件中寻找参数的赋值语句，找到则继续5，否则6
5. 判断赋值是否为字面量，如果是则获取取值并添加，否则返回4
6. 遍历工程文件，重复3-5

可以支持内容：
1. 字面量 如 "allow_linkmic_pk"
2. 赋值/多次赋值的非字面量，如 String a = "allow_linkmic_pk" / String a = "allow_linkmic_pk", String b = a.

支持不到的：
1. 通过表达式计算得到的 ('a' + 'b')，add到list中的
2. 非代码中的 如 数据表 或 配置 等
3. 参数作为方法里的形参 （无法解析里占比最多）
