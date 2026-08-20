# Prefix-cache root cause

## Symptom

With DFlash2 P11, repeated identical prompts did not reuse any prefix:

| Arm/request | End-to-end latency | Prefix metrics after two requests |
|---|---:|---:|
| DFlash2 first | 4.87 s | 0 hits |
| DFlash2 repeat | 4.82 s | 0 hits |
| No-draft first | 5.44 s | — |
| No-draft repeat | **1.37 s** | **4,704 hits / 10,102 queries** |

After the two full P11 benchmark runs, DFlash2 still reported roughly **1.90 million
prefix-cache queries and zero hits**.

The matched control retained the Avuja target, vLLM 0.27.1, Froggeric template, FP8 KV,
131K max length, `mamba-cache-mode=align`, synchronous scheduling, 0.80 memory
utilization, and prefix caching. It changed only `DRAFT_SPEC_N=7` to `0`.

**Measured conclusion:** target prompt hashing and ordinary hybrid prefix caching worked;
the zero-hit behavior appeared only when DFlash/speculative decoding was active.

## Why EAGLE-style speculation needs special cache handling

vLLM's `SpeculativeConfig.use_eagle()` groups methods whose reusable draft state depends
on target-derived state and a shifted/following token. The group includes EAGLE, EAGLE3,
MTP, DFlash, and DSpark.

At a cache boundary, an ordinary target prefix hash proves the tokens in that block. It
does **not** prove the finalized token immediately after the boundary, even though that
token contributes to the draft input used to produce the boundary's draft cache entry.
For example:

```text
request A: a b c d | e
request B: a b c d | f
```

A normal hash for `a b c d` is identical, but the draft boundary input differs (`e`
versus `f`). Reusing the final draft block without proving the successor token can restore
state created for the wrong continuation.

The conservative vLLM behavior is therefore to drop or rewind the final matched EAGLE
unit and recompute it.

## Hybrid Qwen cache reconciliation

Qwen3.8 combines full-attention cache groups with recurrent Mamba/GDN state. A hybrid
coordinator may only resume at a prefix that every required group can safely restore.
Conceptually:

```text
global reusable prefix = min(attention hit, Mamba resumable hit, draft hit)
```

The exact implementation uses coordinated/fixed-point lookup rather than this single
formula, but the safety result is the same: a longer attention hit cannot be used if the
recurrent group lacks a matching resumable state.

In this port:

1. `dflash` is classified as EAGLE-style through `use_eagle()`.
2. Qwen's fallback grouping marks the relevant hybrid groups for the conservative EAGLE
   path.
3. Full attention drops the final speculative boundary unit.
4. The backported PR #48375 makes Mamba honor the same requirement by searching for an
   earlier recurrent snapshot.
5. With `mamba-cache-mode=align`, the earlier resumable Mamba snapshot may be much farther
   back than an attention hash unit—or absent.
6. When no earlier Mamba state is available, its safe hit is zero.
7. Hybrid reconciliation lowers the global hit to zero.

This behavior is expensive but safe. PR #48375 explicitly notes that when only the final
boundary state exists, the fixed behavior can collapse the hit to zero rather than reuse
potentially poisoned recurrent state.

## Why PR #48375 is necessary

Before PR #48375, `MambaManager.find_longest_cache_hit` accepted
`drop_eagle_block` but ignored it. Full attention rewound while Mamba retained the last
snapshot. Upstream reports linked this mismatch to wrong answers and malformed tool calls
that could emerge only after repeated cache reuse.

The patch lowers Mamba's search ceiling by one page so it restores a real earlier
snapshot. A literal list pop would be wrong for Mamba's null-padded representation. The
local experiment applies commit:

```text
4532e8a9d85ea69e8770a7ee2b8085010a56ea64
```

Source: [vLLM PR #48375](https://github.com/vllm-project/vllm/pull/48375).

## Unsafe apparent fixes

### Remove DFlash from `use_eagle()`

Do not do this. It would tell the cache coordinator that DFlash draft state has no
successor-token dependency. Nonzero counters would not prove the reused draft state was
valid.

### Disable `drop_eagle_block`

Do not do this. It can restore a boundary snapshot that includes state for rejected or
different draft tokens. The failure may surface as a quality or tool-call regression
long after startup rather than an exception.

### Remove PR #48375 but leave prefix caching on

Do not do this. It recreates the attention/Mamba mismatch the patch fixes. A faster hit
rate obtained by permitting stale recurrent state is not an optimization.

### Declare prefix caching unnecessary because llama-benchy uses `--no-cache`

Do not do this. Long-lived coding agents repeatedly send a growing conversation prefix.
Follow-up TTFT and prefill work are production requirements independent of a benchmark's
client-side cache controls.

### Disable prefix caching permanently

This is safe from stale-cache reuse but fails the product objective: every follow-up turn
reprocesses the full conversation. The no-draft control's 5.44 s → 1.37 s repeat result
shows the cost even at only ~5K tokens.

## Correct architectural directions

### Successor-aware EAGLE hashing

[vLLM RFC #50438](https://github.com/vllm-project/vllm/issues/50438) and
[PR #50897](https://github.com/vllm-project/vllm/pull/50897) add the finalized successor
token and its input identity to EAGLE-style cache keys. A successful hit then proves the
boundary input is equal, allowing the final draft block to be retained safely.

The key idea is:

```text
ordinary block key = hash(prefix, tokens[s:e], extra keys)
EAGLE block key    = hash(prefix, tokens[s:e+1], extra keys through e)
```

Publication must wait until the successor token is finalized **and** the corresponding
draft cache write is materialized. This is more than a hash-format tweak; scheduler,
request lifecycle, connectors, preemption, and cache publication must agree.

PR #50897 explicitly scopes `use_eagle()` methods including DFlash and keeps normal
hashes for target-only Mamba state groups. It is the preferred long-term direction, but
as of the experiment date it remained a large open change with review concerns and
connector complexity.

### Publish resumable hybrid boundary state

[vLLM PR #52244](https://github.com/vllm-project/vllm/pull/52244), especially commit
`72d05f40fcdd74bf8c5574fef6d9ccc01e0d70ab`, publishes Mamba state where a conservative
EAGLE replay actually lands and adds a reachable full-attention tail at the same depth.
It addresses the case where safe rewind exists logically but no state was materialized
there.

This is a useful fallback/bridge, but its own review notes call successor-aware hashing
the more proper fix and warn that extra prefill chunk boundaries may hurt TTFT.

### Hybrid SSM boundary-state work

[vLLM RFC #52817](https://github.com/vllm-project/vllm/issues/52817) discusses four
families of solutions for hybrid models:

- partial-match block promotion;
- next-token receipt on cached blocks;
- explicit boundary EAGLE state storage;
- sparse EAGLE state cache.

The RFC exists because dropping one aligned hybrid unit can mean recomputing hundreds or
thousands of tokens, not just a 16-token attention block.

## Root-cause confidence

The local A/B proves that DFlash/spec-decode activation is necessary for the observed
zero-hit symptom under this configuration. Source inspection and upstream reports explain
a mechanism that predicts that symptom. However, no instrumented local build recorded
per-group hit lengths at every reconciliation step.

Therefore:

- **proven locally:** DFlash2 arm zero, no-draft arm nonzero under matched settings;
- **verified in source/upstream design:** DFlash is EAGLE-style; final-boundary rewind is
  required; hybrid groups reconcile to a jointly resumable prefix; PR #48375 can safely
  return zero when no earlier Mamba state exists;
- **strong interpretation:** lack of a materialized earlier hybrid boundary caused the
  global P11 hit to collapse to zero;
- **not yet proven by local instrumentation:** the exact per-group length sequence for
  every P11 request.

## Required correctness test matrix for any fix

A candidate fix must pass all of these before throughput testing:

1. **A→A:** identical prompt replay produces nonzero hits and lower TTFT.
2. **A→B→A:** a divergent continuation between identical requests does not poison the
   restored state.
3. **Boundary variants:** successor token equal, different, and not yet known.
4. **Greedy parity:** byte-identical output with APC on/off and DFlash on/off for fixed
   deterministic prompts.
5. **Tool turns:** repeated native tool calls remain valid JSON/tool events after cache
   hits.
6. **Hybrid depths:** prompts around attention hash and Mamba alignment boundaries.
7. **Chunked prefill:** cached and uncached chunk boundaries.
8. **c2 scheduling:** two simultaneous sessions with divergent prefixes.
9. **Preemption/resume:** no publication of unmaterialized draft state.
10. **Acceptance:** no silent collapse to mean acceptance length near 1.0.
11. **Metrics:** per-group hit lengths and global reconciled length agree with expected
    safe boundaries.
12. **Soak:** repeated cache reuse through long sessions and context compression.

A nonzero hit counter alone is insufficient. The release blocker is any deterministic
output divergence or malformed tool behavior caused by cache reuse.
