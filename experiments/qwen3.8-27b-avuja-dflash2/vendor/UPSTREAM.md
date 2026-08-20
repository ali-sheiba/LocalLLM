# Vendored DFlash2 sources

The runtime overlay is pinned to Club-3090 PR #1072 head commit
`b664aacf301c4195693e0be509cdb581bd099d96` (2026-08-20):

- Source: https://github.com/noonghunna/club-3090/pull/1072
- DFlash2 backport: `models/qwen3.8-27b/vllm/patches/vllm-dflash2-backport/`
- Prefix/Mamba fix: `models/qwen3.6-27b/vllm/patches/vllm-pr48375-mamba-drop-eagle-block/`
- Club-3090 license: Apache-2.0

The DFlash2 implementation originates from open vLLM PR #52816 and carries
Apache-2.0 SPDX headers. The local compile-cache namespace patch backports
upstream PR #52816 commit `64c5b80cbf66b405cd000223fc4705fcf3bb2b50`,
which is newer than the pinned Club-3090 overlay.

Do not silently repin these files. Re-evaluate overlay anchors, concurrency,
acceptance, follow-up prefix reuse, and tool quality whenever the source commit
or vLLM image changes.
