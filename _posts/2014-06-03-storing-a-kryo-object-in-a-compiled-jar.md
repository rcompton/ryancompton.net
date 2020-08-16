---
layout: post
title: "Storing a Kryo object in a compiled jar"
description: ""
category:
tags: ["coding"]
---



This really threw me off for a while (cf [https://stackoverflow.com/questions/23748254/storing-a-kryo-object-in-a-compiled-jar](https://stackoverflow.com/questions/23748254/storing-a-kryo-object-in-a-compiled-jar) ).

I had a `HashMap` I needed to persist and have fast access to. I used Kryo to serialize the object

{% highlight java %}
Kryo kryo = new Kryo();
MapSerializer serializer = new MapSerializer();
kryo.register(Location.class);
kryo.register(HashMap.class, serializer);

Output output = new Output(new FileOutputStream("src/main/resources/locations50K.kryo"));
kryo.writeObject(output, locationMap);
output.close();
{% endhighlight %}
<!--more-->

I successfully deserialized with

{% highlight java %}
Input input = new Input(new FileInputStream("src/main/resources/locations50K.kryo"));
Map<String, Location> locationMap;
locationMap = kryo.readObject(input, HashMap.class);
input.close();

log.info(locationMap.size());
{% endhighlight %}

the `log.info` showed 231,045 entries in my map.

Now, in order to access the .kryo file after compiling a *-jar-with-dependencies.jar (using Maven) I needed to replace `FileInputStream` with `MyClass.class.getResourceAsStream`

{% highlight java %}
InputStream isr = MyClass.class.getResourceAsStream("/locations50K.kryo");

if(isr == null)
  log.error("null input");

Input input = new Input(isr);
locationMap = kryo.readObject(input, HashMap.class);
input.close();

log.info(locationMap.size());
{% endhighlight %}

the `log.error` never showed and the `log.info` said I had 0 entries in my map. Why? `isr` was never null so it read something, Kryo just can't seem to deserialize it and never provided any error.

Well,

Turns out the problem was with Maven. I had "filtering" enabled so Maven was trying to utf8 encode my serialized objects in the jar. Kryo was silent about it but rewriting the code to use standard Java serialization gave the error found here: [http://stackoverflow.com/a/5421992/424631]( http://stackoverflow.com/a/5421992/424631). Kryo should probably have warned rather than failed silently (and I should probably make a JIRA...).

Here is the fix:

{% highlight xml %}
<resources>
  <resource>
    <directory>src/main/resources</directory>
      <!--if true Maven will try to UTF-8 encode objects, which breaks deserialization-->
        <filtering>false</filtering>
  </resource>
</resources>
{% endhighlight %}

