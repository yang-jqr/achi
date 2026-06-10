# Qdrant 向量数据库搭建与简历优化完整教程

> 基于 `e:\achi\` 项目的实战指南，涵盖从零搭建 Qdrant、导入简历文档、向量化存储到 RAG 简历优化的全流程。

---

## 目录

0. [核心概念入门](#0-核心概念入门)
1. [项目概述与架构](#1-项目概述与架构)
2. [环境准备与依赖安装](#2-环境准备与依赖安装)
3. [Qdrant 向量数据库搭建](#3-qdrant-向量数据库搭建)
4. [简历 Word 文档导入](#4-简历-word-文档导入)
5. [量化/向量数据导入流程](#5-量化向量数据导入流程)
6. [基于 RAG 的简历优化实现](#6-基于-rag-的简历优化实现)
7. [常见问题排查](#7-常见问题排查)

---

## 0. 核心概念入门

> 在动手实践之前，先理解本教程涉及的 **6 个核心概念**。这些概念构成了整个系统的理论基础。

### 0.1 什么是向量数据库 (Vector Database)

#### 传统数据库 vs 向量数据库

```
┌─────────────────────────────────────────────────────────────────────┐
│                      传统关系型数据库 (MySQL)                        │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│   查询方式：精确匹配                                                 │
│                                                                     │
│   SELECT * FROM resumes WHERE skill = 'Python';                     │
│                                                                     │
│   ❌ 只能匹配完全相同的值                                            │
│   ❌ 无法理解 "Python" 和 "编程语言" 的语义关联                       │
│   ❌ 无法按"相似程度"排序                                             │
│                                                                     │
│   数据示例：                                                         │
│   ┌──────┬─────────────┬────────────┐                               │
│   │  id  │    name     │   skill    │                               │
│   ├──────┼─────────────┼────────────┤                               │
│   │   1  │    张三      │   Python   │                               │
│   │   2  │    李四      │   Java     │                               │
│   └──────┴─────────────┴────────────┘                               │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘

                              vs

┌─────────────────────────────────────────────────────────────────────┐
│                        向量数据库 (Qdrant)                           │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│   查询方式：语义相似度搜索                                           │
│                                                                     │
│   Query: "熟悉深度学习框架"                                          │
│                                                                     │
│   ✅ 能找到包含 "PyTorch"、"TensorFlow" 的记录                       │
│   ✅ 理解语义关联，而非字面匹配                                       │
│   ✅ 按相关度排序返回结果                                             │
│                                                                     │
│   数据示例：                                                         │
│   ┌──────┬──────────────────────────────────────────┬────────────┐  │
│   │  id  │              vector (768维浮点数)          │   payload  │  │
│   ├──────┼──────────────────────────────────────────┼────────────┤  │
│   │   1  │ [0.12, -0.56, 0.90, ..., 0.34]           │ "熟练Python"│  │
│   │   2  │ [-0.23, 0.67, -0.12, ..., 0.78]          | "精通PyTorch"│  │
│   └──────┴──────────────────────────────────────────┴────────────┘  │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

#### 一句话总结

> **向量数据库** 是一种专门用于存储和检索 **高维向量** 的数据库系统。它不存文字本身，而是存文字的**数学表示（向量）**，并通过计算向量之间的**距离/相似度**来实现"语义搜索"——即根据**含义**而非**关键词**来查找信息。

#### 为什么需要向量数据库？

| 场景 | 传统数据库 | 向量数据库 |
|------|-----------|-----------|
| 查询 `name = '张三'` | ✅ 完美胜任 | ❌ 杀鸡用牛刀 |
| 搜索包含 "机器学习" 的文档 | ⚠️ 只能用 LIKE 模糊匹配 | ✅ 语义理解，找到 "深度学习"、"神经网络" 等 |
| 找出与岗位 JD 最匹配的简历 | ❌ 无法做到 | ✅ 相似度排序，Top-K 返回 |
| 推荐"你可能喜欢的内容" | ❌ 需要复杂的协同过滤 | ✅ 向量相似度即可实现 |

#### 主流向量数据库对比

| 数据库 | 特点 | 适用场景 |
|--------|------|---------|
| **Qdrant** (本项目使用) | Rust 编写，高性能，支持本地文件模式 | 中小规模项目、本地开发 |
| Milvus | 分布式架构，云原生 | 大规模生产环境 |
| Pinecone | 全托管云服务 | 快速原型开发 |
| Weaviate | 内置向量化管道 | 需要一体化解决方案 |
| Chroma | 轻量级，嵌入式 | 个人项目/Jupyter Notebook |

---

### 0.2 什么是 Embedding（词嵌入/向量化）

#### 核心思想：把文字变成数字

计算机无法直接理解"苹果"和"水果"的关系，但可以计算两个数字向量的距离。

```
┌─────────────────────────────────────────────────────────────────┐
│                    Embedding 的本质                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   文本 (人类可读)                    向量 (机器可计算)            │
│   ════════════                     ══════════════════           │
│                                                                 │
│   "Python编程"     ──▶   [ 0.52, -0.31,  0.87, ...,  0.15]     │
│   "Java开发"       ──▶   [ 0.48, -0.28,  0.82, ...,  0.21]     │
│   "炸鸡啤酒"       ──▶   [-0.71,  0.65, -0.33, ..., -0.88]     │
│                                                                 │
│   🔍 观察：                                                          │
│   · "Python编程" 和 "Java开发" 的向量很接近（都是编程语言话题）        │
│   · "炸鸡啤酒" 与前两者距离很远（完全不同领域）                         │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

#### Embedding 模型是如何工作的？

Embedding 模型（如本项目使用的 BGE-base-zh-v1.5）是一个经过大规模文本训练的 **深度神经网络（Transformer）**：

```
输入文本: "熟悉 Python 和深度学习"
         │
         ▼
┌─────────────────────────────────────────┐
│  Tokenization (分词)                     │
│  "熟悉", "Python", "和", "深度", "学习"   │
└─────────────────┬───────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────┐
│  Transformer Encoder (BERT架构)          │
│                                         │
│   ┌───┐ ┌───┐ ┌───┐ ┌───┐ ┌───┐       │
│   │ 熟 │ │Pyt │ │ 和 │ │深  │ │学  │ ...  │
│   │ 悉 │ │hon │ │ 度 │ │度  │ │习  │       │
│   └─┬─┘ └─┬─┘ └─┬─┘ └─┬─┘ └─┬─┘       │
│     │     │     │     │     │            │
│     └─────┴─────┴─────┴─────┘            │
│                 │                        │
│                 ▼                        │
│         [CLS] Token 输出                  │
│        (聚合全文语义)                      │
└─────────────────┬───────────────────────┘
                  │
                  ▼
        输出: [0.123, -0.456, 0.789, ..., 0.321]
              ← 768 个浮点数的向量 →
```

#### 关键属性

| 属性 | 本项目的值 | 含义 |
|------|-----------|------|
| **维度** | 768 | 向量的长度，决定表达能力。越高越精细，但计算和存储成本也更高 |
| **归一化** | L2 Normalize | 将向量映射到单位球面上，使余弦相似度等价于点积运算 |
| **语义聚类** | 自动形成 | 相似含义的文本在向量空间中自然聚集在一起 |

#### 直观理解：向量空间中的语义关系

```
                    食物
                      ↑
                      │
           苹果 ○─────┼─────○ 香蕉
                \     |     /
                 \    |    /
                  \   |   /
                   \  |  /
                    \ | /
                     ↓↓
                   ○ 水果
                     
    ↑ "苹果" + "香蕉" 的向量平均 ≈ "水果" 的向量位置
    （这就是 Embedding 的神奇之处！它捕捉了语言中的语义关系）


                    技术
                      ↑
                      │
           Python ○──┼───○ Java
                \    |    /
                 \   |   /
                  \  |  /
                   \ | /
                    ↓↓
                  ○ 编程语言
```

---

### 0.3 什么是 RAG（检索增强生成）

#### 问题背景：LLM 的局限性

大语言模型（如 DeepSeek、ChatGPT）虽然强大，但有明显的短板：

```
❌ LLM 不知道你的私人数据
   用户: "根据我的简历优化一下"
   LLM: "我没有您的简历信息，无法操作"

❌ LLM 可能产生幻觉（一本正经地胡说八道）
   用户: "我的简历里有哪些项目？"
   LLM: "您有 A、B、C 项目..."  ← 可能是编造的！

❌ LLM 的知识有截止日期
   训练数据截止后的事件一无所知
```

#### RAG 的解决方案

**RAG = Retrieval（检索）+ Augmentation（增强）+ Generation（生成）**

```
┌─────────────────────────────────────────────────────────────────┐
│                    没有 RAG 的 LLM                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   用户提问 ──▶ LLM 凭「训练记忆」回答                            │
│               │                                                 │
│               ├─→ 可能不知道答案                                │
│               ├─→ 可能编造答案                                  │
│               └→ 信息可能过时                                   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘


┌─────────────────────────────────────────────────────────────────┐
│                    有 RAG 的 LLM                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   用户提问                                                      │
│     │                                                           │
│     ├──▶ ① 从知识库中【检索】相关资料  ◀── 向量数据库发挥作用     │
│     │        ("找到了3段相关的简历内容")                          │
│     │                                                           │
│     ├──▶ ② 将资料【增强】到 Prompt 中                           │
│     │        ("以下是参考信息：{简历片段}")                       │
│     │                                                           │
│     └──▶ ③ LLM 基于资料【生成】回答                             │
│              ("根据您的简历，建议...")  ← 有据可依，不会瞎编       │
│                                                                 │
│   ✅ 回答基于真实数据          ✅ 可以处理私有数据                │
│   ✅ 信息来源可追溯           ✅ 减少幻觉问题                    │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

#### 类比理解

> **没有 RAG 的 LLM** = 一个博学但**闭门不出**的学者，只靠记忆答题
>
> **有 RAG 的 LLM** = 同一个学者，但允许他**查阅参考资料**后再作答

在本项目中：
- **知识库** = 存储在 Qdrant 中的简历向量
- **检索过程** = 用岗位 JD 在 Qdrant 中搜索最相关的简历片段
- **增强过程** = 把检索到的简历片段塞进 Prompt 里
- **生成过程** = DeepSeek-R1 基于真实简历内容输出优化建议

---

### 0.4 什么是文本分块 (Text Chunking / Splitting)

#### 为什么需要分块？

```
问题：LLM 和 Embedding 模型都有长度限制

一份完整的简历可能有 2000+ 字符：
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
张三，某大学计算机科学与技术专业2022届本科毕业生...
主修课程：数据结构、算法分析、操作系统...
实习经历：ABC公司后端开发实习生(2023.07-2023.10)...
项目经历：(详细描述 500 字)...
技能证书：Python, Java, SQL, CET-6...
校园活动：计算机协会技术部长...
获奖情况：校级奖学金、ACM竞赛银牌...
自我评价：（200 字）...
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 2500字符

如果整个塞进去：
· Embedding 效果差（太长的文本，语义会模糊）
· 检索精度低（返回一大坨，大部分无关）
· Token 成本高（LLM 处理长文本更贵）

解决方案：拆成小块！
```

#### 分块的策略

```
原始简历 (2500字符)
        │
        ▼  RecursiveCharacterTextSplitter
        │  chunk_size=300, chunk_overlap=50
        │
   ┌────┴────┬────┴────┬────┴────┬────┴────┬────┴────┬
   ▼         ▼         ▼         ▼         ▼         ▼
┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐
│Chunk0│ │Chunk1│ │Chunk2│ │Chunk3│ │Chunk4│ │Chunk5│
│基本信息│ │主修课│ │实习经│ │项目1 │ │项目2 │ │技能自│
│ 300字│ │ 250字│ │ 280字│ │ 290字│ │ 270字│ │ 310字│
└──┬───┘ └──┬───┘ └──┬───┘ └──┬───┘ └──┬───┘ └──┬───┘
   │        │        │        │        │        │
   ▼        ▼        ▼        ▼        ▼        ▼
 [向量0]   [向量1]   [向量2]   [向量3]   [向量4]   [向量5]
   768维    768维    768维    768维    768维    768维
```

#### overlap（重叠）的作用

```
无 overlap (chunk_overlap=0):          有 overlap (chunk_overlap=50):
┌─────────┐ ┌─────────┐                ┌─────────┬──┐
│ Chunk A  │ │ Chunk B │                │ Chunk A  │ov│
│ "abcde"  │ "fghij"  │                │ "abcde"  │er│
└─────────┘ └─────────┘                └─────────┬──┘
                                              │  ┌──┬─────────┐
         ⚠️ e/f 之间断裂！                    └─▶│ov│ Chunk B  │
            关键信息可能在边界丢失                 │er│ "defghij" │
                                               ┌──┴─────────┐
                                               │ Chunk C  │ov│
                                               │ "hijklm" │er│
                                               └─────────┬──┘
         ✅ 保持上下文连贯性，避免截断关键信息
```

---

### 0.5 什么是余弦相似度 (Cosine Similarity)

#### 核心概念：用角度衡量相似度

```
向量空间中的两段文本：

      ↑
      │    vector_A ("Python编程")
      │      ↗
      │     /
      │    /  θ = 10° → 余弦值 ≈ 0.98 → 非常相似 ✅
      │   /
      │  /
      │ /__________▶
      /
   vector_B ("Java开发")
   
   
      ↑
      │    vector_C ("Python编程")  
      │      │
      │      │
      │      │  θ = 85° → 余弦值 ≈ 0.09 → 很不相似 ❌
      │      │
      │      │
      │      │__________▶
      │
   vector_D ("今晚吃火锅")
```

#### 数学公式（了解即可）

$$
\text{Cosine Similarity} = \cos(\theta) = \frac{A \cdot B}{\|A\| \times \|B\|}
$$

| 值域 | 含义 | 解释 |
|------|------|------|
| **≈ 1.0** | 几乎相同 | 两个向量方向一致，语义高度相近 |
| **≈ 0.5** | 部分相关 | 有一定关联，但不强 |
| **≈ 0.0** | 完全无关 | 两个向量垂直（正交），毫无关联 |

#### 在本项目中的应用

当用户输入岗位 JD 时：
1. JD 被编码为查询向量 `query_vector`
2. Qdrant 计算 `query_vector` 与每个简历 chunk 向量的余弦相似度
3. 按相似度从高到低排序，返回 Top-K（默认 K=3）个最相关的片段

---

### 0.6 什么是 LLM（大语言模型）

#### 什么是 LLM？

> **Large Language Model（大型语言模型）** 是一种基于深度学习的 AI 模型，通过阅读海量文本学习语言规律，能够理解和生成人类语言。

#### 本项目使用的 LLM：DeepSeek-R1

```
┌─────────────────────────────────────────────────────────────┐
│                    DeepSeek-R1                              │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  开发商：DeepSeek（深度求索，中国 AI 公司）                    │
│  别名：deepseek-reasoner                                    │
│                                                             │
│  🧠 核心特点：                                                │
│  · 具有「思维链」推理能力——回答前会先"思考"                    │
│  · 输出中包含 ＜thinking＞...＜/thinking＞ 标签               │
│  · 适合复杂推理任务（如简历优化这种需要综合分析的活儿）          │
│                                                             │
│  🔗 接入方式：                                                │
│  · 兼容 OpenAI API 格式                                      │
│  · base_url: https://api.deepseek.com                        │
│  · 通过 LangChain 的 ChatOpenAI 类调用                        │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

#### LLM 在本项目中扮演的角色

```
┌──────────────────────────────────────────────────────────┐
│                   LLM 的角色分工                          │
├──────────────────────┬───────────────────────────────────┤
│        组件          │              角色                │
├──────────────────────┼───────────────────────────────────┤
│  BGE Embedding 模型   │ 将文本变成向量（理解语义）          │
│  Qdrant 向量数据库     │ 存储向量，做相似度搜索             │
│  DeepSeek-R1 (LLM)   │ 理解上下文，生成优化后的简历内容    │
└──────────────────────┴───────────────────────────────────┘

比喻：
· BGE = 图书馆管理员（帮你找到相关书籍）
· Qdrant = 书架（存放书籍的地方）
· DeepSeek-R1 = 资深顾问（读完资料后给你专业建议）
```

#### Temperature 参数

```python
ChatOpenAI(..., temperature=0.7)
```

| temperature 值 | 效果 | 适用场景 |
|----------------|------|---------|
| **0.0 - 0.3** | 输出确定性强，几乎每次都一样 | 事实性问答、代码生成 |
| **0.4 - 0.7** | 创造性与稳定性平衡（本项目取值） | 内容改写、文案优化 |
| **0.8 - 1.0+** | 输出随机性强，富有创意 | 创意写作、头脑风暴 |

---

### 0.7 概念全景图：各组件如何协作

```
┌─────────────────────────────────────────────────────────────────┐
│                    概念协作全景图                                │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────┐                                                    │
│  │ .docx   │  原始数据                                          │
│  │ 简历文件 │                                                    │
│  └────┬────┘                                                    │
│       │ 分块 (Chunking - §0.4)                                  │
│       ▼                                                         │
│  ┌─────────┐    ┌──────────────────┐                            │
│  │ 文本块   │───▶│ Embedding (§0.2) │                            │
│  │ Chunks  │    │ BGE 模型向量化     │                            │
│  └─────────┘    └────────┬─────────┘                            │
│                          │ 768维向量                              │
│                          ▼                                      │
│  ┌──────────────────────────────────────┐                        │
│  │  向量数据库 Qdrant (§0.1)            │                        │
│  │  存储向量 + 余弦相似度搜索 (§0.5)     │                        │
│  └──────────────────┬───────────────────┘                        │
│                     │ 检索 (Retrieval)                           │
│                     ▼                                            │
│  ┌──────────────────────────────────────┐                        │
│  │  RAG 流程 (§0.3)                     │                        │
│  │  检索 → 增强 Prompt → LLM 生成       │                        │
│  └──────────────────┬───────────────────┘                        │
│                     │                                            │
│                     ▼                                            │
│  ┌──────────────────────────────────────┐                        │
│  │  LLM DeepSeek-R1 (§0.6)             │                        │
│  │  推理 & 生成优化后的简历              │                        │
│  └──────────────────────────────────────┘                        │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 1. 项目概述与架构

### 1.1 技术栈

| 组件 | 技术选型 | 说明 |
|------|----------|------|
| 向量数据库 | **Qdrant** (本地模式) | 无需 Docker，基于文件系统持久化 |
| Embedding 模型 | **BAAI/bge-base-zh-v1.5** | 768 维中文向量模型 |
| 大语言模型 (LLM) | **DeepSeek-R1** (deepseek-reasoner) | 通过 OpenAI 兼容 API 调用 |
| 框架 | **LangChain** | 分块、向量存储、链编排 |

### 1.2 系统架构

```
┌─────────────────────────────────────────────────────────────┐
│                      简历优化系统架构                         │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│   ┌──────────┐    ┌──────────────┐    ┌────────────────┐   │
│   │  .docx   │───▶│ 文本分块器    │───▶│ BGE Embedding │   │
│   │ 简历文档  │    │(LangChain)   │    │ (768维向量)    │   │
│   └──────────┘    └──────────────┘    └───────┬────────┘   │
│                                               │             │
│                                               ▼             │
│                                        ┌─────────────┐     │
│                                        │   Qdrant    │     │
│                                        │ 向量数据库   │     │
│                                        └──────┬──────┘     │
│                                               │             │
│                    ┌──────────────────────────┤             │
│                    ▼                          ▼             │
│           ┌──────────────┐          ┌─────────────┐        │
│           │  语义检索     │          │  岗位 JD    │        │
│           │ (相似度Top-K)│          │ (job.txt)   │        │
│           └──────┬───────┘          └──────┬──────┘        │
│                  │                        │                │
│                  └──────────┬─────────────┘                │
│                             ▼                              │
│                   ┌──────────────────┐                     │
│                   │   Prompt 模板     │                     │
│                   │ (resume + input)  │                     │
│                   └────────┬─────────┘                     │
│                            ▼                               │
│                   ┌──────────────────┐                     │
│                   │   DeepSeek-R1    │                     │
│                   │  (推理生成优化)   │                     │
│                   └──────────────────┘                     │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 1.3 项目文件结构

```
e:\achi\
├── qdrant/
│   └── resume_importer.py      # 核心：简历向量化 & 导入 Qdrant
├── llm.py                      # LLM / Embedding 封装
├── prompt.py                   # Prompt 模板定义
├── writeresume.py              # 主程序：RAG 链路 & 简历优化
├── pyproject.toml              # 项目依赖
├── .env                        # API Key 配置
├── job.txt                     # 岗位 JD 输入
├── qdrant_resume_db/           # 自动生成的 Qdrant 数据库目录
│   ├── collection/
│   │   └── resume_collection/
│   └── meta.json
└── *.docx                      # 待导入的 Word 简历
```

---

## 2. 环境准备与依赖安装

### 2.1 Python 版本

推荐使用 **Python 3.10+**：

```bash
python --version
# Python 3.11.x 或更高
```

### 2.2 安装项目依赖

在项目根目录执行：

```bash
cd e:\achi
pip install -e .
```

或手动安装核心依赖：

```bash
pip install langchain langchain-community langchain-openai langchain-qdrant
pip install qdrant-client sentence-transformers python-docx unstructured
pip install openai python-dotenv
```

### 2.3 配置 API Key

编辑 `.env` 文件（位于项目根目录）：

```env
deepseek=sk-你的DeepSeek_API_Key
```

获取 DeepSeek API Key：访问 https://platform.deepseek.com/api_keys

### 2.4 HuggingFace 镜像配置（中国大陆用户）

由于网络原因，需设置 HF 镜像源以加速 BGE 模型下载。

**方法一：环境变量（推荐，已在代码中配置）**

在 `qdrant/resume_importer.py` 顶部已包含：

```python
import os
os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"
```

**方法二：命令行临时设置**

```powershell
$env:HF_ENDPOINT="https://hf-mirror.com"
```

---

## 3. Qdrant 向量数据库搭建

### 3.1 关于本项目使用的 Qdrant 模式

**本项目采用 Qdrant 本地文件模式**，无需 Docker 容器或远程服务器。Qdrant Client 会自动在本地创建文件型数据库，所有数据持久化到指定目录。

### 3.2 核心配置参数

来自 `qdrant/resume_importer.py`：

```python
# Qdrant 配置
QDRANT_PATH = "./qdrant_resume_db"       # 数据库存储路径
COLLECTION_NAME = "resume_collection"     # 集合名称

# Embedding 模型配置
EMBEDDING_MODEL = "BAAI/bge-base-zh-v1.5" # 中文优化模型，768维
```

### 3.3 初始化流程说明

当运行导入脚本时，以下步骤自动完成：

1. **初始化 Embedding 模型** → 自动从 HuggingFace 下载 BGE 模型（约 400MB）
2. **连接/创建 Qdrant Client** → 若路径不存在则自动创建
3. **创建 Collection** → 设置向量维度为 768，距离度量方式为余弦相似度
4. **写入文档向量** → 将分块后的文本向量化后批量存入

### 3.4 首次运行预期输出

首次执行时，会看到类似日志：

```
Downloading (…)lve/main/config.json: 100%|██████████| 645/645 [00:00<00:00, 1.25MB/s]
Downloading (…)model.safetensors: 100%|██████████| 438M/438M [01:23<00:00, 5.24MB/s]
```

这表示 BGE 模型正在下载，后续运行会使用缓存。

---

## 4. 简历 Word 文档导入

### 4.1 准备简历文件

将 `.docx` 格式的简历放置于项目目录下。默认读取的路径在 `qdrant/resume_importer.py` 中配置：

```python
RESUME_PATH = r"E:\achi\AI_intern_resume.docx"  # 修改为你的简历路径
```

### 4.2 导入脚本详解

`qdrant/resume_importer.py` 是核心导入脚本，包含以下关键函数：

#### (1) `read_docx()` — 读取 Word 文档

```python
from docx import Document

def read_docx(file_path: str) -> str:
    """读取 docx 文件并返回纯文本"""
    doc = Document(file_path)
    return "\n".join([para.text for para in doc.paragraphs])
```

#### (2) `split_text()` — 文本智能分块

```python
from langchain_text_splitters import RecursiveCharacterTextSplitter

def split_text(text: str):
    """使用 LangChain 进行文本分块"""
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=300,       # 每块最大字符数
        chunk_overlap=50,     # 块间重叠字符数
        separators=["\n\n", "\n", "。", "！", "？", ".", " ", ""]
    )
    return splitter.split_text(text)
```

**分块策略解读：**
- `chunk_size=300`：每块约 150 个中文字符（适合中文语义单元）
- `chunk_overlap=50`：保持上下文连贯性，避免截断关键信息
- `separators`：按段落 > 行 > 句号 > 空格优先级分割，确保语义完整

#### (3) `init_embedding()` — 初始化向量模型

```python
from langchain_huggingface import HuggingFaceEmbeddings

def init_embedding(model_name: str = EMBEDDING_MODEL):
    """初始化 HuggingFace Embedding 模型"""
    return HuggingFaceEmbeddings(
        model_name=model_name,
        model_kwargs={"device": "cpu"},  # 可改为 "cuda" 使用 GPU
        encode_kwargs={"normalize_embeddings": True}  # L2 归一化
    )
```

#### (4) `import_to_qdrant()` — 执行导入

```python
from langchain_qdrant import QdrantVectorStore

def import_to_qdrant(chunks: list[str], embedding, path: str, collection: str):
    """将文本块向量并导入 Qdrant"""
    store = QdrantVectorStore.from_texts(
        texts=chunks,
        embedding=embedding,
        path=path,
        collection_name=collection,
        distance="COSINE",  # 余弦距离
    )
    return store
```

### 4.3 执行导入

```bash
cd e:\achi
python qdrant/resume_importer.py
```

**预期成功输出：**

```
[INFO] 成功读取文档，共 1234 字符
[INFO] 分块完成，共生成 8 个文本块
[INFO] Qdrant 导入完成！集合名称: resume_collection
[INFO] 数据库路径: ./qdrant_resume_db
[INFO] 共导入 8 条向量记录
```

### 4.4 验证导入结果

检查 `qdrant_resume_db/` 目录是否生成：

```bash
dir qdrant_resume_db\collection\resume_collection\
```

应看到 segments 目录和元数据文件。

---

## 5. 量化/向量数据导入流程

### 5.1 完整数据流水线图

```
┌──────────┐    ┌──────────────┐    ┌────────────────┐    ┌──────────┐
│  .docx   │───▶│ read_docx()  │───▶│ split_text()   │───▶│ Text     │
│ 原始简历  │    │ 提取纯文本     │    │ 智能分8块       │    │ Chunks[] │
└──────────┘    └──────────────┘    └────────────────┘    └────┬─────┘
                                                            │
                                                     ┌──────▼──────┐
                                                     │  Chunk 示例  │
                                                     ├──────────────┤
                                                     │ Chunk #0:    │
                                                     │ "张三        │
                                                     │  某大学计算机 │
                                                     │  科学与技术   │
                                                     │  专业2022届..."│
                                                     │              │
                                                     │ Chunk #1:    │
                                                     │ "实习经历     │
                                                     │  ABC公司-后端 │
                                                     │  开发实习生   │
                                                     │  2023.07-"...│
                                                     └──────────────┘
                                                            │
                                                            ▼
┌───────────────────────────────────────────────────────────────────┐
│                       向量化过程                                   │
├───────────────────────────────────────────────────────────────────┤
│                                                                   │
│   Chunk #0 ("张三某大学...")                                       │
│       │                                                           │
│       ▼                                                           │
│   ┌─────────────────────┐                                         │
│   │  BGE-base-zh-v1.5   │                                         │
│   │  (Transformer编码器)  │                                         │
│   └──────────┬──────────┘                                         │
│              │                                                    │
│              ▼                                                    │
│   [0.1234, -0.5678, 0.9012, ..., 0.3456]  ← 768维浮点数向量      │
│                                                                   │
│   Chunk #1 ("实习经历ABC...")                                      │
│       │                                                           │
│       ▼                                                           │
│   [-0.2345, 0.6789, -0.1234, ..., 0.7890]  ← 768维浮点数向量      │
│                                                                   │
│   ...（每个Chunk都生成对应的768维向量）                              │
│                                                                   │
└───────────────────────────────────────────────────────────────────┘
                                                            │
                                                            ▼
┌───────────────────────────────────────────────────────────────────┐
│                       Qdrant 存储                                  │
├───────────────────────────────────────────────────────────────────┘
│                                                                    │
│  Collection: resume_collection                                     │
│  ├── Vector Dimension: 768                                         │
│  ├── Distance Metric: Cosine                                       │
│  └── Points:                                                       │
│      ├── Point ID: 1                                               │
│      │   ├── Vector: [0.12, -0.56, ...]                           │
│      │   └── Payload: {text: "张三某大学..."}                      │
│      ├── Point ID: 2                                               │
│      │   ├── Vector: [-0.23, 0.67, ...]                           │
│      │   └── Payload: {text: "实习经历ABC..."}                     │
│      └── ... (共 N 条记录)                                          │
│                                                                    │
└───────────────────────────────────────────────────────────────────┘
```

### 5.2 关键参数说明

| 参数 | 值 | 说明 |
|------|-----|------|
| 向量维度 | **768** | 由 BGE-base-zh-v1.5 模型决定 |
| 距离度量 | **Cosine** | 余弦相似度，适合文本语义匹配 |
| 归一化 | **L2 Normalize** | `encode_kwargs={"normalize_embeddings": True}` 使余弦距离等价于点积 |
| 存储模式 | **本地文件** | `path="./qdrant_resume_db"`，无需服务器 |

### 5.3 向量检索原理

当查询时，Query 文本同样被编码为 768 维向量，然后在 Qdrant 中进行 **ANN（近似最近邻）搜索**：

```
Query: "熟悉Python和机器学习"
         │
         ▼  BGE Encode
    [0.23, -0.45, 0.67, ...]  (768d Query Vector)
         │
         ▼  Cosine Similarity with all stored vectors
    ┌─────────────────────────────────┐
    │ Rank 1: Chunk #5 (0.89) ✓      │  ← 最相关
    │ Rank 2: Chunk #2 (0.76)        │
    │ Rank 3: Chunk #7 (0.71)        │
    │ ...                             │
    └─────────────────────────────────┘
```

---

## 6. 基于 RAG 的简历优化实现

### 6.1 RAG 工作流

```
┌─────────────────────────────────────────────────────────────────────┐
│                        RAG 简历优化工作流                            │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  Step 1: 输入                                                        │
│  ┌─────────────────┐    ┌──────────────────────────┐               │
│  │   用户输入岗位JD  │    │   已存储在 Qdrant 中的简历  │              │
│  │  "熟悉Python..." │    │   向量化 chunks            │              │
│  └────────┬────────┘    └────────────┬─────────────┘               │
│           │                          │                             │
│           ▼                          ▼                             │
│  Step 2: 检索 (Retrieval)                                         │
│  ┌────────────────────────────────────────────────────┐            │
│  │  Query Encoder (BGE)                                │            │
│  │       ↓                                             │            │
│  │  Qdrant ANN Search → Top-3 相关简历片段              │            │
│  └────────────────────┬───────────────────────────────┘            │
│                       │                                            │
│                       ▼                                            │
│  Step 3: 增强 (Augmentation)                                       │
│  ┌────────────────────────────────────────────────────┐            │
│  │  Prompt Template:                                   │            │
│  │  ┌──────────────────────────────────────────┐      │            │
│  │  │ 你是一个专业的简历优化助手...               │      │            │
│  │  │                                          │      │            │
│  │  │ 【候选人简历】:                           │      │            │
│  │  │ {resume}  ← 注入检索到的简历片段           │      │            │
│  │  │                                          │      │            │
│  │  │ 【目标岗位要求】:                         │      │            │
│  │  │ {input}   ← 注入用户的岗位JD              │      │            │
│  │  └──────────────────────────────────────────┘      │            │
│  └────────────────────┬───────────────────────────────┘            │
│                       │                                            │
│                       ▼                                            │
│  Step 4: 生成 (Generation)                                         │
│  ┌────────────────────────────────────────────────────┐            │
│  │  DeepSeek-R1 (deepseek-reasoner)                   │            │
│  │       ↓                                           │            │
│  │  思考链推理 → 结构化优化后的简历                     │            │
│  └────────────────────┬───────────────────────────────┘            │
│                       │                                            │
│                       ▼                                            │
│  Step 5: 输出                                                       │
│  ┌────────────────────────────────────────────────────┐            │
│  │  ✅ 优化后的简历内容（针对目标岗位定制）              │            │
│  └────────────────────────────────────────────────────┘            │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### 6.2 核心代码解析

#### `llm.py` — LLM 与 Embedding 工厂

```python
from langchain_openai import ChatOpenAI
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_qdrant import QdrantVectorStore
import os
from dotenv import load_dotenv

load_dotenv()

def DeepSeekR1():
    """返回 DeepSeek-R1 ChatOpenAI 实例"""
    return ChatOpenAI(
        model="deepseek-reasoner",
        api_key=os.getenv("deepseek"),
        base_url="https://api.deepseek.com",
        temperature=0.7,
    )

def TongyiEmbedding():
    """返回 HuggingFace BGE Embeddings"""
    os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"
    return HuggingFaceEmbeddings(
        model_name="BAAI/bge-base-zh-v1.5",
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": True}
    )

def QdrantVecStore():
    """连接已有 Qdrant 集合"""
    return QdrantVectorStore.from_existing_collection(
        embedding=TongyiEmbedding(),
        path="./qdrant_resume_db",
        collection_name="resume_collection"
    )
```

#### `prompt.py` — Prompt 模板

```python
from langchain_core.prompts import ChatPromptTemplate

ResumePrompt2 = ChatPromptTemplate.from_template("""
你是一个专业的简历优化助手。
根据【目标岗位要求】，对【候选人简历】进行针对性优化，
使简历更符合岗位需求，同时保持真实性。

【候选人简历】:
{resume}

【目标岗位要求】:
{input}

请输出优化后的完整简历：
""")
```

#### `writeresume.py` — 主程序（RAG 链路）

```python
from langchain_core.runnables import RunnablePassthrough
from langchain.output_parsers import StrOutputParser
from llm import DeepSeekR1, QdrantVecStore
from prompt import ResumePrompt2

def fix_resume(input_text: str):
    """
    构建 RAG Chain 并执行简历优化
    
    Args:
        input_text: 目标岗位 JD
        
    Returns:
        优化后的简历字符串
    """
    vectorstore = QdrantVecStore()
    retriever = vectorstore.as_retriever(search_kwargs={"k": 3})
    
    llm = DeepSeekR1()
    
    # LangChain LCEL Chain 编排
    chain = (
        {
            "resume": retriever,           # 从 Qdrant 检索相关简历片段
            "input": RunnablePassthrough()  # 直接传递用户输入
        }
        | ResumePrompt2                     # 注入 Prompt 模板
        | llm                               # 调用 DeepSeek-R1 推理
        | StrOutputParser()                 # 解析输出为字符串
    )
    
    return chain.invoke(input_text)

def load_jobs(path: str = "job.txt") -> str:
    """从 job.txt 读取岗位 JD"""
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

if __name__ == "__main__":
    jd = load_jobs()           # 加载岗位要求
    result = fix_resume(jd)    # 执行 RAG 优化
    print(result)              # 输出优化后的简历
```

### 6.3 使用示例

**(1) 准备岗位 JD**

编辑 `job.txt`：

```
岗位：AI 算法实习生
要求：
- 熟悉 Python，有 PyTorch/TensorFlow 使用经验
- 了解机器学习、深度学习基础算法
- 有 NLP 或 CV 相关项目经验者优先
- 良好的编程能力和数学基础
```

**(2) 运行简历优化**

```bash
cd e:\achi
python writeresume.py
```

**(3) 预期输出**

DeepSeek-R1 会先输出思考过程（`<think＞` 标签内），然后给出结构化的优化简历：

```
＜thinking＞
分析候选人与岗位的匹配度...
发现候选人有 PyTorch 项目经验但未突出展示...
建议增加量化成果描述...
＜/thinking＞

## 优化后的简历

### 基本信息
- 姓名：张三
- 学历：某大学 计算机科学与技术 2022届本科

### 项目经历（针对本岗位优化）
1. **基于 Transformer 的文本分类项目**
   - 使用 PyTorch 实现 BERT 微调，在中文情感数据集上达到 92% 准确率
   - 优化数据预处理流程，训练时间缩短 30%
   ...

### 优化建议总结
✅ 突出了 PyTorch 和深度学习相关技能
✅ 增加了可量化的项目成果
✅ 调整了技能排序，将岗位关键词前置
```

---

## 7. 常见问题排查

### 7.1 ModuleNotFoundError

**错误信息：**
```
ModuleNotFoundError: No module named 'langchain_huggingface'
```

**解决方案：**
```bash
pip install langchain-huggingface
```

### 7.2 API Key 缺失

**错误信息：**
```
ValueError: API key missing. Please set deepseek key in .env
```

**解决方案：**
检查 `.env` 文件是否存在且格式正确：
```env
deepseek=sk-your-actual-api-key-here
```

### 7.3 HuggingFace 模型下载慢/超时

**现象：**
下载 BGE 模型时速度极慢或连接超时。

**解决方案：**

确认镜像源设置（必须在 import 之前）：
```python
import os
os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"
```

或在系统中设置环境变量：
```powershell
# PowerShell（临时）
$env:HF_ENDPOINT="https://hf-mirror.com"

# 或永久设置（系统属性 → 环境变量）
```

### 7.4 Collection 已存在报错

**现象：**
第二次运行导入脚本时报错集合已存在。

**解决方案：**

方案 A：删除旧数据库重建
```bash
Remove-Item -Recurse -Force qdrant_resume_db
python qdrant/resume_importer.py
```

方案 B：修改代码支持追加导入（参考 `llm.py` 中的 `QdrantVecStore()` 方法）

### 7.5 向量维度不匹配

**错误信息：**
```
ValueError: Vector dimension mismatch. Expected 768, got 1024
```

**原因：** Embedding 模型与 Collection 创建时的维度不一致。

**解决：** 确保 `EMBEDDING_MODEL` 全程统一为 `BAAI/bge-base-zh-v1.5`（768 维），删除旧的 `qdrant_resume_db/` 目录后重新导入。

### 7.6 DeepSeek API 调用失败

**错误信息：**
```
openai.AuthenticationError: Incorrect API key provided
```

**检查清单：**
1. API Key 是否正确复制（无多余空格）
2. 账户是否有可用额度（新用户通常有免费额度）
3. `base_url` 是否正确：`https://api.deepseek.com`

---

## 附录：快速启动清单

- [ ] 安装 Python 3.10+
- [ ] 执行 `pip install -e .` 安装依赖
- [ ] 配置 `.env` 文件中的 DeepSeek API Key
- [ ] 准备 `.docx` 格式简历文件
- [ ] 修改 `qdrant/resume_importer.py` 中的 `RESUME_PATH` 指向简历文件
- [ ] 运行 `python qdrant/resume_importer.py` 导入简历到 Qdrant
- [ ] 编辑 `job.txt` 写入目标岗位 JD
- [ ] 运行 `python writeresume.py` 执行简历优化

---

> **文档版本**: v1.0  
> **更新日期**: 2026-05-25  
> **适用项目**: e:\achi\ (基于 LangChain + Qdrant + DeepSeek 的 RAG 简历优化系统)
