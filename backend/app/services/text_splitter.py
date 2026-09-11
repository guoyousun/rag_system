# -*- coding: utf-8 -*-
"""
文本分块器：语义段落合并分块（chunk_size / chunk_overlap 由 .env 配置）。

背景：旧实现按"每行一个块"切分，对 Markdown/逐行文档（标题行、列表项）
会把语义单元切成 10~30 字的碎片，导致检索命中标题却丢失正文、LLM 上下文
碎片化。本实现改为：
  1. 按行累积内容，空行为段落边界时切块；
  2. 无空行的连续文档（标题+正文+列表项）累积到 chunk_size 硬上限再切，
     保证标题与其下内容、列表项与其上下文属于同一块；
  3. 超过 chunk_size 的长段落仍按句子边界递归切分（复用原 _split_long_text）。
"""


def split_text(text: str, chunk_size: int = 500, chunk_overlap: int = 50) -> list[str]:
    if not text or not text.strip():
        return []
    chunks: list[str] = []
    buffer: list[str] = []
    buffer_len = 0

    def flush():
        nonlocal buffer, buffer_len
        if not buffer:
            return
        piece = "\n".join(buffer).strip()
        buffer = []
        buffer_len = 0
        if not piece:
            return
        if len(piece) <= chunk_size:
            chunks.append(piece)
        else:
            chunks.extend(_split_long_text(piece, chunk_size, chunk_overlap))

    for line in text.split("\n"):
        line = line.rstrip()
        if not line.strip():
            flush()  # 空行 = 段落边界
            continue
        if buffer and buffer_len + len(line) + 1 > chunk_size:
            flush()  # 硬上限：先切出当前块
        buffer.append(line)
        buffer_len += len(line) + 1
    flush()
    return chunks


def _split_long_text(text: str, chunk_size: int, chunk_overlap: int) -> list[str]:
    """递归切分单个长文本段，优先在句子边界断开（overlap 保留入参以兼容配置）"""
    if len(text) <= chunk_size:
        return [text]

    # 在 chunk_size 附近找最近的句子边界
    cut = min(chunk_size, len(text))
    window = text[cut // 2 : cut]  # 前半段找边界，避免切太靠前
    for sep in ("。", "！", "？", "；", "\n", ". ", "! ", "? ", "; ", "，", ", "):
        idx = window.rfind(sep)
        if idx != -1:
            cut = cut // 2 + idx + len(sep)
            break

    if cut <= 0 or cut >= len(text):
        cut = min(chunk_size, len(text))

    head = text[:cut].strip()
    tail = text[cut:].strip()
    result = [head] if head else []
    if tail:
        result.extend(_split_long_text(tail, chunk_size, chunk_overlap))
    return result
