"""
Bllossom-8B 파인튜닝 스크립트
"""
import os
import json
import torch
from datetime import datetime
from pathlib import Path
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    TrainingArguments,
    Trainer,
    DataCollatorForLanguageModeling
)
from peft import LoraConfig, get_peft_model
from datasets import Dataset
import subprocess


# 경로 설정 (backend/scripts 기준)
SCRIPT_DIR = Path(__file__).parent  # backend/scripts
BACKEND_DIR = SCRIPT_DIR.parent      # backend
PROJECT_ROOT = BACKEND_DIR.parent    # agent-khu

MODELS_DIR = PROJECT_ROOT / "models"
CHECKPOINTS_DIR = MODELS_DIR / "checkpoints"
FINETUNED_DIR = MODELS_DIR / "finetuned"
TRAINING_DATA_FILE = SCRIPT_DIR / "training_data.jsonl"
LOGS_DIR = PROJECT_ROOT / "logs"

# 디렉토리 생성
MODELS_DIR.mkdir(exist_ok=True)
CHECKPOINTS_DIR.mkdir(exist_ok=True)
FINETUNED_DIR.mkdir(exist_ok=True)
LOGS_DIR.mkdir(exist_ok=True)


def extract_training_data():
    """Elasticsearch에서 학습 데이터 추출"""
    print("📊 학습 데이터 추출 중...")
    
    # extract_training_data.py 실행
    result = subprocess.run(
        ["python3", str(SCRIPT_DIR / "extract_training_data.py")],
        capture_output=True,
        text=True,
        cwd=str(SCRIPT_DIR)
    )
    
    if result.returncode != 0:
        print(f"❌ 데이터 추출 실패: {result.stderr}")
        return False
    
    print(result.stdout)
    return True


def load_training_data():
    """JSONL 파일에서 학습 데이터 로드"""
    if not TRAINING_DATA_FILE.exists():
        print(f"❌ 학습 데이터 파일 없음: {TRAINING_DATA_FILE}")
        return None
    
    data = []
    with open(TRAINING_DATA_FILE, "r", encoding="utf-8") as f:
        for line in f:
            data.append(json.loads(line))
    
    print(f"✅ {len(data)}개 학습 데이터 로드")
    return data


def format_prompt(example):
    """Bllossom 형식으로 프롬프트 포맷팅"""
    return f"""### 질문: {example['input']}

### 답변: {example['output']}"""


def prepare_dataset(data, tokenizer):
    """데이터셋 준비"""
    formatted_data = []
    for example in data:
        formatted_data.append({
            "text": format_prompt(example)
        })
    
    dataset = Dataset.from_list(formatted_data)
    
    def tokenize_function(examples):
        return tokenizer(
            examples["text"],
            truncation=True,
            max_length=512,
            padding="max_length"
        )
    
    tokenized_dataset = dataset.map(
        tokenize_function,
        batched=True,
        remove_columns=dataset.column_names
    )
    
    return tokenized_dataset


def finetune():
    """Bllossom-8B 파인튜닝 실행"""
    print("\n🚀 Bllossom-8B 파인튜닝 시작")
    print(f"📁 프로젝트 루트: {PROJECT_ROOT}")
    print(f"⏰ 시작 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # 1. 학습 데이터 추출
    if not extract_training_data():
        return False
    
    # 2. 데이터 로드
    data = load_training_data()
    if not data or len(data) < 10:
        print("❌ 학습 데이터 부족 (최소 10개 필요)")
        return False
    
    # 3. 모델 & 토크나이저 로드
    print("\n📦 모델 로딩 중...")
    # Qwen 2.5 3B Instruct (HF weights; GGUF는 학습 불가)
    model_name = "Qwen/Qwen2.5-3B-Instruct"

    tokenizer = AutoTokenizer.from_pretrained(
        model_name,
        trust_remote_code=True
    )
    tokenizer.pad_token = tokenizer.eos_token

    # CPU 환경에서 bitsandbytes 4bit가 동작하지 않으므로 기본 로딩으로 전환
    # (메모리 부담이 크면 더 작은 모델로 교체 필요)
    device_map = "auto" if torch.cuda.is_available() else {"": "cpu"}
    dtype = torch.float16 if torch.cuda.is_available() else torch.float32

    model = AutoModelForCausalLM.from_pretrained(
        model_name,
        device_map=device_map,
        torch_dtype=dtype,
        trust_remote_code=True
    )
    
    # 4. LoRA 설정
    print("🔧 LoRA 설정 중...")
    
    lora_config = LoraConfig(
        r=16,
        lora_alpha=32,
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj"],
        lora_dropout=0.05,
        bias="none",
        task_type="CAUSAL_LM"
    )
    
    model = get_peft_model(model, lora_config)
    model.print_trainable_parameters()
    
    # 5. 데이터셋 준비
    print("\n📚 데이터셋 준비 중...")
    dataset = prepare_dataset(data, tokenizer)
    
    # 6. 학습 설정
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = CHECKPOINTS_DIR / f"bllossom-khu-{timestamp}"
    
    training_args = TrainingArguments(
        output_dir=str(output_dir),
        num_train_epochs=3,
        per_device_train_batch_size=1 if not torch.cuda.is_available() else 4,
        gradient_accumulation_steps=1 if not torch.cuda.is_available() else 4,
        learning_rate=2e-4,
        fp16=torch.cuda.is_available(),
        bf16=False,
        logging_steps=10,
        save_steps=100,
        save_total_limit=3,
        warmup_steps=10,
        report_to="tensorboard",
        logging_dir=str(output_dir / "logs")
    )
    
    # 7. Trainer 설정
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=dataset,
        data_collator=DataCollatorForLanguageModeling(tokenizer, mlm=False)
    )
    
    # 8. 학습 시작
    print("\n🎓 학습 시작...\n")
    trainer.train()
    
    # 9. 모델 저장
    final_model_dir = FINETUNED_DIR / f"bllossom-khu-{timestamp}"
    print(f"\n💾 모델 저장 중: {final_model_dir}")
    
    trainer.model.save_pretrained(str(final_model_dir))
    tokenizer.save_pretrained(str(final_model_dir))
    
    # 10. 메타데이터 저장
    metadata = {
        "model_name": model_name,
        "timestamp": timestamp,
        "num_samples": len(data),
        "epochs": 3,
        "output_dir": str(final_model_dir)
    }
    
    with open(final_model_dir / "metadata.json", "w") as f:
        json.dump(metadata, f, indent=2)
    
    print(f"\n✅ 파인튜닝 완료!")
    print(f"📁 모델 위치: {final_model_dir}")
    print(f"⏰ 종료 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    return True


if __name__ == "__main__":
    try:
        success = finetune()
        exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ 에러 발생: {e}")
        import traceback
        traceback.print_exc()
        exit(1)