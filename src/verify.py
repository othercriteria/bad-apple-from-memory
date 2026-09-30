#!/usr/bin/env python3
"""Check the final film's streams, duration, fast-start layout and full decode."""
import argparse
import json
import struct
import subprocess
from pathlib import Path


def verify(path):
    result = subprocess.run([
        'ffprobe', '-v', 'error', '-show_streams', '-show_format',
        '-of', 'json', str(path),
    ], check=True, capture_output=True, text=True)
    metadata = json.loads(result.stdout)
    video = next(s for s in metadata['streams'] if s['codec_type'] == 'video')
    audio = next(s for s in metadata['streams'] if s['codec_type'] == 'audio')
    assert video['codec_name'] == 'h264', 'Expected H.264 video'
    assert video['pix_fmt'] == 'yuv420p', 'Expected widely compatible pixel format'
    assert video['width'] * 3 == video['height'] * 4, 'Expected 4:3 aspect ratio'
    assert audio['codec_name'] == 'aac' and audio['channels'] == 2
    assert abs(float(video['duration']) - float(audio['duration'])) < .06, 'A/V duration mismatch'
    assert abs(float(metadata['format']['duration']) - 504 * 60 / 138) < .06, 'Incomplete film'
    atoms = []
    with path.open('rb') as f:
        while header := f.read(8):
            size, kind = struct.unpack('>I4s', header)
            header_size = 8
            if size == 1:
                size = struct.unpack('>Q', f.read(8))[0]
                header_size = 16
            atoms.append(kind.decode('ascii'))
            if size == 0:
                break
            assert size >= header_size, 'Invalid MP4 atom'
            f.seek(size - header_size, 1)
    assert atoms.index('moov') < atoms.index('mdat'), 'MP4 lacks fast-start layout'
    decode = subprocess.run([
        'ffmpeg', '-v', 'error', '-xerror', '-i', str(path),
        '-map', '0:v:0', '-map', '0:a:0', '-f', 'null', '-',
    ], check=True, capture_output=True, text=True)
    assert not decode.stderr.strip(), decode.stderr
    return {
        'file': path.name,
        'full_decode': 'passed',
        'fast_start': True,
        'video': {k: video[k] for k in ['codec_name', 'width', 'height', 'pix_fmt', 'r_frame_rate', 'nb_frames', 'duration']},
        'audio': {k: audio[k] for k in ['codec_name', 'sample_rate', 'channels', 'duration']},
        'bytes': path.stat().st_size,
    }


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('video', type=Path, nargs='?', default=Path('output/bad-apple-from-memory.mp4'))
    args = parser.parse_args()
    report = verify(args.video)
    target = args.video.with_suffix('.verification.json')
    target.write_text(json.dumps(report, indent=2) + '\n')
    print(target.read_text(), end='')
