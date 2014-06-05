---
layout: post
title: "Bit reversal permutation in Python"
description: ""
category:
tags: []
---
{% include JB/setup %}
{% excerpt %}
For the [FFT sonification](http://ryancompton.net/2014/05/24/algorithm-sonification-iii-the-fft/) I needed to implement my own FFT in order to keep track of which notes are being played while the Fourier transform executes. It turns out that implementing an FFT isn’t too difficult as long as you don’t care how fast it goes (Note: if you do need it to be fast you’ll have a hard time beating fftw which “is an implementation of the discrete Fourier transform (DFT) that adapts to the hardware in order to maximize performance” (cf <http://www.fftw.org/fftw-paper-ieee.pdf>) ).

The key ingredient to implementing an FFT with the [Cooley-Tukey algorithm](https://en.wikipedia.org/wiki/Cooley%E2%80%93Tukey_FFT_algorithm) (which I used for the sonification) is a traversal of the input array in [bit-reversed](https://en.wikipedia.org/wiki/Bit-reversal_permutation) order. Here’s how I did the traversal in Python:

{% highlight python %}
def bit_reverse_traverse(a):
    n = a.shape[0]
    assert(not n&(n-1) ) # assert that n is a power of 2

    if n == 1:
        yield a[0]
    else:
        even_index = arange(n/2)*2
        odd_index = arange(n/2)*2 + 1
        for even in bit_reverse_traverse(a[even_index]):
            yield even
        for odd in bit_reverse_traverse(a[odd_index]):
            yield odd

    return
{% endhighlight %}

What I thought was interesting about this code was that I had to use Python’s `yield` statement, which I had never run into before.
{% endexcerpt %}

In short, Python’s yield statement is useful when you need to perform recursion efficiently. The difference between a yield statement and a return statement is that yield produces a generator which executes your code on-the-fly rather than storing the entire recursive tree in memory (cf <http://stackoverflow.com/a/231855/424631> for more). So, instead of having a global list to write the output of our recursive calls we use a yield statment to make a generator that runs through our list in bit reversed order. Doing something like `z=bit_reverse_traverse(a)` and then several `z.next()`s will go through a in the bit-reversed way without eating up all the memory needed for a deep recursive tree. Here's the code to use the generator:

{% highlight python %}
def get_bit_reversed_list(l):
    n = len(l)

    indexs = arange(n)
    b = []
    for i in bit_reverse_traverse(indexs):
        b.append(l[i])

    return b
{% endhighlight %}



