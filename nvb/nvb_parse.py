
def f1(asciiBlock, floatList):
    #floatList = [float(l[0]) for l in asciiBlock]
    l_float = float
    for line in asciiBlock:
        floatList.append(l_float(line[0]))


def f2(asciiBlock, floatList):
    #floatList = [(float(l[0]), float(l[1])) for l in asciiBlock]
    l_float = float
    for line in asciiBlock:
        floatList.append( (l_float(line[0]), l_float(line[1])) )


def f3(asciiBlock, floatList):
    #floatList = [(float(l[0]), float(l[1]), float(l[2])) for l in asciiBlock]
    l_float = float
    for line in asciiBlock:
        floatList.append( (l_float(line[0]), l_float(line[1]), l_float(line[2])) )


def f4(asciiBlock, floatList):
    #floatList = [(float(l[0]), float(l[1]), float(l[2]), float(l[3])) for l in asciiBlock]
    l_float = float
    for line in asciiBlock:
        floatList.append( (l_float(line[0]), l_float(line[1]), l_float(line[2]), l_float(line[3])) )


def f5(asciiBlock, floatList):
    #floatList = [(float(l[0]), float(l[1]), float(l[2]), float(l[3]), float(l[4])) for l in asciiBlock]
    l_float = float
    for line in asciiBlock:
        floatList.append( (l_float(line[0]),
                           l_float(line[1]),
                           l_float(line[2]),
                           l_float(line[3]),
                           l_float(line[4])) )


def txt(asciiBlock, txtBlock):
    #txtBlock = ['\n'+' '.join(l) for l in aciiBlock]
    for line in asciiBlock:
        txtBlock = txtBlock + '\n' + ' '.join(line)

