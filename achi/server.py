import logging
import sys
from mcp.server.fastmcp import FastMCP
from tools.job import JobTools
# from tools.resume import ResumeTools

class JobSearchMCPServer:
    def __init__(self):
        self.name = "jobsearch_mcp_server"
        self.mcp = FastMCP(self.name)

        # Configure logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(self.name)

        # Initialize tools
        self._register_tools()

    def _register_tools(self):
        """Register all MCP tools."""
        # Initialize tool classes
        job_tools = JobTools(self.logger)
        #resume_tools = ResumeTools()

        job_tools.register_tools(self.mcp)
        #resume_tools.register_tools(self.mcp)

    def run(self, transport="streamable-http"):
        """Run the MCP server.

        Args:
            transport: 'stdio' (Claude Desktop/Roo Code) or 'streamable-http' (HTTP API)
        """
        if transport == "stdio":
            self.mcp.run()
        else:
            import uvicorn
            app = self.mcp.streamable_http_app()
            uvicorn.run(app, host="0.0.0.0", port=8000)

def main():
    transport = sys.argv[1] if len(sys.argv) > 1 else "streamable-http"
    server = JobSearchMCPServer()
    print(f"MCP Server 启动中... (transport={transport})", file=sys.stderr)
    server.run(transport=transport)

if __name__ == "__main__":
    main()

