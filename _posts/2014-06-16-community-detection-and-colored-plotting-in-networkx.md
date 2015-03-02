---
layout: post
title: "Community detection and colored plotting in networkx"
description: ""
category:
tags: ["coding"]
---
{% include JB/setup %}
Just came across this very easy library for community detection <https://sites.google.com/site/findcommunities/> <https://bitbucket.org/taynaud/python-louvain/src>. Here's how to create a graph, detect communities in it, and then visualize with nodes colored by their community in less than 10 lines of python:

{% highlight python %}
import networkx as nx
import community

G = nx.random_graphs.powerlaw_cluster_graph(300, 1, .4)

part = community.best_partition(G)
values = [part.get(node) for node in G.nodes()]

nx.draw_spring(G, cmap = plt.get_cmap('jet'), node_color = values, node_size=30, with_labels=False)
{% endhighlight %}

![community structuree]({{ site.url }}/assets/pix/random_graph_communities.png)

It's easy to get [modularity](https://en.wikipedia.org/wiki/Modularity_%28networks%29) to:
{% highlight python %}
mod = community.modularity(part,G)
print("modularity:", mod)
{% endhighlight %}
gave `modularity: 0.8700238252368541`, which is quite high.
