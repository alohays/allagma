#!/usr/bin/env python3
"""Portable offline TeX builder shipped in the source archive's anc directory.

Requires an existing TeX installation and macOS sandbox-exec or Linux bubblewrap.
It installs nothing and refuses to claim isolation when the sandbox is absent.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def run(command, *, cwd, env, timeout):
    result = subprocess.run(command, cwd=cwd, env=env, stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT, timeout=timeout, text=True)
    if result.returncode:
        raise RuntimeError(f"Build command exited {result.returncode}: {Path(command[-1]).name}\n{result.stdout[-6000:]}")
    return result.stdout


def compile_sources(source, output, *, engine="pdflatex", timeout=60):
    source, output = Path(source).resolve(), Path(output).resolve()
    if engine not in ("pdflatex", "xelatex") or not 1 <= timeout <= 600:
        raise ValueError("Choose pdflatex/xelatex and a finite 1-600 second command limit")
    compiler, bibtex, kpsewhich = (shutil.which(name) for name in (engine, "bibtex", "kpsewhich"))
    if not all((compiler, bibtex, kpsewhich)):
        raise RuntimeError("Install a TeX distribution separately; the offline core never installs TeX")
    manifest = json.loads((source / "anc/provenance.json").read_text())
    files = manifest["source_files"]
    for name, expected in files.items():
        path = source / name
        if Path(name).is_absolute() or ".." in Path(name).parts or path.is_symlink() or sha(path) != expected:
            raise ValueError(f"Source archive integrity mismatch: {name}")
    if output.exists():
        raise ValueError("Use a new build output directory")
    output.mkdir(parents=True)
    # /tmp avoids ambient workspace and host caches. Only reviewed source files
    # enter this tree, followed by an OS-enforced network/read boundary.
    with tempfile.TemporaryDirectory(prefix="allagma-tex-", dir="/tmp") as temporary:
        work = Path(temporary).resolve()
        for name in files:
            target = work / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source / name, target)
        (work / "home").mkdir()
        tex_root = Path(subprocess.check_output([kpsewhich, "--var-value=TEXMFROOT"], text=True).strip()).resolve()
        tex_roots = {tex_root}
        for variable in ("TEXMFSYSVAR", "TEXMFSYSCONFIG", "TEXMFDIST"):
            raw_path = subprocess.check_output([kpsewhich, "--var-value=" + variable], text=True).strip()
            if raw_path and Path(raw_path).is_dir():
                tex_roots.add(Path(raw_path).resolve())
        env = {"PATH": str(Path(compiler).parent) + os.pathsep + "/usr/bin:/bin",
               "HOME": str(work / "home"), "TMPDIR": str(work), "LANG": "C.UTF-8",
               "TEXMFHOME": str(work / "empty-texmf"), "TEXMFVAR": str(work / "texmf-var"),
               "TEXMFCONFIG": str(work / "texmf-config"), "TEXINPUTS": ".:", "BIBINPUTS": ".:", "BSTINPUTS": ".:",
               "openin_any": "p", "openout_any": "p", "SOURCE_DATE_EPOCH": "1791504000", "FORCE_SOURCE_DATE": "1"}
        if sys.platform == "darwin" and Path("/usr/bin/sandbox-exec").is_file():
            allowed = [work, *sorted(tex_roots), Path("/System"), Path("/usr/lib"), Path("/usr/share"),
                       Path("/Library/Apple"), Path("/dev")]
            quote = lambda p: json.dumps(str(p))
            policy = "\n".join(["(version 1)", "(allow default)", "(deny network*)", "(deny file-read-data)",
                "(deny file-write*)", *[f"(allow file-read-data (subpath {quote(p)}))" for p in allowed],
                # macOS 26 dyld opens the root directory during startup. This
                # grants that directory only, not arbitrary descendant files.
                '(allow file-read-data (literal "/"))',
                f"(allow file-write* (subpath {quote(work)}) (literal \"/dev/null\"))"])
            prefix = ["/usr/bin/sandbox-exec", "-p", policy]
            isolation = "macOS Seatbelt: deny network; read only clean source, TeX and system runtime; write only clean build"
        elif sys.platform.startswith("linux") and shutil.which("bwrap"):
            prefix = [shutil.which("bwrap"), "--die-with-parent", "--unshare-net", "--new-session"]
            for directory in ("/usr", "/bin", "/lib", "/lib64", "/etc"):
                if Path(directory).exists():
                    prefix += ["--ro-bind", directory, directory]
            for runtime_root in sorted(tex_roots):
                if not runtime_root.is_relative_to(Path("/usr")) and not runtime_root.is_relative_to(Path("/etc")):
                    prefix += ["--ro-bind", str(runtime_root), str(runtime_root)]
            prefix += ["--proc", "/proc", "--dev", "/dev", "--bind", str(work), str(work), "--chdir", str(work)]
            isolation = "Linux bubblewrap: private network; clean build plus read-only TeX/system runtime; no reference cache mount"
        else:
            raise RuntimeError("Clean compilation requires macOS sandbox-exec or Linux bubblewrap; no unsandboxed fallback")
        invocations, combined = [], []

        def command(argv):
            invocations.append([Path(argv[0]).name, *argv[1:]])
            try:
                text = run([*prefix, *argv], cwd=work, env=env, timeout=timeout)
            except (RuntimeError, OSError, subprocess.SubprocessError) as exc:
                for name in ("main.log", "main.fls", "main.pdf"):
                    if (work / name).is_file():
                        shutil.copyfile(work / name, output / name)
                (output / "failure.json").write_text(json.dumps({"status": "failed", "commands": invocations,
                    "reason": str(exc).replace(str(work), "<clean-build>")}, indent=2) + "\n")
                raise
            combined.append(text)

        tex = [compiler, "-no-shell-escape", "-interaction=nonstopmode", "-halt-on-error", "-file-line-error", "-recorder", "main.tex"]
        command(tex)
        if r"\citation{" in (work / "main.aux").read_text():
            command([bibtex, "main"])
        for iteration in range(5):
            command(tex)
            log = (work / "main.log").read_text(errors="replace")
            if iteration >= 1 and not re.search(r"Rerun to get|Rerun to get cross-references|Label\(s\) may have changed", log, re.I):
                break
        for name in ("main.pdf", "main.bbl", "main.log", "main.fls"):
            if (work / name).exists():
                shutil.copyfile(work / name, output / name)
        (output / "commands.log").write_text("\n".join(combined).replace(str(work), "<clean-build>"))
        defects = [line for line in log.splitlines() if re.search(
            r"Overfull \\[hv]box|Missing character:|undefined|Rerun to get|There were multiply-defined|Citation .*not found", line, re.I)]
        if defects:
            (output / "failure.json").write_text(json.dumps({"status": "failed", "layout_reference_errors": defects}, indent=2) + "\n")
            raise RuntimeError("Unresolved TeX layout/reference defects:\n" + "\n".join(defects))
        pdf = work / "main.pdf"
        if not pdf.is_file() or not pdf.read_bytes().startswith(b"%PDF-"):
            raise RuntimeError("Compiler did not produce a PDF")
        for name in ("main.pdf", "main.bbl", "main.log", "main.fls"):
            if (work / name).exists():
                shutil.copyfile(work / name, output / name)
        version = subprocess.check_output([compiler, "--version"], text=True).splitlines()[0]
        inputs = sorted(set(line[6:] for line in (work / "main.fls").read_text().splitlines() if line.startswith("INPUT ")))
        normalized = [name.replace(str(work), "<clean-build>") for name in inputs]
        receipt = {"format": "allagma-clean-tex-build-v1", "status": "pass", "engine": engine,
                   "compiler_version": version, "network": "denied", "reference_cache": "not accessible",
                   "isolation": isolation, "commands": invocations, "source_files": files,
                   "pdf_sha256": sha(output / "main.pdf"), "pdf_bytes": (output / "main.pdf").stat().st_size,
                   "layout_reference_errors": defects, "compiler_inputs": normalized,
                   "scope": "Clean local compilation and log checks; PDF visual inspection and arXiv server processing are separate"}
        (output / "build.json").write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
        (output / "commands.log").write_text("\n".join(combined).replace(str(work), "<clean-build>"))
        return receipt


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--engine", choices=["pdflatex", "xelatex"], default="pdflatex")
    parser.add_argument("--timeout", type=int, default=60)
    args = parser.parse_args()
    try:
        result = compile_sources(args.source, args.output, engine=args.engine, timeout=args.timeout)
    except (ValueError, RuntimeError, OSError, subprocess.SubprocessError) as exc:
        parser.exit(1, str(exc) + "\n")
    print(json.dumps({k: v for k, v in result.items() if k not in ("source_files", "compiler_inputs")}, indent=2))
