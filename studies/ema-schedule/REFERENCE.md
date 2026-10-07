# Reference and disclosure

`development/science.py` is an exact copy of the completed v0.2 EMA study's
`domain/science.py` at Allagma commit `6d2daf0`. That study adapted the residual
denoiser and DDPM equations from SakanaAI/AI-Scientist `templates/2d_diffusion`
at commit `1de1dbc1f4ee2c5f61e9c94348d55eb51d7fa2eb`. Attribution, the original
reference files and the rationale for a cosine DDPM noise schedule are retained
in the [prior study](../ema-2d-diffusion/REFERENCE.md).

The applicable AI Scientist Source Code License is retained verbatim at
`reference/LICENSE`. This license applies to the adapted scientific code; it
does not replace the Allagma framework's MIT license.

**AI disclosure:** This study's code, documentation and any resulting manuscript
are generated or revised by an AI agent. Scientific assertions require retained
execution and verification evidence. Development pilots are not final research
findings, and same-model critique is not independent peer review.

The follow-up changes the learning-rate-policy and terminal-duration design.
It makes no claim to reproduce the upstream AI-Scientist paper's results.
