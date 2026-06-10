"""测试 MCP Server 的工具是否正常工作"""
import sys
sys.path.insert(0, "E:/achi")

from tools.job import JobTools
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("test")

def test():
    job_tools = JobTools(logger)

    # 模拟 MCP 工具调用
    print("=" * 50)
    print("测试 get_joblist_by_expect_job")
    print("=" * 50)

    result = job_tools.get_joblist_by_expect_job.__call__(job="AI应用开发")
    print(result[:500] if len(result) > 500 else result)  # 只打印前500字符

    print("\n" + "=" * 50)
    print("测试完成!")
    print("=" * 50)

if __name__ == "__main__":
    test()
