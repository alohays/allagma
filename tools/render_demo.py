#!/usr/bin/env python3
"""Encode an actual capture with reviewed local narration, captions and receipts.

Requires FFmpeg/ffprobe and clips from narrate_demo.py. Never fabricates footage.
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


def render(capture, output, narration_directory):
    timeline = json.loads((capture / "timeline.json").read_text())
    script = json.loads((ROOT / "media/source/scenes.json").read_text())
    movie = output / "allagma-workflow.mp4"
    if movie.exists():
        raise SystemExit("Choose a fresh output directory; prior rendered movies are preserved")
    output.mkdir(parents=True, exist_ok=True)
    speech = json.loads((narration_directory / "narration.json").read_text())
    if speech['script_sha256'] != hashlib.sha256((ROOT / "media/source/scenes.json").read_bytes()).hexdigest():
        raise ValueError("Narration does not match the current script")
    # Footage and observed times remain frozen. Narration is editable in
    # postproduction; keep its current source distinct from the capture plan.
    narration = {scene['id']:scene for scene in script['scenes']}
    scenes = [{**scene, 'narration':narration[scene['id']]['narration'],
               'caption':narration[scene['id']]['caption']} for scene in timeline['scenes']]
    inputs, filters, captions, voice_records = [], [], [], []
    for scene in scenes:
        sentences = re.split(r'(?<=[.!?])\s+', scene["narration"])
        clips = [clip for clip in speech['clips'] if clip['scene'] == scene['id']]
        if [clip['text'] for clip in clips] != sentences:
            raise ValueError("Narration clips differ from the scene text")
        pieces, lengths = [], []
        for clip in clips:
            raw = narration_directory / clip['path']
            if hashlib.sha256(raw.read_bytes()).hexdigest() != clip['sha256']:
                raise ValueError("Narration clip digest changed")
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
                "-metadata", "comment=Actual continuous software capture; no accelerated computation. Synthetic Kokoro af_heart narration, generated locally with Apache-2.0 model weights. Final chapter reuses labeled EMA r07 results; see transcript, provenance, narration notices and AI Scientist study license.",
                str(movie)]
    run(command)
    vtt = "WEBVTT\n\n" + '\n\n'.join(f"{i}\n{timestamp(start)} --> {timestamp(end)}\n" + '\n'.join(textwrap.wrap(text, 64)) for i,(start,end,text) in enumerate(captions,1)) + '\n'
    (output / 'allagma-workflow.en.vtt').write_text(vtt)
    srt = '\n\n'.join(f"{i}\n{timestamp(start,',')} --> {timestamp(end,',')}\n" + '\n'.join(textwrap.wrap(text,64)) for i,(start,end,text) in enumerate(captions,1)) + '\n'
    (output / 'allagma-workflow.en.srt').write_text(srt)
    transcript = "# Allagma workflow video — transcript\n\n" + script['scope'] + "\n\nNarration uses Kokoro's af_heart voice, synthesized locally with Apache-2.0 model weights and the MIT-licensed kokoro-onnx engine. See [narration notices](NARRATION-NOTICES.md). The recording workbench is a shipped demo utility, not the native agent UI. Displayed command paths are abbreviated. No computation is accelerated; scene navigation is automated. The final EMA figure is machine-generated using AI Scientist-adapted code, with its separate license and source disclosure retained.\n"
    for scene in scenes:
        transcript += f"\n## {timestamp(scene['start'])} — {scene['id'].capitalize()}\n\n{scene['narration']}\n\nOn screen: {scene['caption']}\n"
    (output/'transcript.md').write_text(transcript)
    manifest = {"format":"allagma-video-render-v1", "duration_seconds":duration(movie), "bytes":movie.stat().st_size,
                "video_sha256":hashlib.sha256(movie.read_bytes()).hexdigest(),
                "raw_video_sha256":hashlib.sha256(raw.read_bytes()).hexdigest(),
                "capture_timeline_sha256":hashlib.sha256((capture/'timeline.json').read_bytes()).hexdigest(),
                "script_sha256":hashlib.sha256((ROOT/'media/source/scenes.json').read_bytes()).hexdigest(),
                "renderer_sha256":hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                "scope":script['scope'], "voice":script['voice'], "voice_adjustments":voice_records,
                "narration_source":speech['source'],
                "narration_receipt_sha256":hashlib.sha256((narration_directory/'narration.json').read_bytes()).hexdigest(),
                "software":"Chromium/Playwright actual browser capture, Allagma CLI, Kokoro/ONNX CPU synthesis, FFmpeg H.264/AAC",
                "narration_editing":"Current narration script applied to the original continuous footage and recorded scene times; footage is not accelerated or replaced.",
                "publication":"prepared locally, not a public upload"}
    raw_state=(capture/'state.json').read_bytes()
    public_state=json.loads(raw_state)
    public_state.pop('capture_root',None)
    (output/'capture-state.json').write_text(json.dumps(public_state,indent=2)+'\n')
    public_timeline={**timeline,'scenes':[{k:v for k,v in scene.items() if k not in ('narration','caption')} for scene in timeline['scenes']]}
    public_timeline['scope_note']='Observed capture times and source digests. The original capture plan is retained locally; final narration is in the transcript and current narration script.'
    (output/'capture-timeline.json').write_text(json.dumps(public_timeline,indent=2)+'\n')
    manifest['public_preview']={
      'capture-state.json':{'source_sha256':hashlib.sha256(raw_state).hexdigest(),'sha256':hashlib.sha256((output/'capture-state.json').read_bytes()).hexdigest(),'transformation':'Omit local execution-directory field; retain all scientific values and operation outcomes.'},
      'capture-timeline.json':{'source_sha256':manifest['capture_timeline_sha256'],'sha256':hashlib.sha256((output/'capture-timeline.json').read_bytes()).hexdigest(),'transformation':'Retain observed timings/source hashes; omit draft narration and caption text superseded during postproduction.'}}
    (output/'provenance.json').write_text(json.dumps(manifest, indent=2)+'\n')
    shutil.copyfile(ROOT/'media/evidence/EMA-LICENSE.txt', output/'EMA-LICENSE.txt')
    for name in ('NARRATION-NOTICES.md', 'NARRATION-LICENSE.txt'):
        shutil.copyfile(ROOT/'media/demo'/name, output/name)
    print(json.dumps(manifest,indent=2))


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--capture',required=True,type=Path)
    parser.add_argument('--output',required=True,type=Path)
    parser.add_argument('--narration',required=True,type=Path)
    args=parser.parse_args()
    render(args.capture,args.output,args.narration)
