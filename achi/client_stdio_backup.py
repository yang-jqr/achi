import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def run():
    # 配置服务器启动参数
    server_params = StdioServerParameters(
        command="uv",
        args=[
            "run",
            "--with", "mcp[cli]",
            "--directory", "C:/Users/rog/Desktop/achievement",
            "mcp", "run", "server.py"
        ]
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            # 初始化连接
            await session.initialize()

            # 列出可用工具
            tools = await session.list_tools()
            print("Tools:", tools)

            # 调用工具
            result = await session.call_tool("get_score_by_name", arguments={"name": "张三"})
            print("Tool call result:", result)

            # 列出可用资源
            resources = await session.list_resources()
            print("Resources:", resources)

            # 读取资源
            content, mime_type = await session.read_resource("file:///info.md")
            print("Resource content:", content)
            print("MIME type:", mime_type)

            # 列出可用提示词
            prompts = await session.list_prompts()
            print("Prompts:", prompts)

            # 获取提示词
            prompt = await session.get_prompt("prompt", arguments={"name": "张三"})
            print("Prompt:", prompt)

if __name__ == "__main__":
    asyncio.run(run())