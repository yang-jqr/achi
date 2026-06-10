# server_sse.py
"""
Achievement - AI 求职助手 MCP Server
======================================
基于 MCP (Model Context Protocol) 的求职辅助工具，通过 SSE 协议提供服务。

功能：
1. RAG 简历浓缩 - 使用向量数据库对简历进行检索增强生成，快速生成简历摘要
2. AI 简历优化 - 根据目标岗位描述（JD）优化简历，生成可直接投递的专业简历
3. 岗位智能匹配 - 根据简历和岗位列表，由 AI 猎头顾问匹配最合适的岗位
4. 简历文件解析 - 支持上传 PDF/Word 格式的简历文件，自动提取文本内容
5. 投递历史跟踪 - 记录和管理求职投递历史
"""
import uvicorn
from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware
from starlette.routing import Mount, Route
from mcp.server.fastmcp import FastMCP
from mcp.server.transport_security import TransportSecuritySettings
from src.jobsearch_mcp_server.resume_tools.rag_resume import RagResume
from src.jobsearch_mcp_server.resume_tools.resume_enhancer import ResumeEnhancer
from src.jobsearch_mcp_server.resume_tools.resume_parser import ResumeParser
from src.jobsearch_mcp_server.tracker import JobTracker
from src.jobsearch_mcp_server.crawler import fetch_51job, format_jobs_text, CITY_CODES
from src.jobsearch_mcp_server.llm.llm import send_messages
from src.jobsearch_mcp_server.prompt.prompt import JOB_SEARCH_PROMPT

# 允许 file:// 协议（本地 HTML 文件）和 null Origin（某些浏览器/场景）
mcp = FastMCP(
    "Achievement - AI 求职助手",
    transport_security=TransportSecuritySettings(
        enable_dns_rebinding_protection=True,
        allowed_hosts=["127.0.0.1:*", "localhost:*", "[::1]:*"],
        allowed_origins=[
            "http://127.0.0.1:*",
            "http://localhost:*",
            "http://[::1]:*",
            "null",  # 允许 file:// 协议访问（浏览器发送 Origin: null）
        ],
    ),
)


# ============================================================
#  功能一：RAG 简历浓缩
#  用途：将简历导入向量数据库，通过 RAG 技术快速生成浓缩版简历摘要
# ============================================================
_rag = RagResume()

@mcp.tool()
def import_resume_to_vector_db(
    resume_text: str,
    resume_id: str = "",
    name: str = "",
    chunk_size: int = 500,
    chunk_overlap: int = 50
) -> str:
    """
    将简历文本分块后导入向量数据库（Qdrant），用于后续 RAG 检索和简历浓缩

    参数:
        resume_text:   简历全文文本
        resume_id:     简历唯一标识（如姓名拼音），不传则自动生成
        name:          姓名（可选，用于元数据标记）
        chunk_size:    分块大小（字符数），默认 500
        chunk_overlap: 块间重叠字符数，默认 50

    返回:
        导入结果信息，包含生成的 resume_id 和导入的块数
    """
    # 如果 resume_id 为空字符串，传 None 让底层自动生成
    rid = resume_id if resume_id else None
    metadata = {"name": name} if name else {}
    n_chunks = _rag.import_resume(resume_text, rid, metadata, chunk_size, chunk_overlap)
    # import_resume 返回 int（块数），需要格式化为字符串
    return f"简历导入成功！共导入 {n_chunks} 个片段，resume_id: {rid or '(自动生成)'}"


@mcp.tool()
def rag_summarize_resume(resume_id: str, max_length: int = 500) -> str:
    """
    基于 RAG（检索增强生成）技术，从向量数据库中检索简历关键信息并生成浓缩摘要

    参数:
        resume_id: 简历唯一标识（导入时返回的 resume_id）
        max_length: 摘要最大长度（字符数），默认 500

    返回:
        浓缩后的简历摘要文本
    """
    return _rag.summarize(resume_id, max_length)


@mcp.tool()
def search_similar_resumes(query: str = "", top_k: int = 10) -> str:
    """
    列出向量数据库中所有已导入的简历

    参数:
        query: 搜索查询文本（保留参数以兼容前端调用，实际使用 list_resumes）
        top_k: 返回数量上限，默认 10

    返回:
        已导入的简历列表
    """
    resumes = _rag.list_resumes()
    if not resumes:
        return "向量数据库中暂无简历数据。"
    lines = [f"共 {len(resumes)} 份简历：", ""]
    for i, r in enumerate(resumes[:top_k], 1):
        lines.append(f"{i}. resume_id: {r.get('resume_id', 'N/A')}")
        lines.append(f"   姓名: {r.get('name', '未命名')}")
        lines.append(f"   来源: {r.get('source', '未知')}")
        lines.append(f"   片段数: {r.get('chunks', 0)}")
        lines.append("")
    return "\n".join(lines)


# ============================================================
#  功能二：AI 简历优化
#  用途：根据目标岗位描述（JD）优化简历，或按模板生成简历
# ============================================================
_enhancer = ResumeEnhancer()

@mcp.tool()
def enhance_resume_by_jd(resume_text: str, jd_text: str) -> str:
    """
    根据目标岗位描述（JD）优化简历，使简历更贴合岗位要求

    参数:
        resume_text: 原始简历文本
        jd_text:     目标岗位描述（JD）文本

    返回:
        优化后的简历文本
    """
    return _enhancer.enhance_by_jd(resume_text, jd_text)


@mcp.tool()
def enhance_resume_by_template(
    resume_text: str,
    template: str = "standard",
    target_position: str = "",
) -> str:
    """
    按指定模板风格重新排版和润色简历

    参数:
        resume_text:     原始简历文本
        template:        模板类型，可选值：standard（标准）, technical（技术）, concise（简洁）
        target_position: 目标岗位名称（可选，用于针对性优化）

    返回:
        按模板生成的简历文本
    """
    return _enhancer.enhance_by_template(resume_text, template, target_position)


# ============================================================
#  功能三：岗位智能匹配
#  用途：根据简历和岗位列表，由 AI 猎头顾问匹配最合适的岗位
# ============================================================

@mcp.tool()
def crawl_jobs(keyword: str = "AI应用开发", city: str = "上海", max_pages: int = 2) -> str:
    """
    从 51job 招聘网站爬取岗位信息

    参数:
        keyword:   搜索关键词，如 "AI应用开发"、"Python后端" 等
        city:      城市名称，可选值：上海、北京、广州、深圳、杭州、成都、武汉、南京、全国
        max_pages: 爬取页数（1~5页），默认 2 页

    返回:
        爬取到的岗位列表文本
    """
    # 校验城市
    city_code = CITY_CODES.get(city)
    if not city_code:
        return f"[失败] 不支持的城市：{city}。可选城市：{', '.join(CITY_CODES.keys())}"

    # 限制页数
    max_pages = min(max_pages, 5)

    try:
        jobs = fetch_51job(keyword, city, max_pages)
        if not jobs:
            return f"未找到关键词「{keyword}」在 {city} 的岗位信息。"
        return format_jobs_text(jobs)
    except Exception as e:
        err_msg = str(e)
        # 替换无法用 GBK 编码的字符（Windows 终端兼容）
        try:
            err_msg.encode('gbk')
        except UnicodeEncodeError:
            err_msg = err_msg.encode('gbk', errors='replace').decode('gbk')
        return f"[失败] 爬取失败：{err_msg}"


@mcp.tool()
def get_job_by_resume(jobs: str, resume: str) -> str:
    """
    根据简历内容，从岗位列表中智能匹配最合适的岗位

    参数:
        jobs:   岗位列表文本（通常由 crawl_jobs 工具返回）
        resume: 简历文本

    返回:
        AI 猎头顾问的岗位匹配分析结果
    """
    prompt = JOB_SEARCH_PROMPT.format(resume=resume, jobs=jobs)
    return send_messages([{"role": "user", "content": prompt}])


# ============================================================
#  功能四：简历文件解析
#  用途：支持上传 PDF/Word 格式的简历文件，自动提取文本内容
# ============================================================
_parser = ResumeParser()

@mcp.tool()
def parse_resume_file(file_path: str) -> str:
    """
    解析简历文件（支持 PDF、DOCX 格式），提取文本内容

    参数:
        file_path: 简历文件的完整路径

    返回:
        提取到的简历文本内容
    """
    return _parser.parse(file_path)


# ============================================================
#  功能五：投递历史跟踪
#  用途：记录和管理求职投递历史
# ============================================================
_tracker = JobTracker()

@mcp.tool()
def add_job_record(
    company: str,
    position: str,
    status: str = "已投递",
    salary: str = "",
    location: str = "",
    job_url: str = "",
    note: str = "",
) -> str:
    """
    添加一条投递记录

    参数:
        company:  公司名称
        position: 岗位名称
        status:   投递状态，可选值：已投递、简历筛选、面试中、Offer、不合适、已入职
        salary:   薪资范围（可选）
        location: 工作地点（可选）
        job_url:  岗位链接（可选）
        note:     备注（可选）

    返回:
        添加结果信息
    """
    try:
        record_id = _tracker.add_application(
            company_name=company,
            job_title=position,
            salary_range=salary,
            location=location,
            notes=note,
        )
        return f"✅ 投递记录已添加（ID: {record_id}）\n公司：{company}\n岗位：{position}\n状态：{status}"
    except Exception as e:
        return f"❌ 添加失败：{e}"


@mcp.tool()
def list_job_records(status: str = "", page: int = 1, page_size: int = 20) -> str:
    """
    查询投递记录列表

    参数:
        status:   筛选状态（可选），不传则查询全部
        page:     页码，从 1 开始，默认 1
        page_size: 每页条数，默认 20

    返回:
        投递记录列表文本
    """
    try:
        status_param = status if status else None
        offset = (page - 1) * page_size
        records = _tracker.list_applications(status=status_param, limit=page_size, offset=offset)
        if not records:
            return "暂无投递记录"
        lines = [f"{'ID':<4} {'公司':<12} {'岗位':<20} {'状态':<8} {'时间':<20}"]
        lines.append("-" * 70)
        for r in records:
            lines.append(
                f"{r['id']:<4} {r['company_name']:<12} {r['job_title']:<20} "
                f"{r['status']:<8} {r['applied_at']:<20}"
            )
        return "\n".join(lines)
    except Exception as e:
        return f"❌ 查询失败：{e}"


@mcp.tool()
def update_job_record(record_id: int, status: str = "", note: str = "") -> str:
    """
    更新投递记录信息

    参数:
        record_id: 记录 ID
        status:    新状态（可选），可选值：已投递、已查看、面试中、已拒绝、已录用
        note:      新备注（可选）

    返回:
        更新结果信息
    """
    try:
        updated = False
        if status:
            if _tracker.update_status(record_id, status):
                updated = True
        if note:
            if _tracker.update_notes(record_id, note):
                updated = True
        if updated:
            return f"✅ 记录 {record_id} 已更新"
        return "⚠️ 未提供需要更新的字段"
    except Exception as e:
        return f"❌ 更新失败：{e}"


@mcp.tool()
def delete_job_record(record_id: int) -> str:
    """
    删除一条投递记录

    参数:
        record_id: 要删除的记录 ID

    返回:
        删除结果信息
    """
    try:
        if _tracker.delete_application(record_id):
            return f"✅ 记录 {record_id} 已删除"
        return f"❌ 未找到记录 {record_id}"
    except Exception as e:
        return f"❌ 删除失败：{e}"


@mcp.tool()
def get_job_stats() -> str:
    """
    获取投递统计概览

    返回:
        投递统计信息，包含总投递数、各状态数量等
    """
    try:
        stats = _tracker.get_statistics()
        total = stats.get("total", 0)
        recent = stats.get("recent_week", 0)
        status_counts = stats.get("status_counts", {})
        interview = status_counts.get("面试中", 0)
        offer = status_counts.get("已录用", 0)
        return (
            f"📊 投递统计\n"
            f"{'='*30}\n"
            f"总投递数：{total}\n"
            f"近7天：{recent}\n"
            f"面试中：{interview}\n"
            f"已录用：{offer}\n"
            f"{'='*30}"
        )
    except Exception as e:
        return f"❌ 获取统计失败：{e}"


# ============================================================
#  启动服务器（手动创建 Starlette 应用以添加 CORS 支持）
# ============================================================
if __name__ == "__main__":
    # 获取 FastMCP 的 SSE Starlette 应用
    sse_app = mcp.sse_app()

    # 创建自定义 Starlette 应用，包装 SSE 应用并添加 CORS 中间件
    # 允许 Origin: null（file:// 协议）和本地开发地址
    cors_app = Starlette(
        routes=[
            Mount("/", app=sse_app),
        ],
        middleware=[
            Middleware(
                CORSMiddleware,
                allow_origins=[
                    "http://127.0.0.1:*",
                    "http://localhost:*",
                    "http://[::1]:*",
                    "null",  # 允许 file:// 协议
                ],
                allow_credentials=True,
                allow_methods=["*"],
                allow_headers=["*"],
            ),
        ],
    )

    uvicorn.run(cors_app, host="127.0.0.1", port=8000, log_level="info")
