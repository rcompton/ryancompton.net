---
layout: post
title: "Algorithm Sonification III: The FFT"
description: ""
category:
tags: ["audio", "coding"]
redirect_from:
  - /2014/05/24/algorithm-sonification-iii-the-fft./
---



*Originally published in 2009 at [http://www.math.ucla.edu/~rcompton/fft_sonification/fft_sonification.html](http://www.math.ucla.edu/~rcompton/fft_sonification/fft_sonification.html)*

The FFT is an essential tool for digital signal processing and electronic music production. It is easily, commonly, and inefficiently implemented via the recursive Cooley-Tukey algorithm which we now briefly review.

To compute the discrete Fourier transform, $$\{ X_k \}_{k=0}^{N-1}$$, of a sequence, $$\{ x_n \}_{n=0}^{N-1}$$, we must sum

$$
\begin{equation*}
X_k = \sum_{n=0}^{N-1} x_n e^{\frac{-2 \pi i}{N}nk}
\end{equation*}
$$

for each $k$ in $0, ..., N-1$. Using the [Danielson-Lanczos lemma](http://mathworld.wolfram.com/Danielson-LanczosLemma.html), we split the above sum into its even and odd constituents

$$
 \begin{eqnarray*}
X_k &=& \sum_{n=0}^{N/2-1} x_{2n} e^{\frac{-2 \pi i}{N}(2n)k} + \sum_{n=0}^{N/2-1} x_{2n+1} e^{\frac{-2 \pi i}{N}(2n+1)k} \\
&=& X_{\text{even }k} + e^{\frac{-2 \pi i}{N}k} X_{\text{odd }k}
\end{eqnarray*}
$$
<!--more-->


where $$X_{\text{even }k}$$ and $$X_{\text{odd }k}$$ are the $$k$$th component of the DFT of the sequences obtained by selecting only the even or odd members from $$\{ x_n \}$$. In this manner we compute the DFT by recursively computing the DFT of the even and odd subsequences of $$\{ x_n \}$$. By the time that $$N=1$$ our DFT is simply the identity mapping from the constant sequence into the constant mode in Fourier space.

Now, suppose that in our initial array we store values corresponding to the frequencies of the usual western equally tempered scale.

$$
 \begin{equation*}
x_n = 220.0*2^{\frac{n}{12}}
\end{equation*}
$$

and execute our DFT algorithm on $$\{ x_n \}$$ while playing the corresponding frequency on a guitar each time we reach the base case in our recursion. This will play the notes of the scale in bit reversed order and simultaneously allow us a tool for digital signal processing.

Here's how it sounds: [fast_fourier_music.wav]({{ site.url }}/assets/fft_sonification/fast_fourier_music.wav)

Audio is made in C++ with STK. Here's the source code: [https://bitbucket.org/rcompton/fft-sonification/src](https://bitbucket.org/rcompton/fft-sonification/src)
