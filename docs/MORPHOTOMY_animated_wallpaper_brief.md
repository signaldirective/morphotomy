# MORPHOTOMY Animated Video Wallpaper System

## Goal

Build a reusable local workflow that turns my existing MORPHOTOMY
specimen wallpapers into seamless-looping MP4 video wallpapers for
Omarchy Linux.

I am using a development build of Omarchy that supports MP4 files as
wallpapers. Keep the original wallpaper artwork completely intact and
animate only a separate HUD/diagnostic overlay on top of it.

**Do not generate or alter any artwork yet.** First inspect the
available files and environment, then propose a practical implementation
plan. After confirming the source wallpapers and available tools,
implement the animation system and render a test video if the
environment supports it.

## Visual concept

The wallpapers belong to a dystopian cybernetic/biomechanical art
project called **MORPHOTOMY**. Each image presents a central cybernetic
organ or body part surrounded by generous negative space:

-   Eye specimen
-   Heart specimen
-   Hand specimen
-   Brain specimen (planned)

The wallpapers share a visual language: near-black background, a central
organic/cybernetic subject, restrained red accents, small specimen
metadata, barcode/interface details, and a clinical, ominous
science-fiction atmosphere.

I showed ChatGPT a screenshot of the eye wallpaper, but it was a desktop
screenshot with terminal/shell content overlaid. **Do not use that
screenshot as the production source if the original wallpaper file is
available.** Work directly from the actual wallpaper files. Preserve
each source image's original pixels and composition.

The animation should feel like a technical diagnostic HUD inspecting the
specimen, not like a new image being generated.

## Core animation sequence

Create a silent, looping video with this sequence:

1.  **Idle:** Display the original wallpaper without added overlays for
    a short pause.
2.  **Callout lines extend:** Thin, crisp white diagnostic lines animate
    outward from carefully selected anchor points on the organ toward
    the surrounding negative space. The lines point to relevant
    features. Small endpoint dots or markers may illuminate when a line
    reaches its destination.
3.  **Specifications type in:** Monospaced technical text appears beside
    each line with a typewriter effect. Use short, atmospheric,
    fictional technical specifications appropriate to the specimen.
    Reveal labels in a readable sequence, either one at a time or in a
    few coordinated groups.
4.  **Hold:** Leave the completed annotations visible long enough to
    read.
5.  **Text erases:** Remove the text character by character, as if
    Backspace is being held.
6.  **Callout lines retract:** Retract the lines in reverse, extinguish
    endpoint markers, and return to the untouched original wallpaper.
7.  **Loop:** Return to the initial state cleanly, with no visible jump,
    flash, leftover overlay, or frame mismatch.

Timing should feel deliberate and restrained rather than frantic. Make
timing easy to tune through configuration rather than hard-coding it
throughout the renderer.

## Technical requirements

-   **Output:** MP4 suitable for use as an Omarchy video wallpaper.
-   **Audio:** None.
-   **Looping:** Design for a seamless loop. Verify the first and final
    frames and inspect the transition for visible discontinuities.
-   **Background:** Keep the original wallpaper static and unchanged. Do
    not regenerate, repaint, warp, flicker, or otherwise modify the
    organ or existing interface elements.
-   **Overlay:** Render the animated HUD as a separate layer, then
    composite it over the original wallpaper.
-   **Resolution:** Render at the source wallpaper's native resolution
    by default. Preserve aspect ratio and avoid unintended cropping or
    stretching.
-   **Encoding:** Use a broadly compatible MP4 encoding and sensible
    bitrate/file size. The images are mostly dark with fine lines and
    small text, so avoid unnecessary bitrate while preserving clean text
    and line edges.
-   **Performance:** Prefer an efficient offline rendering process. The
    final wallpaper should not require a browser, a running animation
    script, or an additional live overlay process during playback.
-   **Tools and cost:** Prefer tools already installed locally and
    free/open-source options. Do not assume that I have or want a paid
    subscription or hosted AI video-generation service. Check the actual
    environment before choosing dependencies.
-   **Reusability:** Build one animation engine that can be reused
    across the eye, heart, hand, and brain wallpapers. Specimen-specific
    content and coordinates should live in configuration files or
    similarly easy-to-edit data.
-   **Maintainability:** Keep the project organized, document how to run
    it, and provide simple instructions for rendering one or all
    specimens.

## Suggested implementation

Choose the most reliable approach based on the actual environment. A
local scripted renderer is preferred over generative video because the
artwork must remain perfectly stable and the animation must be
deterministic.

Potential approach: - Use SVG or another vector layer for sharp lines,
endpoint markers, and monospaced text. - Animate line growth/retraction
and character-by-character text reveal/erasure programmatically. -
Composite the overlay over the original still image. - Render frames and
encode them to MP4 using tools available locally, such as FFmpeg and/or
Python libraries if installed or reasonably installable. - Keep specimen
definitions separate from rendering code.

These are suggestions, not mandatory technology choices. Inspect the
available tools first and choose the simplest robust solution. Do not
install packages or make system-wide changes without checking first and
explaining what is needed.

## Design direction

Aim for a minimal, precise, clinical, unsettling diagnostic interface:

-   Thin white or slightly cool-white callout lines.
-   Small endpoint markers, ticks, or restrained targeting details where
    useful.
-   Monospaced technical text, all-caps labels, compact values, and
    subtle hierarchy.
-   Preserve the wallpaper's existing palette and visual balance. Use
    red only where it complements existing red interface accents.
-   Keep callouts sparse enough that the organ remains the focus. Around
    two or three active callouts at a time is a reasonable starting
    point.
-   Position labels in the surrounding empty space so they do not
    collide with the specimen, existing UI text, barcodes, or other
    fixed elements.
-   Avoid excessive glow, oversized HUD graphics, random glitching,
    camera motion, zooms, or any animation that changes the source
    artwork.
-   Use subtle staggered timing so the interface feels like a real
    diagnostic scan.

## Example fictional callout content

These are tone examples, not mandatory final text. Keep each label short
enough to read comfortably.

### Eye

-   `RETINAL INTEGRITY: 61%`
-   `OPTIC INTERFACE: SYNTHETIC`
-   `PUPILLARY RESPONSE: OVERRIDDEN`
-   `SENSORY INPUT: ACTIVE`

### Heart

-   `CARDIAC SYNC: 62 BPM`
-   `MYOCARDIAL GRAFT: STABLE`
-   `PERFUSION: NOMINAL`
-   `AUTONOMIC CONTROL: PARTIAL`

### Hand

-   `MOTOR RESPONSE: 94%`
-   `TACTILE ARRAY: ONLINE`
-   `TENDON ACTUATORS: SYNCHRONIZED`
-   `GRIP LIMITER: DISABLED`

### Brain

-   `NEURAL SYNC: 87%`
-   `MEMORY INTEGRITY: FRAGMENTED`
-   `COGNITIVE PARTITION: ACTIVE`
-   `EXECUTIVE CONTROL: DISPUTED`

Keep the fictional data consistent with the MORPHOTOMY setting. The
existing wallpaper may already contain specimen metadata; avoid
redundantly repeating it in the animated annotations unless it serves a
clear visual purpose.

## Configuration and reuse

Create a simple configuration for each specimen containing, as
appropriate:

-   Source image path
-   Output MP4 path
-   Video dimensions and frame rate
-   Total loop duration and phase timings
-   Callout anchor coordinates on the organ
-   Line destination/label coordinates
-   Text strings
-   Typing speed and erasing speed
-   Hold durations
-   Optional stagger/delay between callouts

Use normalized coordinates (0--1 relative to image width/height) where
practical so the layout is easier to adapt if source resolution changes.
If the artwork has different dimensions or compositions, allow
specimen-specific coordinates rather than assuming every point is
identical.

The wallpapers share a layout and similar negative space, so the engine
should be shared. Do not force identical callout placements if a
particular organ's anatomy or existing UI makes a different layout look
better.

## Validation and quality checks

Before considering the work complete:

1.  Inspect the actual source wallpaper files and their dimensions.
2.  Confirm which rendering and encoding tools are already available.
3.  Create one prototype first, preferably for the eye specimen if its
    original file is present.
4.  Render a low-cost preview or representative frames before producing
    a final-quality video.
5.  Check that all labels are legible at the actual desktop resolution
    and that lines point to the intended features.
6.  Check for overlap with existing wallpaper text and interface
    elements.
7.  Verify that the background remains unchanged wherever no overlay is
    present.
8.  Verify that the final frame transitions cleanly back to the first
    frame.
9.  Confirm the MP4 is silent, plays correctly, has the expected
    dimensions/frame rate, and is reasonably sized.
10. Keep the source images untouched and save outputs to a separate
    output directory.

## Workflow instructions

-   Start by inspecting the project directory and locating the original
    wallpaper files. Do not assume filenames or paths; discover them.
-   Check which tools are already installed before selecting the
    implementation.
-   Explain the proposed approach briefly, then proceed with the most
    practical local implementation.
-   Do not ask me to repeat the concept or design requirements in this
    document.
-   If something essential is missing, ask one focused question rather
    than making up a path or assuming a dependency.
-   Do not overwrite the original wallpaper files.
-   Build the eye prototype first if the original file is available,
    then make the system reusable for the other specimens.
-   Provide the exact commands to preview, render, and regenerate
    videos, along with where the outputs were saved.
-   Optimize for a reliable result and an easy workflow, not unnecessary
    architectural complexity.

## Definition of done

The first milestone is one polished, silent, looping MP4 made from the
original eye wallpaper, with animated callout lines and typewriter-style
technical labels that erase and retract before the loop restarts.

After that prototype is approved, adapt the same engine to the heart and
hand wallpapers, then the brain wallpaper when it is available.
