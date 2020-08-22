---
layout: post
title: "Supervised Learning Superstitions Cheat Sheet"
description: ""
category:
tags: ["coding", "machine learning"]
redirect_from:
  - /2014/05/02/machine-learning-superstitions-cheat-sheet
---


This notebook contains notes and beliefs about several commonly-used supervised learning algorithms. My dream is that it will be useful as a quick reference or for people who are irrational about studying for machine learning interviews.

The methods discussed are:

+ Logistic regression
+ Decision trees
+ Support vector machines
+ K-nearest neighbors
+ Naive Bayes

To see how different classifiers perform on datasets of varying quality I've plotted empirical decisions boundaries after training each classifier on "two moons". For example, here's what happens to scikit-learn's decision tree (which uses a version of the CART algorithm) at different noise levels and training sizes:

![tree]({{site.url}}/assets/ml_cheat_sheet/tree.png)

Here's the notebook:
<http://ryancompton.net/assets/ml_cheat_sheet/supervised_learning.html>

(as a .ipynb file: <http://ryancompton.net/assets/ml_cheat_sheet/supervised_learning.ipynb>)
