# src/jobsearch_mcp_server/server.py
"""
JobSearch MCP Server - AI 求职助手核心服务
===========================================
基于 MCP (Model Context Protocol) 的求职辅助服务，
提供岗位匹配、简历优化等功能。
"""
import logging
import sys
from mcp.server.fastmcp import FastMCP

from .tools.job import JobTools


class JobSearchMCPServer:
    def __init__(self, host: str = "0.0.0.0", port: int = 8000):
        self.name = "jobsearch_mcp_server"

        # FastMCP 直接支持 host 和 port 参数
        self.mcp = FastMCP(
            self.name,
            host=host,
            port=port,
            streamable_http_path="/mcp",
        )

        # 配置日志
        self._setup_logging()
        self._register_tools()

    def _setup_logging(self):
        """配置日志格式和级别"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s | %(name)s | %(levelname)s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S',
            stream=sys.stdout
        )
        self.logger = logging.getLogger(self.name)
        self.logger.info("JobSearch MCP Server 初始化完成")

    def _register_tools(self):
        """注册所有工具"""
        job_tools = JobTools(self.logger)
        job_tools.register_tools(self.mcp)
        self.logger.info("工具注册完成")

    def run(self):
        """使用 Streamable HTTP 方式启动 MCP Server"""
        try:
            self.logger.info(
                f"服务启动中... 监听地址: {self.mcp.settings.host}:{self.mcp.settings.port}"
            )
            self.mcp.run(transport="streamable-http")
        except Exception as e:
            self.logger.error(f"服务启动失败: {str(e)}")
            raise


def main():
    server = JobSearchMCPServer()
    server.run()


if __name__ == "__main__":
    main()
