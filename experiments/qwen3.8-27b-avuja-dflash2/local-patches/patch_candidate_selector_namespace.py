#!/usr/bin/env python3
"""Give DFlash2's candidate selector a dedicated torch.compile cache namespace.

Backports vllm-project/vllm#52816 commit 64c5b80 onto the Club-3090 v0.27.1
DFlash2 overlay. Without this, the selector can load the draft head's compiled
graph because both modules inherit the active drafter model tag.
"""

from pathlib import Path

TARGET = Path("/usr/local/lib/python3.12/dist-packages/vllm/model_executor/models/qwen3_dflash2.py")
IMPORT_OLD = "from vllm.compilation.decorators import support_torch_compile\n"
IMPORT_NEW = (
    "from vllm.compilation.backends import set_model_tag\n"
    "from vllm.compilation.decorators import support_torch_compile\n"
)
BLOCK_OLD = '''        self.candidate_selector = CandidateSelector(
            hidden_size=self.config.hidden_size,
            vocab_size=self.config.vocab_size,
            rank=int(draft_config["selector_rank"]),
            top_k=int(draft_config["selector_top_k"]),
            params_dtype=vllm_config.model_config.dtype,
            prefix=maybe_prefix(prefix, "candidate_selector"),
        )
'''
BLOCK_NEW = '''        # Keep the selector out of the draft head's compile-cache namespace.
        # The two compiled modules have different input signatures.
        with set_model_tag("dflash2_candidate_selector"):
            self.candidate_selector = CandidateSelector(
                hidden_size=self.config.hidden_size,
                vocab_size=self.config.vocab_size,
                rank=int(draft_config["selector_rank"]),
                top_k=int(draft_config["selector_top_k"]),
                params_dtype=vllm_config.model_config.dtype,
                prefix=maybe_prefix(prefix, "candidate_selector"),
            )
'''


def replace_once(source: str, old: str, new: str, label: str) -> str:
    if new in source:
        return source
    count = source.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected one anchor, found {count}")
    return source.replace(old, new, 1)


def main() -> None:
    source = TARGET.read_text(encoding="utf-8")
    source = replace_once(source, IMPORT_OLD, IMPORT_NEW, "set_model_tag import")
    source = replace_once(source, BLOCK_OLD, BLOCK_NEW, "candidate selector block")
    _ = TARGET.write_text(source, encoding="utf-8")
    print("[dflash2-local] candidate-selector compile namespace applied")


if __name__ == "__main__":
    main()
