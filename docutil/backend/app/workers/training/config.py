"""Training configuration for Qwen3 fine-tuning pipeline."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class TrainingConfig:
    """Configuration for Qwen3 QLoRA + GRPO fine-tuning.

    Based on latest Unsloth 2026 best practices:
    - Dynamic 4-bit quantization (recovers ~70% accuracy vs full precision)
    - FP8 GRPO for reinforcement learning on consumer GPUs
    - 500K context training support on 80GB GPU
    - Padding-free training with 30% VRAM savings
    """

    # Model
    base_model: str = "Qwen/Qwen3-32B"
    model_type: str = "causal_lm"
    max_seq_length: int = 8192
    load_in_4bit: bool = True
    dtype: str = "bfloat16"

    # LoRA
    lora_r: int = 64
    lora_alpha: int = 128
    lora_dropout: float = 0.05
    lora_target_modules: list[str] = field(
        default_factory=lambda: [
            "q_proj",
            "k_proj",
            "v_proj",
            "o_proj",
            "gate_proj",
            "up_proj",
            "down_proj",
        ]
    )
    use_rslora: bool = True  # Rank-Stabilized LoRA
    use_gradient_checkpointing: str = "unsloth"

    # Training (SFT Phase)
    sft_epochs: int = 3
    sft_batch_size: int = 2
    sft_gradient_accumulation: int = 8
    sft_learning_rate: float = 2e-4
    sft_lr_scheduler: str = "cosine"
    sft_warmup_ratio: float = 0.1
    sft_weight_decay: float = 0.01
    sft_max_grad_norm: float = 1.0
    sft_packing: bool = True

    # GRPO RL Phase (Group Relative Policy Optimization)
    grpo_enabled: bool = True
    grpo_epochs: int = 1
    grpo_batch_size: int = 1
    grpo_gradient_accumulation: int = 16
    grpo_learning_rate: float = 5e-6
    grpo_group_size: int = 4
    grpo_kl_coeff: float = 0.05
    grpo_clip_range: float = 0.2
    grpo_use_fp8: bool = True  # FP8 for GRPO on consumer GPUs

    # Oracle Judge (for GRPO reward calibration)
    judge_model: str = "gpt-4o"
    judge_temperature: float = 0.0

    # Data
    train_dataset_path: str = "data/train.jsonl"
    eval_dataset_path: str = "data/eval.jsonl"
    dataset_text_field: str = "text"
    reasoning_ratio: float = 0.75  # 75% reasoning, 25% non-reasoning
    min_quality_score: float = 0.8
    max_samples: int = 100_000

    # Output
    output_dir: str = "outputs/qwen3-finetuned"
    hub_model_id: str | None = None
    save_steps: int = 500
    eval_steps: int = 500
    logging_steps: int = 10

    # Hardware
    use_unsloth: bool = True
    seed: int = 42


@dataclass
class DataGenerationConfig:
    """Configuration for synthetic training data generation."""

    source_model: str = "gpt-4o"
    judge_model: str = "gpt-4o"

    # QA pair generation
    qa_per_chunk: int = 3
    qa_temperature: float = 0.7
    qa_max_tokens: int = 1024

    # Quality filtering
    min_judge_score: float = 0.8
    max_judge_retries: int = 2

    # Output
    output_path: str = "data/synthetic_qa.jsonl"
    target_samples: int = 50_000
