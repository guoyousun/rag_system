# -*- coding: utf-8 -*-
"""
千问大模型服务（OpenAI 库兼容端点）。
- chat(): 普通补全
- chat_stream(): 流式补全（SSE）
- extract_entities(): 从文本抽取实体/关系三元组，返回结构化 JSON
所有模型名、BaseURL、Key 均来自 .env，服务内部不做硬编码。
"""
import json
import re
from typing import Iterator

from openai import OpenAI

from app.core.config import settings

_llm_client: OpenAI | None = None


def get_llm_client() -> OpenAI:
    global _llm_client
    if _llm_client is None:
        if not settings.QWEN_API_KEY or settings.QWEN_API_KEY.startswith("sk-your"):
            raise RuntimeError(
                "未配置千问 API Key：请在 backend/.env 中填写 QWEN_API_KEY "
                "(阿里云百炼控制台申请: https://bailian.console.aliyun.com/)"
            )
        _llm_client = OpenAI(
            api_key=settings.QWEN_API_KEY,
            base_url=settings.QWEN_LLM_BASE_URL,
            timeout=120,
            max_retries=2,
        )
    return _llm_client


def chat(messages: list[dict], temperature: float | None = None, max_tokens: int | None = None) -> str:
    """普通对话补全"""
    client = get_llm_client()
    resp = client.chat.completions.create(
        model=settings.QWEN_LLM_MODEL,
        messages=messages,
        temperature=temperature if temperature is not None else settings.LLM_TEMPERATURE,
        max_tokens=max_tokens or settings.LLM_MAX_TOKENS,
    )
    return resp.choices[0].message.content or ""


def chat_stream(messages: list[dict], temperature: float | None = None) -> Iterator[str]:
    """流式对话补全，逐段 yield 文本增量"""
    client = get_llm_client()
    stream = client.chat.completions.create(
        model=settings.QWEN_LLM_MODEL,
        messages=messages,
        temperature=temperature if temperature is not None else settings.LLM_TEMPERATURE,
        stream=True,
    )
    for chunk in stream:
        if chunk.choices and chunk.choices[0].delta and chunk.choices[0].delta.content:
            yield chunk.choices[0].delta.content


def extract_entities(text: str) -> dict:
    """
    从文本中抽取工业领域实体与关系，返回:
    {"entities": [{"name": str, "type": str}], "relations": [{"source": str, "target": str, "relation": str}]}
    使用千问模型 + JSON 输出约束；解析失败时降级为空结构（不阻塞流水线）。
    """
    prompt = (
        "你是工业垂直领域知识抽取引擎。请从下面的技术文档片段中抽取：\n"
        "1. 实体(entities)：工业设备、零部件、工艺、参数指标、材料、故障、系统/软件模块、文档主题等；\n"
        "2. 关系(relations)：实体之间的语义关系，如\"包含/属于/用于/由...组成/参数为/可能导致/安装在\"等。\n"
        "要求：\n"
        "- 实体名称保留原文中的规范名称；\n"
        "- 只抽取明确出现的信息，不要臆造；\n"
        "- 关系必须连接已抽取的实体；\n"
        "- 输出严格 JSON，不要输出任何其他文字，格式如下：\n"
        '{"entities": [{"name": "实体名", "type": "设备/工艺/参数/材料/故障/系统/其他"}], '
        '"relations": [{"source": "实体A", "target": "实体B", "relation": "关系类型"}]}\n\n'
        f"文档片段：\n{text[:4000]}"
    )
    try:
        resp = chat(
            [
                {"role": "system", "content": "你只输出合法 JSON。"},
                {"role": "user", "content": prompt},
            ],
            temperature=0.1,
            max_tokens=1024,
        )
        return _parse_entity_json(resp)
    except Exception:
        return {"entities": [], "relations": []}


def _parse_entity_json(raw: str) -> dict:
    """容错解析 LLM 返回的 JSON（去除 ```json 包裹等）"""
    text = raw.strip()
    text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text, flags=re.MULTILINE)
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        # 尝试截取第一个 { 到最后一个 }
        start, end = text.find("{"), text.rfind("}")
        if start >= 0 and end > start:
            try:
                data = json.loads(text[start : end + 1])
            except json.JSONDecodeError:
                return {"entities": [], "relations": []}
        else:
            return {"entities": [], "relations": []}
    entities = data.get("entities", []) if isinstance(data, dict) else []
    relations = data.get("relations", []) if isinstance(data, dict) else []
    return {
        "entities": [
            {"name": str(e.get("name", "")).strip(), "type": str(e.get("type", "其他")).strip()}
            for e in entities
            if isinstance(e, dict) and e.get("name")
        ],
        "relations": [
            {
                "source": str(r.get("source", "")).strip(),
                "target": str(r.get("target", "")).strip(),
                "relation": str(r.get("relation", "关联")).strip(),
            }
            for r in relations
            if isinstance(r, dict) and r.get("source") and r.get("target")
        ],
    }
