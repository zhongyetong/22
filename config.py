# config.py
import os
from dotenv import load_dotenv

load_dotenv()

DEEPSEEK_API_KEY = os.getenv("sk-6a9028dac8984edba9ac0e9afc6ceb31")

MODEL_NAME = "deepseek-chat"  # 支持Function Calling的模型