# to convert 'string' into 'integer' (don't use 'int' function)
def int1(s):
    negative = '-' in s
    s = s.replace('-', '').strip()
    def mapping(s):
        return {k: ord(k) - 48 for k in '0123456789'}[s]
    r = reduce(lambda x, y: x*10 + y, map(mapping, s))
    return -r if negative else r
# print int1('12312132')
# print int1('-12312132')
# to count duplicated elements in a list
a = [1,1,1,1,2,2,2,2,3,3,4,5,5]
def find_num(array, ele):
    return len(filter(lambda x: x==ele, array))

# print find_num(a,3)

# read and parse a config file
import re
def parse_conf(config_path):
    section_pattern = re.compile(r'\[(.*)\]')
    option_pattern = re.compile(r'([a-z_ ]+)=(.+)')
    fileobj = open('db.conf')
    now_section = None
    config = {}
    for line in fileobj.readlines():
        if section_pattern.search(line):
            key = section_pattern.findall(line)[0]
            config[key] = {}
            now_section = key
        elif option_pattern.search(line):
            key, val = option_pattern.findall(line)[0]
            config[now_section][key] = val.strip()
    return config
print parse_conf('db.conf')
