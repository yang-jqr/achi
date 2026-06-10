"""
Qdrant 向量数据库工具
支持：创建集合、插入向量、相似度搜索、删除集合
"""

from qdrant_client import QdrantClient
from qdrant_client.models import (
    PointStruct,
    VectorParams,
    Distance,
    Filter, FieldCondition, MatchValue
)
import os

# 数据存储路径（项目根目录下的 qdrant_data）
QDRANT_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "qdrant_resume_db")


class VectorDB:
    """Qdrant 向量数据库封装类"""

    def __init__(self, collection_name: str = "resume_db", vector_size: int = 1536):
        """
        初始化向量数据库
        
        Args:
            collection_name: 集合名称
            vector_size: 向量维度 (OpenAI=1536)
        """
        self.collection_name = collection_name
        self.vector_size = vector_size
        # 本地嵌入模式，数据持久化到磁盘
        self.client = QdrantClient(path=QDRANT_PATH)
        self._ensure_collection()

    def _ensure_collection(self):
        """确保集合存在，不存在则创建"""
        collections = [c.name for c in self.client.get_collections().collections]
        if self.collection_name not in collections:
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(
                    size=self.vector_size,
                    distance=Distance.COSINE  # 余弦相似度
                )
            )
            print(f"[VectorDB] 创建集合: {self.collection_name}, 维度: {self.vector_size}")
        else:
            print(f"[VectorDB] 连接到已有集合: {self.collection_name}")

    def insert(self, points: list[dict]):
        """
        插入数据点
        
        Args:
            points: 数据列表，每项格式：
                {
                    "id": int 或 str,        # 唯一ID
                    "vector": list[float],   # 向量
                    "payload": dict          # 附加数据 { "name": "xxx", "content": "xxx" }
                }
        """
        point_structs = [
            PointStruct(
                id=p["id"],
                vector=p["vector"],
                payload=p.get("payload", {})
            ) for p in points
        ]
        
        result = self.client.upsert(
            collection_name=self.collection_name,
            points=point_structs
        )
        print(f"[VectorDB] 成功插入 {len(points)} 条数据")
        return result

    def search(self, query_vector: list[float], limit: int = 5, 
               score_threshold: float = None) -> list[dict]:
        """
        相似度搜索
        
        Args:
            query_vector: 查询向量
            limit: 返回结果数量
            score_threshold: 相似度阈值 (0~1)，低于该值的结果将被过滤
            
        Returns:
            匹配结果列表，按相似度排序
        """
        kwargs = {
            "collection_name": self.collection_name,
            "query": query_vector,
            "limit": limit,
        }
        if score_threshold is not None:
            kwargs["score_threshold"] = score_threshold

        results = self.client.query_points(**kwargs).points

        return [
            {
                "id": hit.id,
                "score": hit.score,
                "payload": dict(hit.payload) if hit.payload else {}
            } for hit in results
        ]

    def search_by_field(self, query_vector: list[float], field: str, value, limit: int = 5):
        """带字段过滤的搜索"""
        results = self.client.query_points(
            collection_name=self.collection_name,
            query=query_vector,
            query_filter=Filter(
                must=[
                    FieldCondition(key=field, match=MatchValue(value=value))
                ]
            ),
            limit=limit
        ).points
        return [
            {"id": hit.id, "score": hit.score, "payload": dict(hit.payload) if hit.payload else {}}
            for hit in results
        ]

    def delete_by_ids(self, ids: list[int] | list[str]):
        """根据 ID 删除数据"""
        self.client.delete(
            collection_name=self.collection_name,
            points_selector=ids
        )
        print(f"[VectorDB] 删除 {len(ids)} 条数据")

    def delete_collection(self):
        """删除整个集合"""
        self.client.delete_collection(collection_name=self.collection_name)
        print(f"[VectorDB] 删除集合: {self.collection_name}")

    def get_count(self) -> int:
        """获取数据条数"""
        info = self.client.get_collection(collection_name=self.collection_name)
        return info.points_count

    def get_all(self, offset: int = 0, limit: int = 100) -> list:
        """获取所有数据"""
        results, _ = self.client.scroll(
            collection_name=self.collection_name,
            offset=offset,
            limit=limit
        )
        return [
            {"id": p.id, "payload": dict(p.payload) if p.payload else {}} for p in results
        ]


# ==================== 测试代码 ====================
if __name__ == "__main__":
    db = VectorDB(collection_name="test_collection", vector_size=4)
    
    print(f"\n当前数据量: {db.get_count()}")
    
    # 测试插入
    print("\n--- 插入测试 ---")
    test_points = [
        {"id": 1, "vector": [0.9, 0.8, 0.7, 0.6], "payload": {"name": "张三", "skill": "Python"}},
        {"id": 2, "vector": [0.3, 0.4, 0.5, 0.6], "payload": {"name": "李四", "skill": "Java"}},
        {"id": 3, "vector": [0.85, 0.75, 0.65, 0.55], "payload": {"name": "王五", "skill": "Python+AI"}},
    ]
    db.insert(test_points)
    
    # 测试搜索
    print("\n--- 搜索测试 ---")
    results = db.search(query_vector=[0.88, 0.78, 0.68, 0.58], limit=3)
    for r in results:
        print(f"  ID={r['id']}, 分数={r['score']:.4f}, 数据={r['payload']}")
    
    # 测试过滤搜索
    print("\n--- 过滤搜索 ---")
    filtered = db.search_by_field(query_vector=[0.5, 0.5, 0.5, 0.5], field="skill", value="Python")
    for r in filtered:
        print(f"  ID={r['id']}, 分数={r['score']:.4f}, 数据={r['payload']}")
    
    print(f"\n当前总数据量: {db.get_count()}")
