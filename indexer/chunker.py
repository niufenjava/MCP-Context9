import re

def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> list[str]:
    """按固定长度分块，支持 overlap"""
    if len(text) <= chunk_size:
        return [text]

    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        chunks.append(chunk)
        start = end - overlap
    return chunks

def chunk_markdown(markdown: str, max_chunk_size: int = 500) -> list[dict]:
    """按标题结构分块，返回 [{title, content, level}, ...]"""
    lines = markdown.split("\n")
    chunks = []
    current_title = ""
    current_level = 0
    current_content = []

    def save_chunk():
        if current_content:
            content = "\n".join(current_content).strip()
            if content:
                chunks.append({
                    "title": current_title or "Untitled",
                    "level": current_level,
                    "content": content
                })

    for line in lines:
        header_match = re.match(r"^(#{1,6})\s+(.+)", line)
        if header_match:
            save_chunk()
            current_level = len(header_match.group(1))
            current_title = header_match.group(2)
            current_content = [line]
        else:
            current_content.append(line)

    save_chunk()

    result = []
    for chunk in chunks:
        if len(chunk["content"]) <= max_chunk_size:
            result.append(chunk)
        else:
            sub_chunks = chunk_text(chunk["content"], max_chunk_size, 50)
            for sc in sub_chunks:
                result.append({
                    "title": chunk["title"],
                    "level": chunk["level"],
                    "content": sc
                })
    return result