"""Qwen3 fine-tuning trainer with QLoRA + GRPO RL.

Two-phase training approach based on "Making Qwen3 Think in Korean" (2025):
1. SFT Phase: Supervised fine-tuning on high-quality Korean QA data
2. GRPO Phase: Reinforcement learning for Korean reasoning alignment

Uses Unsloth for 2x speed and 70% VRAM reduction.
"""

from __future__ import annotations

import logging

from .config import TrainingConfig

logger = logging.getLogger(__name__)


class Qwen3Trainer:
    """Two-phase Qwen3 fine-tuning trainer."""

    def __init__(self, config: TrainingConfig | None = None):
        self.config = config or TrainingConfig()

    def run_sft(self) -> str:
        """Phase 1: Supervised Fine-Tuning with QLoRA.

        Returns path to the saved adapter.
        """
        logger.info("Starting SFT phase with %s", self.config.base_model)

        if self.config.use_unsloth:
            return self._run_sft_unsloth()
        return self._run_sft_standard()

    def _run_sft_unsloth(self) -> str:
        """SFT using Unsloth for optimized training."""
        from datasets import load_dataset
        from transformers import TrainingArguments
        from trl import SFTTrainer
        from unsloth import FastLanguageModel

        # Load model with Unsloth optimizations
        model, tokenizer = FastLanguageModel.from_pretrained(
            model_name=self.config.base_model,
            max_seq_length=self.config.max_seq_length,
            dtype=None,  # Auto-detect
            load_in_4bit=self.config.load_in_4bit,
        )

        # Apply LoRA
        model = FastLanguageModel.get_peft_model(
            model,
            r=self.config.lora_r,
            target_modules=self.config.lora_target_modules,
            lora_alpha=self.config.lora_alpha,
            lora_dropout=self.config.lora_dropout,
            bias="none",
            use_gradient_checkpointing=self.config.use_gradient_checkpointing,
            use_rslora=self.config.use_rslora,
        )

        # Load dataset
        dataset = load_dataset("json", data_files=self.config.train_dataset_path, split="train")

        # Apply chat template
        def format_chat(example):
            text = tokenizer.apply_chat_template(
                example["messages"],
                tokenize=False,
                add_generation_prompt=False,
            )
            return {"text": text}

        dataset = dataset.map(format_chat)

        # Training arguments
        training_args = TrainingArguments(
            output_dir=self.config.output_dir,
            num_train_epochs=self.config.sft_epochs,
            per_device_train_batch_size=self.config.sft_batch_size,
            gradient_accumulation_steps=self.config.sft_gradient_accumulation,
            learning_rate=self.config.sft_learning_rate,
            lr_scheduler_type=self.config.sft_lr_scheduler,
            warmup_ratio=self.config.sft_warmup_ratio,
            weight_decay=self.config.sft_weight_decay,
            max_grad_norm=self.config.sft_max_grad_norm,
            fp16=False,
            bf16=True,
            logging_steps=self.config.logging_steps,
            save_steps=self.config.save_steps,
            eval_steps=self.config.eval_steps,
            seed=self.config.seed,
            report_to="none",
            dataset_text_field="text",
            packing=self.config.sft_packing,
        )

        trainer = SFTTrainer(
            model=model,
            tokenizer=tokenizer,
            train_dataset=dataset,
            args=training_args,
        )

        trainer.train()

        # Save adapter
        adapter_path = f"{self.config.output_dir}/sft_adapter"
        model.save_pretrained(adapter_path)
        tokenizer.save_pretrained(adapter_path)

        logger.info("SFT complete. Adapter saved to %s", adapter_path)
        return adapter_path

    def _run_sft_standard(self) -> str:
        """Fallback SFT without Unsloth."""
        import torch
        from datasets import load_dataset
        from peft import LoraConfig, get_peft_model
        from transformers import AutoModelForCausalLM, AutoTokenizer, TrainingArguments
        from trl import SFTTrainer

        tokenizer = AutoTokenizer.from_pretrained(self.config.base_model)
        model = AutoModelForCausalLM.from_pretrained(
            self.config.base_model,
            torch_dtype=torch.bfloat16,
            device_map="auto",
            load_in_4bit=self.config.load_in_4bit,
        )

        lora_config = LoraConfig(
            r=self.config.lora_r,
            lora_alpha=self.config.lora_alpha,
            lora_dropout=self.config.lora_dropout,
            target_modules=self.config.lora_target_modules,
            bias="none",
            task_type="CAUSAL_LM",
            use_rslora=self.config.use_rslora,
        )
        model = get_peft_model(model, lora_config)

        dataset = load_dataset("json", data_files=self.config.train_dataset_path, split="train")

        training_args = TrainingArguments(
            output_dir=self.config.output_dir,
            num_train_epochs=self.config.sft_epochs,
            per_device_train_batch_size=self.config.sft_batch_size,
            gradient_accumulation_steps=self.config.sft_gradient_accumulation,
            learning_rate=self.config.sft_learning_rate,
            bf16=True,
            save_steps=self.config.save_steps,
            logging_steps=self.config.logging_steps,
            seed=self.config.seed,
        )

        trainer = SFTTrainer(
            model=model,
            tokenizer=tokenizer,
            train_dataset=dataset,
            args=training_args,
        )
        trainer.train()

        adapter_path = f"{self.config.output_dir}/sft_adapter"
        model.save_pretrained(adapter_path)
        tokenizer.save_pretrained(adapter_path)
        return adapter_path

    def run_grpo(self, sft_adapter_path: str) -> str:
        """Phase 2: GRPO Reinforcement Learning for Korean reasoning.

        Based on "Making Qwen3 Think in Korean" (Aug 2025):
        - Uses oracle judge model for reward calibration
        - Prevents reward hacking and policy collapse
        - Enhances Korean reasoning without losing general ability
        """
        if not self.config.grpo_enabled:
            logger.info("GRPO disabled, skipping RL phase")
            return sft_adapter_path

        logger.info("Starting GRPO RL phase from %s", sft_adapter_path)

        from datasets import load_dataset
        from trl import GRPOConfig, GRPOTrainer
        from unsloth import FastLanguageModel

        # Load SFT model
        model, tokenizer = FastLanguageModel.from_pretrained(
            model_name=sft_adapter_path,
            max_seq_length=self.config.max_seq_length,
            load_in_4bit=self.config.load_in_4bit,
        )
        FastLanguageModel.for_inference(model)

        # Load evaluation dataset for GRPO
        dataset = load_dataset("json", data_files=self.config.eval_dataset_path, split="train")

        # GRPO configuration
        grpo_config = GRPOConfig(
            output_dir=f"{self.config.output_dir}/grpo",
            num_train_epochs=self.config.grpo_epochs,
            per_device_train_batch_size=self.config.grpo_batch_size,
            gradient_accumulation_steps=self.config.grpo_gradient_accumulation,
            learning_rate=self.config.grpo_learning_rate,
            num_generations=self.config.grpo_group_size,
            max_completion_length=1024,
            bf16=True,
            logging_steps=self.config.logging_steps,
            save_steps=self.config.save_steps,
            seed=self.config.seed,
            report_to="none",
        )

        # Reward function using oracle judge
        # Phase 7 — R2 완전 보강: OpenAI httpx 직접 호출(anti-patterns.md §1 위반) 제거.
        # GRPO worker 는 prefork Celery 환경이므로 동기 변종 ``generate_sync`` 사용.
        # AgentCode "docutil-evaluator" — LLM-as-Judge / 평가 전용 Agent.
        from app.integrations.llm.factory import create_llm_client

        judge_llm = create_llm_client("training_judge")

        def reward_function(completions: list[str], prompts: list[str]) -> list[float]:
            """Score completions using oracle judge model (AgentHub 위임)."""

            scores = []
            for completion, prompt in zip(completions, prompts, strict=False):
                try:
                    judge_prompt = (
                        f"Rate this Korean AI response on a scale of 0-10.\n"
                        f"Question: {prompt}\n"
                        f"Response: {completion}\n"
                        f"Criteria: accuracy, reasoning quality, Korean fluency, helpfulness.\n"
                        f"Output only the number."
                    )
                    # AgentHub `/v1/chat/completions` 동기 호출 — Celery prefork 워커에서
                    # asyncio 이벤트 루프 없이 사용 가능.
                    score_text = judge_llm.generate_sync(
                        messages=[{"role": "user", "content": judge_prompt}],
                        temperature=0.0,
                        max_tokens=10,
                    ).strip()
                    score = float(score_text) / 10.0
                    scores.append(max(0.0, min(1.0, score)))
                except Exception:
                    scores.append(0.5)
            return scores

        trainer = GRPOTrainer(
            model=model,
            processing_class=tokenizer,
            config=grpo_config,
            train_dataset=dataset,
            reward_funcs=[reward_function],
        )

        trainer.train()

        # Save final model
        final_path = f"{self.config.output_dir}/grpo_final"
        model.save_pretrained(final_path)
        tokenizer.save_pretrained(final_path)

        logger.info("GRPO RL complete. Final model saved to %s", final_path)
        return final_path

    def run_full_pipeline(self) -> str:
        """Run the complete two-phase training pipeline."""
        logger.info("=" * 60)
        logger.info("Starting Qwen3 Two-Phase Fine-Tuning Pipeline")
        logger.info("Base model: %s", self.config.base_model)
        logger.info("=" * 60)

        # Phase 1: SFT
        sft_path = self.run_sft()

        # Phase 2: GRPO RL
        final_path = self.run_grpo(sft_path)

        logger.info("=" * 60)
        logger.info("Training pipeline complete!")
        logger.info("Final model: %s", final_path)
        logger.info("=" * 60)

        return final_path
