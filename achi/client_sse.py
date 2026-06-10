import asyncio
from mcp.client.sse import sse_client
from mcp import ClientSession

async def main():
    async with sse_client("http://127.0.0.1:8000/sse") as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.call_tool("get_score_by_name", arguments={"name": "张三"})
            print("工具调用结果：", result)

if __name__ == "__main__":
    asyncio.run(main())