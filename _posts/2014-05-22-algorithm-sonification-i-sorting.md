---
layout: post
title: "Algorithm Sonification I: Sorting"
description: ""
category:
tags: ["audio", "coding"]
redirect_from:
  - /2014/05/22/algorithm-sonification-i-sorting/
---



*Originally published in 2009 at [http://www.math.ucla.edu/~rcompton/musical_sorting_algorithms/musical_sorting_algorithms.html](http://www.math.ucla.edu/~rcompton/musical_sorting_algorithms/musical_sorting_algorithms.html)*

Suppose you drop a set of drums and they land randomly ordered in a row on the floor. You want to put the drums back in order but can only pick up and swap two at a time. A good strategy to minimize the number of swaps you must make is to follow the Quicksort algorithim [http://en.wikipedia.org/wiki/Quicksort](http://en.wikipedia.org/wiki/Quicksort).

If you order the drums by their general MIDI number and simultaneously strike any two which you swap then you will produce a sound similar to this:

[https://www.youtube.com/watch?v=g2IWUd3p30I](https://www.youtube.com/watch?v=g2IWUd3p30I)

<!--more-->

To hear what's going on with quick sort a little better consider the case where you have dropped 12 guitar strings whose frequencies vary expoentially, ie

frequency of string $$i = 220.0*( 2.0^{\frac{i}{12.0}} )$$

for $$i=0,...,11$$ for more information [http://en.wikipedia.org/wiki/Pitch_(music)](http://en.wikipedia.org/wiki/Pitch_(music))

[https://www.youtube.com/watch?v=YR6VAZUGAMo](https://www.youtube.com/watch?v=YR6VAZUGAMo)

I could not hear what's going on all that well either. An aesthetically pleasing quadratic running time strategy you may follow is insertion sort [http://en.wikipedia.org/wiki/Insertion_sort]( http://en.wikipedia.org/wiki/Insertion_sort). Here's how insertion sort sounds in a scenario involving many more strings on the floor:

[https://www.youtube.com/watch?v=DNAmWDmIAZQ](https://www.youtube.com/watch?v=DNAmWDmIAZQ)

And if you were to sort drums with insertion sort you would get something like this:

[https://www.youtube.com/watch?v=zXTlRc6QM-M](https://www.youtube.com/watch?v=zXTlRc6QM-M)

The sounds were made using STK [http://ccrma.stanford.edu/software/stk/](http://ccrma.stanford.edu/software/stk/) the videos were made using the python gnuplot module [http://gnuplot-py.sourceforge.net](http://gnuplot-py.sourceforge.net) and mencoder. The source is at [https://code.google.com/p/musical-sorting-algorithms/](https://code.google.com/p/musical-sorting-algorithms/)


**Update 2009-08-11:**
[This got written up in Make](https://web.archive.org/web/20090827005157/http://blog.makezine.com/archive/2009/08/musical_sorting_algorithms.html)

