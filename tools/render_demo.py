#!/usr/bin/env python3
"""Encode an actual capture with local synthetic narration, captions and receipts.

Requires FFmpeg/ffprobe and macOS `say`. Never accelerates or fabricates footage.
Source narration and recorded scene times remain editable and independently
inspectable. A small voice tempo adjustment can fit the real scene duration;
only narration is adjusted, not scientific execution time.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import textwrap

ROOT = Path(__file__).resolve().parents[1]


def run(command):
    subprocess.run(command, check=True, stdout=subprocess.DEVNULL)


def duration(file):
    return float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", str(file)]))


def timestamp(seconds, sep='.'):
    ms = round(seconds * 1000)
    h, ms = divmod(ms, 3600000)
    m, ms = divmod(ms, 60000)
    s, ms = divmod(ms, 1000)
    return f"{h:02}:{m:02}:{s:02}{sep}{ms:03}"


def render(capture, output):
    timeline = json.loads((capture / "timeline.json").read_text())
    script = json.loads((ROOT / "media/source/scenes.json").read_text())
    movie = output / "allagma-workflow.mp4"
    if movie.exists():
        raise SystemExit("Choose a fresh output directory; prior rendered movies are preserved")
    output.mkdir(parents=True, exist_ok=True)
    sound = capture / "narration"
    sound.mkdir(exist_ok=False)
    inputs, filters, captions, voice_records = [], [], [], []
    for scene in timeline["scenes"]:
        sentences = re.split(r'(?<=[.!?])\s+', scene["narration"])
        pieces, lengths = [], []
        for n, sentence in enumerate(sentences):
            raw = sound / f"{scene['id']}-{n:02d}.aiff"
            run(["say", "-v", script["voice"], "-r", str(script["words_per_minute"]), "-o", str(raw), sentence])
            pieces.append(raw)
            lengths.append(duration(raw))
        available = scene["end"] - scene["start"] - .65
        tempo = max(1.0, sum(lengths) / available)
        if tempo > 1.25:
            raise RuntimeError(f"Narration too long for {scene['id']}; shorten it or recapture a longer scene")
        cursor = scene["start"] + .25
        for sentence, raw, length in zip(sentences, pieces, lengths):
            i = len(inputs)
            inputs += [raw]
            filters.append(f"[{i+1}:a]atempo={tempo:.6f},adelay={round(cursor*1000)}:all=1[a{i}]")
            end = cursor + length/tempo
            captions.append((cursor, end, sentence))
            cursor = end
        voice_records.append({"scene":scene["id"],"original_seconds":sum(lengths),"narration_tempo":tempo,"video_tempo":1.0})
    raw = capture / timeline["raw"]
    command = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-i", str(raw)]
    for item in inputs:
        command += ["-i", str(item)]
    filters.append(''.join(f"[a{i}]" for i in range(len(inputs))) + f"amix=inputs={len(inputs)}:normalize=0,loudnorm=I=-18:TP=-2:LRA=11[audio]")
    command += ["-filter_complex", ';'.join(filters), "-map", "0:v:0", "-map", "[audio]",
                "-c:v", "libx264", "-preset", "medium", "-crf", "22", "-pix_fmt", "yuv420p", "-r", "30",
                "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart", "-t", str(duration(raw)),
                "-metadata", "title="+script['title'],
                "-metadata", "comment=Actual continuous software capture; no accelerated computation. Local synthetic Samantha narration. Final chapter reuses labeled EMA r07 results; see accompanying transcript, provenance, and AI Scientist study license.",
                str(movie)]
    run(command)
    vtt = "WEBVTT\n\n" + '\n\n'.join(f"{i}\n{timestamp(start)} --> {timestamp(end)}\n" + '\n'.join(textwrap.wrap(text, 64)) for i,(start,end,text) in enumerate(captions,1)) + '\n'
    (output / 'allagma-workflow.en.vtt').write_text(vtt)
    srt = '\n\n'.join(f"{i}\n{timestamp(start,',')} --> {timestamp(end,',')}\n" + '\n'.join(textwrap.wrap(text,64)) for i,(start,end,text) in enumerate(captions,1)) + '\n'
    (output / 'allagma-workflow.en.srt').write_text(srt)
    transcript = "# Allagma workflow video — transcript\n\n" + script['scope'] + "\n\nNarration is synthesized locally with the macOS Samantha system voice. The recording workbench is a shipped demo utility, not the native agent UI. Displayed command paths are abbreviated. No computation is accelerated; scene navigation is automated. The final EMA figure is machine-generated using AI Scientist-adapted code, with its separate license and source disclosure retained.\n"
    for scene in timeline['scenes']:
        transcript += f"\n## {timestamp(scene['start'])} — {scene['id'].capitalize()}\n\n{scene['narration']}\n\nOn screen: {scene['caption']}\n"
    (output/'transcript.md').write_text(transcript)
    manifest = {"format":"allagma-video-render-v1", "duration_seconds":duration(movie), "bytes":movie.stat().st_size,
                "video_sha256":hashlib.sha256(movie.read_bytes()).hexdigest(),
                "raw_video_sha256":hashlib.sha256(raw.read_bytes()).hexdigest(),
                "capture_timeline_sha256":hashlib.sha256((capture/'timeline.json').read_bytes()).hexdigest(),
                "script_sha256":hashlib.sha256((ROOT/'media/source/scenes.json').read_bytes()).hexdigest(),
                "renderer_sha256":hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                "scope":script['scope'], "voice":script['voice'], "voice_adjustments":voice_records,
                "software":"Chromium/Playwright actual browser capture, Allagma CLI, macOS say, FFmpeg H.264/AAC",
                "publication":"prepared locally, not a public upload"}
    (output/'provenance.json').write_text(json.dumps(manifest, indent=2)+'\n')
    shutil.copyfile(ROOT/'media/evidence/EMA-LICENSE.txt', output/'EMA-LICENSE.txt')
    print(json.dumps(manifest,indent=2))


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--capture',required=True,type=Path)
    parser.add_argument('--output',required=True,type=Path)
    args=parser.parse_args()
    render(args.capture,args.output)
