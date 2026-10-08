# Synthetic narration sources

The Allagma workflow narration is generated locally using the **af_heart** voice
from **Kokoro-82M v1.0**, whose model repository declares Apache License 2.0.
The model card explicitly permits production and commercial deployment. The
runtime is **kokoro-onnx 0.6.1**, under MIT. No human narrator is implied and no
specific person's voice was cloned for this project. No Apple system voice is
used in the current movie.

- [Pinned model card and training-data attributions](https://huggingface.co/hexgrad/Kokoro-82M/blob/f3ff3571791e39611d31c381e3a41a3af07b4987/README.md)
- [Kokoro Apache 2.0 license](https://github.com/hexgrad/kokoro/blob/dfb907a02bba8152ca444717ca5d78747ccb4bec/LICENSE), also retained in [NARRATION-LICENSE.txt](NARRATION-LICENSE.txt)
- [ONNX engine MIT license](https://github.com/thewh1teagle/kokoro-onnx/blob/3596b26764286a7de9d90c363e988d50578918e5/LICENSE)
- [Model and voice download URLs, digests and generation settings](../source/narration-model.json)

The model card attributes Koniwa (CC BY 3.0) and SIWIS (CC BY 4.0) audio among
its training sources; follow its original source links for those credits.
The model, voice embeddings, ONNX runtime and phonemizer are optional local
rendering dependencies and are not bundled into the movie or Allagma's core.
Their own licenses apply to separate redistribution of those tools.

The original script is maintained in `media/source/scenes.json`. The generated
voice identity, synthesis settings, clip digests and timing adjustments are
recorded in the rendering evidence. Scientific footage and measurements are
unchanged by this replacement.
