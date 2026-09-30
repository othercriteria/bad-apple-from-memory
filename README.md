# Bad Apple — from memory

A complete 3:39 reconstruction of the black-and-white silhouette music video, made without searching for or inspecting reference footage, images, recordings, scores, lyrics, or existing recreations. All character geometry, choreography, editing, melody, and accompaniment are authored in `src/render.py`.

This is an interpretation of remembered imagery and music, not a frame-accurate recreation. The instrumental melody is approximate; there are no sampled recordings or synthesized vocals. The sequence features an apple, shrine maiden, witch and broom, books, maid and clock, knives, bat and crystal wings, swords, ghosts, blossoms, rabbits and bamboo, fire, dolls, sunflowers, umbrella, eyes, crows, and a final return to the apple.

## Play

Download `bad-apple-from-memory.mp4` from the private repository's **Releases**, or open `output/bad-apple-from-memory.mp4` after rendering. The file is 960 × 720 at 30 fps, H.264 with `yuv420p` pixels and stereo AAC audio, with the MP4 index at the front for streaming. `output/storyboard.jpg` provides a contact sheet of all 31 shots.

## Reproduce on NixOS

```sh
direnv allow
python src/render.py
```

Or, without activating direnv:

```sh
nix develop --command python src/render.py
```

`flake.lock` pins the tooling. The renderer does not access the network or read media assets. Nix downloads build dependencies on the first run. A fixed random seed makes the audio repeatable.

For a quick playback check or a larger render:

```sh
python src/render.py --duration 12 --width 640 --output output/preview.mp4
python src/render.py --width 1440 --output output/bad-apple-1440.mp4
python src/render.py --sheet-only
```

Check the complete file's codecs, audio/video duration, streaming layout, and every decoded frame and audio packet:

```sh
nix develop --command python src/verify.py
```

The renderer also saves an uncompressed stereo WAV and a JSON render report beside the MP4. Generated files are excluded from Git and distributed as release attachments. Music is synthesized at 138 BPM and the 31 shots span 504 beats. Frames are drawn with supersampling; silhouette contours, hair, limbs, props, particles, wipes, and camera composition are procedural.

## Attribution

A fan reconstruction of **Bad Apple!!**, the Touhou song and its well-known silhouette animation. The underlying composition, characters, and original video belong to their respective creators. No original media is included. This project records a memory exercise, including its inaccuracies.
