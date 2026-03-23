# KataGo Environment Setup

## Current decision

This project uses:

- Engine: official KataGo `v1.16.4`
- Active backend: `OpenCL`
- Active GPU: `NVIDIA GeForce RTX 5060 Laptop GPU`
- Model: `kata1-b18c384nbt-s9372115968-d4150170048.bin.gz`

## Why OpenCL instead of CUDA

The CUDA build was downloaded, but only the OpenCL build was locally verified to start correctly in this environment.
For a teaching product, stable startup is more important than chasing a small theoretical speed gain.

## Why not use the NPU

This machine has an `AMD Ryzen AI 9 HX 370` and Windows enumerates an `NPU Compute Accelerator Device`.
However, KataGo's supported runtime backends are centered around `CUDA`, `OpenCL`, `TensorRT`, and `Eigen`.
There is no straightforward production-ready NPU backend path for KataGo here, so the NPU should not be used for board analysis in the first version.

## Installed files

- Engine, OpenCL: `tools/katago/opencl/`
- Engine, CUDA: `tools/katago/engine/`
- Model: `models/katago/`
- Project config: `config/`
- Launch scripts: `scripts/`

## Recommended usage

- Backend service process: run `scripts/start-katago-analysis.ps1`
- Direct play or GUI attach: run `scripts/start-katago-gtp.ps1`
- Env template for application wiring: `config/katago.env.example`

## Notes for this machine

- `nvidia-smi` showed about `8GB` usable VRAM, not 12GB.
- LM Studio was already holding part of VRAM during setup.
- Because of that, this project uses a `b18` model and moderate visit/thread settings.

## Future tuning path

If your later backend can queue analysis requests and you close LM Studio while using the Go app, you can try:

- `maxVisits` from `400` to `800`
- `numSearchThreads` from `6` to `8`
- `nnCacheSizePowerOfTwo` from `21` to `22`

Tune one parameter at a time rather than all at once.
