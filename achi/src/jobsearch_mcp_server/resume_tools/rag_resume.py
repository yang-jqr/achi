"""
功能一：RAG 简历浓缩
1. 简历导入向量数据库 - 将简历文本分块后存入 Qdrant（本地模式）
2. 使用 RAG 浓缩简历 - 检索相关片段 + LLM 生成浓缩版简历
"""

import os
import hashlib
import uuid
from typing import List, Optional
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

# ---------- 向量数据库：使用 Qdrant（本地模式） ----------
try:
    from qdrant_client import QdrantClient
    from qdrant_client.models import (
        VectorParams,
        Distance,
        PointStruct,
        Filter,
        FieldCondition,
        MatchValue,
    )
    HAS_QDRANT = True
except ImportError:
    HAS_QDRANT = False

# ---------- LLM 客户端 ----------
client = OpenAI(
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com/v1"
)

# 向量维度（DeepSeek 嵌入维度）
EMBEDDING_DIM = 1024


# ============================================================
#  工具函数：文本分块
# ============================================================
def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
    """将长文本按指定大小分块，块之间带重叠"""
    if not text:
        return []
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        if chunk.strip():
            chunks.append(chunk.strip())
        start += chunk_size - overlap
    return chunks


# ============================================================
#  工具函数：获取文本嵌入向量
# ============================================================
def get_embedding(text: str) -> List[float]:
    """调用 DeepSeek 嵌入 API 获取文本向量"""
    try:
        resp = client.embeddings.create(
            model="deepseek-embedding",
            input=text
        )
        return resp.data[0].embedding
    except Exception as e:
        # fallback：使用简单哈希模拟嵌入
        h = hashlib.md5(text.encode("utf-8")).hexdigest()
        vec = [float(ord(c)) / 255.0 for c in h]
        # 填充或截断到 EMBEDDING_DIM
        if len(vec) < EMBEDDING_DIM:
            vec.extend([0.0] * (EMBEDDING_DIM - len(vec)))
        else:
            vec = vec[:EMBEDDING_DIM]
        return vec


# ============================================================
#  RagResume 类
# ============================================================
class RagResume:
    """
    RAG 简历浓缩器（基于 Qdrant 本地模式）

    用法:
        rr = RagResume()
        # 1. 导入简历
        rr.import_resume("张三的简历...", resume_id="zhangsan")
        # 2. 浓缩简历
        summary = rr.summarize(resume_id="zhangsan", target_length="300字以内")
    """

    def __init__(self, persist_dir: str = None):
        if persist_dir is None:
            persist_dir = os.path.join(
                os.path.dirname(__file__), "..", "..", "..", "qdrant_resume_db"
            )
        self.persist_dir = os.path.abspath(persist_dir)
        self.collection_name = "resumes"

        if not HAS_QDRANT:
            raise ImportError(
                "请先安装 qdrant-client: uv add qdrant-client"
            )

        # 初始化 Qdrant 本地客户端
        os.makedirs(self.persist_dir, exist_ok=True)
        self._client = QdrantClient(path=self.persist_dir)

        # 确保集合存在
        self._ensure_collection()

    def _ensure_collection(self):
        """如果集合不存在则创建"""
        collections = self._client.get_collections().collections
        exists = any(c.name == self.collection_name for c in collections)
        if not exists:
            self._client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(
                    size=EMBEDDING_DIM,
                    distance=Distance.COSINE
                )
            )

    # ----------------------------------------------------------
    #  1. 简历导入向量数据库
    # ----------------------------------------------------------
    def import_resume(
        self,
        resume_text: str,
        resume_id: str = None,
        metadata: dict = None,
        chunk_size: int = 500,
        chunk_overlap: int = 50
    ) -> int:
        """
        将简历文本分块后导入向量数据库

        参数:
            resume_text:   简历全文
            resume_id:     简历唯一标识（如姓名），不传则自动生成
            metadata:      附加元数据（如 {"name": "张三", "source": "pdf"}）
            chunk_size:    分块大小（字符数）
            chunk_overlap: 块间重叠字符数

        返回:
            导入的块数
        """
        if metadata is None:
            metadata = {}
        if resume_id is None:
            resume_id = hashlib.md5(resume_text.encode("utf-8")).hexdigest()[:12]

        # 分块
        chunks = chunk_text(resume_text, chunk_size=chunk_size, overlap=chunk_overlap)
        if not chunks:
            raise ValueError("简历文本为空，无法导入")

        # 先删除该 resume_id 的旧数据
        self.delete_resume(resume_id)

        # 生成嵌入并入库
        points = []
        for i, chunk in enumerate(chunks):
            vec = get_embedding(chunk)
            point_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"{resume_id}_chunk_{i}"))
            points.append(PointStruct(
                id=point_id,
                vector=vec,
                payload={
                    "resume_id": resume_id,
                    "chunk_index": i,
                    "text": chunk,
                    "name": metadata.get("name", ""),
                    "source": metadata.get("source", ""),
                }
            ))

        self._client.upsert(
            collection_name=self.collection_name,
            points=points
        )

        return len(chunks)

    # ----------------------------------------------------------
    #  2. 使用 RAG 浓缩简历
    # ----------------------------------------------------------
    def summarize(
        self,
        resume_id: str,
        target_length: str = "300字以内",
        n_results: int = 5,
        custom_query: str = None
    ) -> str:
        """
        使用 RAG 检索简历相关片段，并通过 LLM 生成浓缩版简历

        参数:
            resume_id:     简历标识
            target_length: 目标长度描述
            n_results:     检索的片段数量
            custom_query:  自定义检索查询

        返回:
            浓缩后的简历文本
        """
        # 构建检索查询
        query_text = custom_query or f"简历 {resume_id} 的核心技能、工作经历、教育背景"
        query_emb = get_embedding(query_text)

        # 向量检索（带 resume_id 过滤）
        search_result = self._client.search(
            collection_name=self.collection_name,
            query_vector=query_emb,
            limit=n_results,
            query_filter=Filter(
                must=[FieldCondition(
                    key="resume_id",
                    match=MatchValue(value=resume_id)
                )]
            )
        )

        if not search_result:
            return f"未找到 resume_id='{resume_id}' 的简历，请先调用 import_resume() 导入。"

        # 拼接检索到的片段
        retrieved_chunks = [hit.payload["text"] for hit in search_result if hit.payload]
        context = "\n\n".join(retrieved_chunks)

        # 调用 LLM 浓缩
        system_prompt = """你是一位顶级的简历优化顾问，拥有 10 年猎头和 HR 经验。请根据提供的简历片段，生成一份可以直接投递的浓缩版简历。

要求：
1. 保留核心信息：个人简介、技能特长、工作经历、项目经验、教育背景
2. 语言简洁精炼，突出重点，让 HR 在 10 秒内抓住关键信息
3. 保持专业、有力的语气，使用行业通用术语
4. 输出格式清晰易读，方便直接复制使用
5. 成果量化优先，每段经历至少包含一个可量化的成果"""

        user_prompt = f"""请将以下简历内容浓缩为 {target_length}，生成一份可以直接投递的简历摘要。

【原始简历片段】
{context}

【浓缩要求】
- 提取最核心的技能和经验，突出与目标岗位的匹配度
- 删除冗余描述，保留关键数据（年限、成果、技能名称等）
- 使用专业、有力的行业用语
- 输出格式：使用简洁的条目式结构，方便 HR 快速浏览"""

        try:
            response = client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.5,
                max_tokens=1500
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"LLM 浓缩失败：{str(e)}"

    # ----------------------------------------------------------
    #  辅助：列出所有已导入的简历
    # ----------------------------------------------------------
    def list_resumes(self) -> List[dict]:
        """列出向量库中所有简历及其元数据"""
        # 使用 scroll 遍历所有点，按 resume_id 去重
        all_points, _ = self._client.scroll(
            collection_name=self.collection_name,
            limit=10000
        )

        seen = {}
        for point in all_points:
            if not point.payload:
                continue
            rid = point.payload.get("resume_id")
            if rid and rid not in seen:
                seen[rid] = {
                    "resume_id": rid,
                    "name": point.payload.get("name", ""),
                    "source": point.payload.get("source", ""),
                }

        # 统计每个 resume_id 的块数
        result = []
        for rid, info in seen.items():
            count_result = self._client.count(
                collection_name=self.collection_name,
                count_filter=Filter(
                    must=[FieldCondition(
                        key="resume_id",
                        match=MatchValue(value=rid)
                    )]
                )
            )
            info["chunks"] = count_result.count
            result.append(info)

        return result

    # ----------------------------------------------------------
    #  辅助：删除简历
    # ----------------------------------------------------------
    def delete_resume(self, resume_id: str) -> bool:
        """从向量库中删除指定简历"""
        try:
            result = self._client.delete(
                collection_name=self.collection_name,
                points_selector=Filter(
                    must=[FieldCondition(
                        key="resume_id",
                        match=MatchValue(value=resume_id)
                    )]
                )
            )
            return True
        except Exception:
            return False


# ============================================================
#  独立运行测试
# ============================================================
if __name__ == "__main__":
    sample_resume = """
    张三，男，28岁，本科毕业于北京大学计算机科学与技术专业。
    
    工作经历：
    2020-2023 在阿里巴巴担任后端开发工程师，负责电商平台订单系统的设计与开发。
    使用 Java、Spring Boot、MySQL、Redis 等技术栈，支撑日均百万级订单处理。
    主导了订单分库分表改造，系统响应时间降低 40%。
    
    2023-至今 在字节跳动担任高级后端工程师，负责抖音支付系统的架构优化。
    使用 Go、Kafka、TiDB 等构建高可用支付链路，保证 99.99% 可用性。
    
    技能：
    - 编程语言：Java、Go、Python
    - 框架：Spring Boot、Spring Cloud、Gin
    - 数据库：MySQL、Redis、TiDB、MongoDB
    - 中间件：Kafka、RabbitMQ、Elasticsearch
    - 工具：Docker、Kubernetes、Git
    
    项目经验：
    1. 电商订单系统重构 - 将单体应用拆分为微服务架构，引入消息队列解耦
    2. 支付链路高可用改造 - 实现多活部署、自动故障转移
    
    证书：阿里云 ACE 认证、PMP 项目管理认证
    """

    rr = RagResume()
    n = rr.import_resume(sample_resume, resume_id="zhangsan", metadata={"name": "张三"})
    print(f"已导入 {n} 个片段")

    summary = rr.summarize("zhangsan", target_length="200字以内")
    print("\n=== 浓缩简历 ===")
    print(summary)
