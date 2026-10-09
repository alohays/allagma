# Reference index

How does the relative benefit of weight EMA vary with terminal training duration and the complete learning-rate policy in a tiny 2D DDPM?

Coverage mode: **online**. Metadata accuracy and scientific support are reviewed separately.

## Coverage

- baseline: limited. Raw, fixed-decay EMA, SWA and alternative averaging are identified. Only the original raw/EMA comparisons were executed.
- competing: covered. Ajroldi 2025 limits replacement-of-annealing claims; Li 2024 contains ordinary-EMA degradations and a distinct switching intervention. Different protocols are kept explicit.
- gaps: limited. The retained study leaves averaging windows, more seeds, architectures and alternative averaging untested. The search does not establish that these are novel open problems.
- implementation: covered. Three exact AI-Scientist repository files at commit 1de1dbc are retained with hashes, plus the completed study's immutable lineage.
- primary: covered. Seven located full papers cover DDPM, weight averaging, optimizer schedules and contrary outcomes.

- Limit: Targeted narrative literature map, not a systematic review or exhaustive search through October 2026. Search engine indexing and selected English-language sources limit coverage.
- Limit: This map was built for a new manuscript revision after the frozen r07 experiment. It does not retroactively establish preregistered literature choices or change historical science.
- Limit: The cited studies differ in architectures, datasets, optimizers, averaging rules and metrics. No cross-paper meta-analysis or new reproduction of their reported results was performed.
- Limit: Selected raw PDFs, source archives, repository files, one real model artifact and one evaluation split are local-only. The map does not claim that every upstream model or dataset was acquired.

## Read on demand

- [Ho2020](notes/Ho2020.md): Denoising Diffusion Probabilistic Models (2020); primary, baseline. Metadata: verified. Defines the DDPM family and supplies context for evaluating averaged diffusion weights.
- [Nichol2021](notes/Nichol2021.md): Improved Denoising Diffusion Probabilistic Models (2021); primary, implementation. Metadata: verified. Explains the fixed cosine diffusion-noise schedule, which must not be confused with the optimizer schedule under study.
- [Izmailov2018](notes/Izmailov2018.md): Averaging Weights Leads to Wider Optima and Better Generalization (2018); primary, baseline. Metadata: verified. Provides a competing averaging baseline and shows why the averaging rule and learning-rate path need separate names.
- [MoralesBrotons2024](notes/MoralesBrotons2024.md): Exponential Moving Average of Weights in Deep Learning: Dynamics and Benefits (2024); primary, competing, baseline. Metadata: verified. Directly connects the benefit of EMA with the learning-rate schedule and offers a comparison to the retained endpoint findings.
- [Karras2024](notes/Karras2024.md): Analyzing and Improving the Training Dynamics of Diffusion Models (2024); primary, competing, gaps. Metadata: verified. Shows that averaging length interacts with architecture and training duration in diffusion models.
- [Ajroldi2025](notes/Ajroldi2025.md): When, Where and Why to Average Weights? (2025); primary, competing, baseline. Metadata: verified. A newer, closely related benchmark explicitly compares averaging with learning-rate annealing and limits the novelty of the retained study.
- [Li2024](notes/Li2024.md): Switch EMA: A Free Lunch for Better Flatness and Sharpness (2024); primary, competing. Metadata: verified. Adds explicit counterexamples to universal EMA-benefit language and describes a different intervention that changes training weights.
- [Sakana2025](notes/Sakana2025.md): AI-Scientist 2D diffusion template: selected source snapshot (2025); implementation, baseline. Metadata: verified. Exact upstream code lineage of the retained denoiser and diffusion equations.

Read `map.json` for located passages, disagreements, limitations and phase decisions. Read individual notes and retained source assets when needed. `citations.bib` includes only metadata marked verified; that status does not verify a claim.
