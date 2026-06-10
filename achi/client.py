import asyncio
from contextlib import AsyncExitStack
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client
from openai import AsyncOpenAI
from typing import Optional
import json
import os
import sys
from dotenv import load_dotenv

# 加载 .env 文件
load_dotenv()

class MCPClient:
    def __init__(self):
        # Initialize session and client objects
        self.session: Optional[ClientSession] = None
        self.exit_stack = AsyncExitStack()
        self.client = AsyncOpenAI(
            api_key=os.getenv("deepseek"),
            base_url="https://api.deepseek.com"
        )

    async def connect_to_server(self, server_url: str):
        """Connect to an MCP server"""
        read_stream, write_stream,_ = await self.exit_stack.enter_async_context(streamablehttp_client(url=server_url))
        self.session = await self.exit_stack.enter_async_context(ClientSession(read_stream, write_stream))
        await self.session.initialize()
                
        # List available tools
        response = await self.session.list_tools()
        tools = response.tools
        print("\nConnected to server with tools:", [tool.name for tool in tools])

    async def _send_messages(self, messages: list, tools: list):
        return await self.client.chat.completions.create(
            model="deepseek-chat",
            messages=messages,
            tools=tools
        )

    async def process_query(self, query: str) -> str:
        """Process a query using OpenAI and available tools"""
        #print("\nProcessing query:", query)
        messages = [
            {
                "role": "user",
                "content": query
            }
        ]
        #print("\nself.session", self.session)
            
        response = await self.session.list_tools()
        #print("\nAvailable tools:", response)
        available_tools = [{
            "type": "function",
            "function": {
                "name": tool.name,
                "description": tool.description,
                "parameters": tool.inputSchema
            }
        } for tool in response.tools]

        # Initial OpenAI API call
        response = await self._send_messages(messages, available_tools)
     
        final_text = []
        message = response.choices[0].message
        final_text.append(message.content or "")

        # Process response and handle tool calls
        while message.tool_calls:
            # Handle each tool call
            for tool_call in message.tool_calls:
                tool_name = tool_call.function.name
                tool_args = json.loads(tool_call.function.arguments)
                
                # Execute tool call
                print(f"\n需调用工具{tool_name} 参数为 {tool_args}")
                result = await self.session.call_tool(tool_name, tool_args)
                final_text.append(f"[Calling tool {tool_name} with args {tool_args}]")

                # Add tool call and result to messages
                messages.append({
                    "role": "assistant",
                    "tool_calls": [
                        {
                            "id": tool_call.id,
                            "type": "function",
                            "function": {
                                "name": tool_name,
                                "arguments": json.dumps(tool_args)
                            }
                        }
                    ]
                })
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": str(result.content)
                })

            # Get next response from OpenAI
            response = await self._send_messages(messages, available_tools)
            
            message = response.choices[0].message
            if message.content:
                final_text.append(message.content)

        return "\n".join(final_text)

    async def chat_loop(self):
        """Run an interactive chat loop"""
        print("\nMCP Client Started!")
        print("Type your queries or 'quit' to exit.")
        
        while True:
            try:
                query = input("\nQuery: ").strip()
                if query.lower() == 'quit':
                    break
                response = await self.process_query(query)
                print("\n" + response)
            except Exception as e:
                print(f"\nError: {str(e)}")
    
    async def cleanup(self):
        """Clean up resources"""
        await self.exit_stack.aclose()

async def main():
    if len(sys.argv) < 2:
        # uv run client.py http://localhost:8000
        print("Usage: uv run client.py <server_url>")
        sys.exit(1)
        
    client = MCPClient()
    try:
        await client.connect_to_server(sys.argv[1])
        await client.chat_loop()
    finally:
        await client.cleanup()

if __name__ == "__main__":
    asyncio.run(main())