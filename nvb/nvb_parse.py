"""TODO: DOC."""


def f1(asciiBlock, floatList):
    """Parse a series on floats into a list."""
    # floatList = [float(l[0]) for l in asciiBlock]
    l_float = float
    for line in asciiBlock:
        floatList.append(l_float(line[0]))


def f2(asciiBlock, floatList):
    """Parse a series on float tuples into a list."""
    # floatList = [(float(l[0]), float(l[1])) for l in asciiBlock]
    l_float = float
    for line in asciiBlock:
        floatList.append((l_float(line[0]),
                          l_float(line[1])))


def f3(asciiBlock, floatList):
    """Parse a series on float 3-tuples into a list."""
    l_float = float
    for line in asciiBlock:
        floatList.append((l_float(line[0]),
                          l_float(line[1]),
                          l_float(line[2])))


def f4(asciiBlock, floatList):
    """Parse a series on float 4-tuples into a list."""
    l_float = float
    for line in asciiBlock:
        floatList.append((l_float(line[0]),
                          l_float(line[1]),
                          l_float(line[2]),
                          l_float(line[3])))


def f5(asciiBlock, floatList):
    """Parse a series on float 5-tuples into a list."""
    l_float = float
    for line in asciiBlock:
        floatList.append((l_float(line[0]),
                          l_float(line[1]),
                          l_float(line[2]),
                          l_float(line[3]),
                          l_float(line[4])))


def txt(asciiBlock, txtBlock):
    """TODO: DOC."""
    # txtBlock = ['\n'+' '.join(l) for l in aciiBlock]
    for line in asciiBlock:
        txtBlock = txtBlock + '\n' + ' '.join(line)
