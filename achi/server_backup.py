# server.py
from mcp.server.fastmcp import FastMCP
from job_crawler_51job import fetch_jobs_from_51job
from openai import OpenAI
import os

deepseek_client = OpenAI(
    api_key=os.getenv("DEEPSEEK_API_KEY", "sk-3d1dff45edd44747816e505aff6601e7"),
    base_url="https://api.deepseek.com/v1"
)

mcp = FastMCP("achievement")

@mcp.tool()
def get_joblist_from_cache(job: str = "") -> str:
    """从本地缓存 job.txt 获取岗位列表（用于人岗匹配）"""
    try:
        with open("job.txt", "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return "错误：找不到 job.txt，请先运行爬虫或检查文件路径。"

# 提示词模板 (和书上 4.6 节一致)
JOB_SEARCH_PROMPT = """
【AI求职助手】
你是一个AI求职助手，我正在寻找与我的技能和经验相匹配的工作机会。以下是我的简历摘要和搜集到的岗位需求列表。

【个人简历】
{resume}

【岗位需求列表】
{job_list}

请帮我匹配最合适的 3 个岗位，并根据我的简历提供简要的求职建议。
"""

@mcp.tool()
def match_jobs_by_resume(resume: str) -> str:
    """根据求职者的简历，匹配最合适的3个岗位，并给出求职建议"""
    try:
        with open("job.txt", "r", encoding="utf-8") as f:
            jobs = f.read()
    except FileNotFoundError:
        return "错误：找不到 job.txt，请先运行爬虫。"

    prompt = JOB_SEARCH_PROMPT.format(resume=resume, job_list=jobs)
    messages = [{"role": "user", "content": prompt}]

    try:
        response = deepseek_client.chat.completions.create(
            model="deepseek-chat",
            messages=messages,
            temperature=0.7,
            max_tokens=2000
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"调用 DeepSeek 失败：{str(e)}"
# ---------- 员工绩效查询工具 ----------
@mcp.tool()
def get_score_by_name(name: str) -> str:
    """根据员工的姓名获取该员工的绩效得分"""
    if name == "张三":
        return "姓名: 张三, 绩效评分: 85.9"
    elif name == "李四":
        return "姓名: 李四, 绩效评分: 92.7"
    else:
        return f"未找到名为 '{name}' 的员工绩效信息。"

# ---------- 前程无忧职位爬取工具 ----------
@mcp.tool()
def search_jobs_51job(keyword: str = "AI应用开发", city: str = "上海", pages: int = 2) -> str:
    """
    使用无头浏览器从前程无忧抓取真实职位信息。
    参数：
    - keyword: 职位关键词，如 "Python开发"
    - city: 城市名称，支持 "上海"、"北京"、"广州"、"深圳"、"杭州"
    - pages: 爬取页数，建议 1~3 页
    """
    city_code_map = {
        "上海": "090200",
        "北京": "010000",
        "广州": "030200",
        "深圳": "040000",
        "杭州": "080200"
    }
    code = city_code_map.get(city, "090200")
    return fetch_jobs_from_51job(keyword, code, max_pages=pages)

# ---------- 资源与提示词（可选） ----------
@mcp.resource("file:///info.md")
def get_file() -> str:
    """返回员工信息文件的内容"""
    try:
        with open("info.md", "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return "错误：未找到 info.md 文件。"

@mcp.prompt()
def prompt(name: str) -> str:
    """创建一个 prompt，用于对员工进行绩效评价"""
    return f"""绩效满分是100分，请获取{name}的绩效评分，并基于评分给出公正、具体的绩效评语。"""

if __name__ == "__main__":
    mcp.run()
