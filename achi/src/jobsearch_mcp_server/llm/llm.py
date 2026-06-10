# src/jobsearch_mcp_server/llm/llm.py
"""
LLM 调用封装模块
================
提供 DeepSeek API 的调用封装，支持：
- 自动重试（指数退避）
- 简单内存缓存（相同请求不重复调用）
- 超时控制
"""

import os
import time
import hashlib
import json
from typing import Optional
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com/v1"
)

# ============================================================
#  缓存配置
# ============================================================
_cache = {}
CACHE_ENABLED = os.getenv("LLM_CACHE_ENABLED", "true").lower() == "true"
CACHE_TTL = int(os.getenv("LLM_CACHE_TTL", "300"))  # 默认缓存 5 分钟


def _make_cache_key(messages: list, model: str, temperature: float) -> str:
    """生成缓存键"""
    data = json.dumps({"messages": messages, "model": model, "temperature": temperature},
                      ensure_ascii=False, sort_keys=True)
    return hashlib.md5(data.encode("utf-8")).hexdigest()


def _get_from_cache(key: str) -> Optional[str]:
    """从缓存获取"""
    if not CACHE_ENABLED:
        return None
    entry = _cache.get(key)
    if entry is None:
        return None
    # 检查 TTL
    if time.time() - entry["time"] > CACHE_TTL:
        del _cache[key]
        return None
    return entry["value"]


def _set_cache(key: str, value: str):
    """写入缓存"""
    if CACHE_ENABLED:
        _cache[key] = {"value": value, "time": time.time()}


def clear_cache():
    """清空缓存"""
    _cache.clear()


# ============================================================
#  发送消息（带重试和缓存）
# ============================================================
def send_messages(
    messages,
    model="deepseek-chat",
    temperature=0.7,
    max_tokens=2000,
    max_retries=3,
    use_cache=True,
):
    """
    发送消息到 LLM，带自动重试和缓存

    参数:
        messages:    消息列表
        model:       模型名称
        temperature: 温度参数
        max_tokens:  最大输出 token 数
        max_retries: 最大重试次数
        use_cache:   是否使用缓存

    返回:
        LLM 回复文本
    """
    # 缓存检查
    if use_cache:
        cache_key = _make_cache_key(messages, model, temperature)
        cached = _get_from_cache(cache_key)
        if cached is not None:
            return cached

    # 带重试的调用
    last_error = None
    for attempt in range(max_retries + 1):
        try:
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                timeout=30,  # 30 秒超时
            )
            result = response.choices[0].message.content

            # 写入缓存
            if use_cache:
                _set_cache(cache_key, result)

            return result

        except Exception as e:
            last_error = e
            if attempt < max_retries:
                # 指数退避：1s, 2s, 4s
                wait_time = 2 ** attempt
                print(f"⚠️ LLM 调用失败 (尝试 {attempt + 1}/{max_retries + 1}): {e}")
                print(f"   等待 {wait_time}s 后重试...")
                time.sleep(wait_time)
            else:
                print(f"❌ LLM 调用最终失败: {e}")

    raise last_error or Exception("LLM 调用失败（未知错误）")
