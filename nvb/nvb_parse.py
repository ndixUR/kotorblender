"""TODO: DOC."""

def _f(asciiBlock, floatList, numVals):
    """Parse floats into a numVals tuple into floatList"""
    l_float = float
    for line in asciiBlock:
        vals = []
        for idx in range(0, numVals):
            vals.append(l_float(line[idx]))
        if len(vals) > 1:
            floatList.append(tuple(vals))
        else:
            floatList.append(vals[0])

def f1(asciiBlock, floatList):
    """Parse a series on floats into a list."""
    _f(asciiBlock, floatList, 1)

def f2(asciiBlock, floatList):
    """Parse a series on float tuples into a list."""
    _f(asciiBlock, floatList, 2)

def f3(asciiBlock, floatList):
    """Parse a series on float 3-tuples into a list."""
    _f(asciiBlock, floatList, 3)

def f4(asciiBlock, floatList):
    """Parse a series on float 4-tuples into a list."""
    _f(asciiBlock, floatList, 4)

def f5(asciiBlock, floatList):
    """Parse a series on float 5-tuples into a list."""
    _f(asciiBlock, floatList, 5)

def i2(asciiBlock, intList):
    l_int = int
    for line in asciiBlock:
        intList.append((l_int(line[0]), l_int(line[1])))

def txt(asciiBlock, txtBlock):
    """TODO: DOC."""
    # txtBlock = ['\n'+' '.join(l) for l in aciiBlock]
    for line in asciiBlock:
        txtBlock = txtBlock + '\n' + ' '.join(line)
