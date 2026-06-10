# src/jobsearch_mcp_server/tools/job.py
"""
岗位工具模块：提供岗位爬取、智能匹配等功能
"""
from ..llm.llm import send_messages
from ..prompt.prompt import JOB_SEARCH_PROMPT
from ..crawler import fetch_51job, format_jobs_text, CITY_CODES


class JobTools:
    def __init__(self, logger=None):
        self.logger = logger

    def register_tools(self, mcp):
        @mcp.tool()
        def crawl_jobs(
            keyword: str = "AI应用开发",
            city: str = "上海",
            max_pages: int = 2
        ) -> str:
            """
            从前程无忧(51job)实时爬取职位数据，返回格式化的岗位列表

            参数:
                keyword:  搜索关键词（如 "AI应用开发"、"Python后端"、"Java开发"）
                city:     城市名称（如 "上海"、"成都"、"北京"、"广州"、"深圳"、"杭州"）
                max_pages: 抓取页数，默认 2 页，最多 5 页

            返回:
                格式化的岗位列表文本，包含公司名称、薪资、地点等信息
            """
            try:
                if city not in CITY_CODES:
                    available = "、".join(CITY_CODES.keys())
                    return f"❌ 不支持的城市 '{city}'，可选：{available}"

                if max_pages > 5:
                    max_pages = 5

                jobs = fetch_51job(
                    keyword=keyword,
                    city=city,
                    max_pages=max_pages,
                    headless=True,
                )

                if not jobs:
                    return f"⚠️ 未找到 '{keyword}' 在 '{city}' 的职位数据，请尝试其他关键词或城市。"

                text = format_jobs_text(jobs)
                return f"✅ 共找到 {len(jobs)} 个 '{keyword}' 相关职位（{city}）：\n\n{text}"
            except Exception as e:
                return f"❌ 爬取失败：{str(e)}"

        @mcp.tool()
        def get_joblist_by_expect_job(job: str) -> str:
            """
            根据求职者的期望岗位，从本地已保存的数据文件中获取岗位列表

            参数:
                job: 期望的岗位名称（如 "Python后端开发"、"AI应用开发"）

            返回:
                岗位列表文本，包含公司名称、薪资、岗位要求等信息
            """
            try:
                with open('job.txt', 'r', encoding='utf-8') as f:
                    jobs = f.read()
                return jobs
            except FileNotFoundError:
                return "岗位数据文件未找到，请先使用 crawl_jobs 工具爬取最新数据。"

        @mcp.tool()
        def get_job_by_resume(jobs: str, resume: str) -> str:
            """
            根据求职者的简历和岗位列表，由 AI 猎头顾问智能匹配最合适的岗位并给出专业求职建议

            参数:
                jobs:   岗位列表文本（来自 crawl_jobs 或 get_joblist_by_expect_job 的输出）
                resume: 求职者的简历文本

            返回:
                匹配结果，包含：
                - 最匹配的 3 个岗位及匹配度分析
                - 每个岗位的竞争力评估
                - 简历优化建议和面试准备方向
                - 综合求职策略建议
            """
            prompt = JOB_SEARCH_PROMPT.format(resume=resume, job_list=jobs)
            messages = [{"role": "user", "content": prompt}]
            try:
                reply = send_messages(messages)
                return reply
            except Exception as e:
                return f"岗位匹配失败：{str(e)}"
