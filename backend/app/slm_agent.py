"""
SLM Agent - Bllossom-8B 기반 Simple 질문 처리
"""
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from typing import Optional, Dict, Any
from pathlib import Path
import os
import json


class SLMAgent:
    """파인튜닝된 Bllossom-8B로 Simple 질문 처리"""
    
    def __init__(self, model_path: Optional[str] = None):
        self.model_path = model_path
        self.model = None
        self.tokenizer = None
        self.enabled = False
        
        # 모델 경로 탐색
        if not model_path:
            model_path = self._find_latest_model()
        
        if model_path and Path(model_path).exists():
            try:
                self._load_model(model_path)
                self.enabled = True
                print(f"✅ SLM 모델 로드 성공: {model_path}")
            except Exception as e:
                print(f"⚠️ SLM 모델 로드 실패: {e}")
                self.enabled = False
        else:
            print("⚠️ SLM 모델 없음 - LLM으로만 동작합니다")
            print(f"   파인튜닝 실행: cd backend/scripts && python3 finetune_slm.py")
            self.enabled = False
    
    def _find_latest_model(self) -> Optional[str]:
        """가장 최신 파인튜닝 모델 찾기"""
        models_dir = Path(__file__).parent.parent.parent / "models" / "finetuned"
        
        if not models_dir.exists():
            return None
        
        # 날짜순 정렬하여 최신 모델 찾기
        model_dirs = sorted(
            [d for d in models_dir.iterdir() if d.is_dir()],
            key=lambda x: x.name,
            reverse=True
        )
        
        if model_dirs:
            return str(model_dirs[0])
        
        return None
    
    def _load_model(self, model_path: str):
        """모델 로드"""
        self.tokenizer = AutoTokenizer.from_pretrained(
            model_path,
            trust_remote_code=True
        )
        
        # GPU 사용 가능 시 GPU, 아니면 CPU
        device_map = "auto" if torch.cuda.is_available() else "cpu"
        
        self.model = AutoModelForCausalLM.from_pretrained(
            model_path,
            device_map=device_map,
            torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
            trust_remote_code=True
        )
        
        self.model.eval()
    
    async def generate(
        self,
        question: str,
        max_new_tokens: int = 512,
        temperature: float = 0.7
    ) -> Dict[str, Any]:
        """
        SLM으로 답변 생성
        
        Returns:
            {
                "message": str,
                "confidence": float,
                "success": bool
            }
        """
        if not self.enabled:
            return {
                "message": "",
                "confidence": 0.0,
                "success": False,
                "error": "SLM not available"
            }
        
        try:
            # 프롬프트 구성 (Bllossom 형식)
            prompt = f"""### 질문: {question}

### 답변:"""
            
            # 토큰화
            inputs = self.tokenizer(
                prompt,
                return_tensors="pt",
                truncation=True,
                max_length=512
            )
            
            if torch.cuda.is_available():
                inputs = {k: v.cuda() for k, v in inputs.items()}
            
            # 생성
            with torch.no_grad():
                outputs = self.model.generate(
                    **inputs,
                    max_new_tokens=max_new_tokens,
                    temperature=temperature,
                    do_sample=True,
                    top_p=0.9,
                    pad_token_id=self.tokenizer.eos_token_id
                )
            
            # 디코딩
            generated_text = self.tokenizer.decode(
                outputs[0],
                skip_special_tokens=True
            )
            
            # 답변 부분만 추출
            answer = generated_text.split("### 답변:")[-1].strip()
            
            # 품질 검증
            confidence = self._evaluate_quality(answer)
            
            return {
                "message": answer,
                "confidence": confidence,
                "success": True
            }
        
        except Exception as e:
            print(f"⚠️ SLM 생성 에러: {e}")
            return {
                "message": "",
                "confidence": 0.0,
                "success": False,
                "error": str(e)
            }
    
    def _evaluate_quality(self, answer: str) -> float:
        """답변 품질 평가 (0.0 ~ 1.0)"""
        confidence = 1.0
        
        # 너무 짧은 답변
        if len(answer) < 10:
            confidence -= 0.3
        
        # "죄송합니다" 등 실패 표현
        failure_words = ["죄송", "모르", "없습니다", "확인할 수 없"]
        if any(word in answer for word in failure_words):
            confidence -= 0.4
        
        # 반복되는 패턴 (hallucination 징후)
        words = answer.split()
        if len(words) > 10 and len(set(words)) / len(words) < 0.5:
            confidence -= 0.3
        
        return max(0.0, confidence)


# 전역 인스턴스 (지연 초기화)
slm_agent: Optional[SLMAgent] = None


def get_slm_agent() -> SLMAgent:
    """SLM Agent 싱글톤 인스턴스"""
    global slm_agent
    if slm_agent is None:
        slm_agent = SLMAgent()
    return slm_agent
