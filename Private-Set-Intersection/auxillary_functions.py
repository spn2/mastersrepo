def read_file_return_list(filename):
    with open(filename) as f:
        return [line.rstrip() for line in f]
    
def read_file_return_list1(filename):
    lines = []
    with open(filename) as f:
        for line in f:
            lines.append(line)
    return lines

def read_file_return_list2(filename):
    lines = []
    with open(filename) as f:
        while (line := f.readline().rstrip()):
            lines.append(line)
    return lines
