from mcp.server.fastmcp import FastMCP

mcp = FastMCP("achievement")

@mcp.tool()
def get_score_by_name(name: str) -> str:
    """根据员工的姓名获取该员工的绩效得分"""
    if name == "张三":
        return "姓名：张三，绩效评分：85.9"
    elif name == "李四":
        return "姓名：李四，绩效评分：92.7"
    else:
        return f"未找到名为 '{name}' 的员工。"

@mcp.resource("file:///info.md")
def get_file() -> str:
    """返回员工信息文件的内容"""
    try:
        with open("C:/Users/rog/Desktop/achievement/info.md", "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return "错误：未找到 info.md 文件。"

@mcp.prompt()
def prompt(name: str) -> str:
    """创建一个prompt，用于对员工进行绩效评价"""
    return f"""绩效满分是100分，请获取{name}的绩效评分，并基于评分给出公正、具体的绩效评语。"""

if __name__ == "__main__":
    # 新版 FastMCP 的 Streamable HTTP 入口
    import uvicorn
    app = mcp.streamable_http_app()
    uvicorn.run(app, host="127.0.0.1", port=8000)