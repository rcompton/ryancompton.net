---
layout: post
title: "Ghoul Fluids: An Interactive Halloween Fluid Simulation"
description: "Building a GPU-accelerated fluid simulation that reacts to people using computer vision."
category:
tags: ["python", "moderngl", "halloween", "computer vision"]
---

For Halloween this year, I wanted to build something interactive for my display. I've always been fascinated by fluid simulations, so I decided to create a virtual fluid that visitors could interact with just by moving in front of a camera. The result is "Ghoul Fluids"—a real-time, GPU-accelerated fluid simulation that glows with spooky colors and reacts to your presence.

![Ghoul Fluids Screenshot](/assets/pix/ghoul_fluids_demo.jpg)

<!--more-->

## The Concept

The idea was simple: set up a screen and a camera. When someone walks by, their silhouette appears in the fluid. As they move, they push the fluid around, creating swirls and mixing colors. When no one is around, the fluid shouldn't just sit still—it needs to look "alive" and spooky.

## Tech Stack

To pull this off in real-time (aiming for 60 FPS), I needed to run the heavy number crunching on the GPU.

*   **Language**: Python
*   **Graphics/Compute**: [ModernGL](https://github.com/moderngl/moderngl) (OpenGL wrapper for Python)
*   **Computer Vision**: [MediaPipe](https://developers.google.com/mediapipe) or [YOLO](https://github.com/ultralytics/ultralytics) for segmentation
*   **Hardware**: A webcam and a decent GPU.

## How It Works

### 1. Fluid Simulation
The core is a grid-based fluid solver running on the GPU. It solves the Navier-Stokes equations (specifically the incompressible flow part) using a series of shaders.
*   **Advection**: Moves velocity and dye fields along the velocity vector.
*   **Divergence & Pressure**: Calculates where fluid is piling up and solves a pressure Poisson equation (using Jacobi iteration) to make the flow incompressible.
*   **Gradient Subtract**: Removes the pressure gradient from the velocity field to enforce incompressibility.

All of this happens in a "ping-pong" fashion between framebuffers, allowing the simulation to evolve over time.

### 2. Seeing Ghosts (Segmentation)
To make it interactive, I needed to isolate the person from the background. I supported both MediaPipe and YOLO for this. The segmentation model gives us a binary mask of the person.

This mask is uploaded to the GPU every frame. We compute the "optical flow" (motion) of the person and inject that as velocity into the fluid simulation. We also emit "dye" from the person's silhouette, so they leave a trail of color as they move.

### 3. Ambient Mode
One of the fun challenges was defining what happens when *no one* is interacting with it. I didn't want a static black screen.

I wrote an `AmbientController` to handle this. It manages a set of invisible "emitters" that drift around the screen.

```python
# Drifting emitters inject velocity and dye
for e in self.emitters:
    # random walk / bounce off walls logic...

    # inject halloweeny colors (orange/purple)
    sim.inject_dye(e['pos'], e['col'])
    sim.inject_vel(e['pos'], e['vel'])
```

These emitters use a spooky color palette—blending between bright orange and deep purple. To make the motion more chaotic and interesting, the system also periodically spawns "vortex dipoles"—pairs of spinning forces that travel through the fluid, creating nice curling patterns.

### 4. Palette Cycling
To keep the display from getting boring, the visualization cycles through different color palettes over time. A shader maps the density of the fluid dye to colors from a texture, and I blend between these textures to smoothly transition between different "moods."

## The Result

The combination of high-performance GPU compute and modern computer vision models made for a really responsive installation. It was great to see kids (and adults) waving their arms to create giant vortices of neon slime.

![Kids playing with Ghoul Fluids](/assets/pix/ghoul_fluids_kids.jpg)

If you're interested in the code, I used `moderngl` for all the heavy lifting. It's a fantastic library that makes writing OpenGL in Python much more approachable.

Happy Halloween!
