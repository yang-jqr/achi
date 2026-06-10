from typing import Any
from word.word import read_word_file
class ResumeTools():
    def register_tools(self, mcp: Any):
        """Register job tools."""

        @mcp.tool(description="读取指定路径的word文件")
        def get_word_by_filepath(filepath: str) -> list:
            """根据文件路径获取word文件内容"""
            content=read_word_file(filepath)
            return content

