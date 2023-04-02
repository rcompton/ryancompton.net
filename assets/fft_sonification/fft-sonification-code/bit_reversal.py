#
# Recursive way to code up a bit reversal
# Basically the same thing as recursive fft
# it would be more stylish to write this as a
# "butterfly" algorithm like they do for
# in place ffts
#


from numpy import *


# This was the neat thing. Instead of having a global
# list to write the output of our recursive calls we
# use a yield statment to make a generator that runs
# through a list in bit reversed order.
# so, doing something like z=bit_reverse_traverse(a)
# and then a bunch of z.next()s will go through a in
# the bit reversed way.
# note: when you want to make a generator recursive
# you don't just "call" the generator but have to remember
# that the generator is a generator and not a function
# hence the recursive call inside of the the "for" iterator
#
#
# By the way, this sucks because it requires n to be
# a power of 2...
# uh, fixable with "butterfly"
#
def bit_reverse_traverse(a):
    n = a.shape[0]

    # if you want the code to work and give
    # the right results then you need
    # this to be in the code.
    # but if you leave it out you still get something,
    # just the output array is the wrong length...
    # assert(not n&(n-1) )

    if n == 1:
        yield a[0]
    else:
        even_index = arange(n / 2) * 2
        odd_index = arange(n / 2) * 2 + 1
        for even in bit_reverse_traverse(a[even_index]):
            yield even
        for odd in bit_reverse_traverse(a[odd_index]):
            yield odd

    return


# not so neat, basically just call .next() a bunch
# and wrap the results of bitreversing the indicies
# into list indicies
def get_bit_reversed_list(l):
    n = len(l)

    indexs = arange(n)
    b = []
    for i in bit_reverse_traverse(indexs):
        b.append(l[i])

    return b


def main():
    fin = open("./test_pitch.txt")
    scale = fin.readlines()
    fin.close()

    rev_scale = get_bit_reversed_list(scale)

    out = open("./reversed_test_pitch.txt", "w")
    out.writelines(rev_scale)
    out.close()

    return


if __name__ == "__main__":
    main()
