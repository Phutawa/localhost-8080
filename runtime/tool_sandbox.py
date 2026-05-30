# -*- coding: utf-8 -*-
"""
Context Mode - Tool Sandbox Module.
Filters and compresses heavy tool outputs (like Playwright HTML, GitHub logs, or Grep)
to keep the LLM context clean and compact.
"""
import re
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ToolSandbox")

class ToolSandbox:
    @staticmethod
    def compress_tool_output(tool_name: str, raw_output: str) -> str:
        """
        Compresses raw output of a tool dynamically based on its name.
        """
        if not raw_output or not isinstance(raw_output, str):
            return ""

        tool_lower = tool_name.lower()
        if "playwright" in tool_lower or "html" in tool_lower:
            return ToolSandbox._compress_html(raw_output)
        elif "git" in tool_lower:
            return ToolSandbox._compress_git(raw_output)
        elif "grep" in tool_lower:
            return ToolSandbox._compress_grep(raw_output)
        
        # Default safety compression for huge terminal outputs
        if len(raw_output) > 2000:
            logger.info(f"Compressing large output for tool '{tool_name}' ({len(raw_output)} bytes)")
            return f"[Truncated Output - Original length: {len(raw_output)} bytes]\n" + raw_output[:1000] + "\n...\n" + raw_output[-500:]
        
        return raw_output

    @staticmethod
    def _compress_html(raw_html: str) -> str:
        """
        Strips JS, CSS, styles, and extracts only semantic body text/links.
        Converts 50KB+ HTML into a short text representation (~300 bytes).
        """
        # Remove style & script blocks
        clean_html = re.sub(r'<(style|script)[^>]*>([\s\S]*?)</\1>', '', raw_html, flags=re.IGNORECASE)
        # Remove HTML comments
        clean_html = re.sub(r'<!--[\s\S]*?-->', '', clean_html)
        # Extract text content from tags
        text = re.sub(r'<[^>]+>', ' ', clean_html)
        # Collapse whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        
        # Summarize to fit context
        if len(text) > 800:
            return f"[Compressed DOM Content]\nText content snippet: {text[:600]}... [Ends with: {text[-200:]}]"
        return f"[Compressed DOM Content]\nText content: {text}"

    @staticmethod
    def _compress_git(raw_git: str) -> str:
        """
        Summarizes git statuses and diffs to files changed and deletion/addition counts.
        """
        lines = raw_git.splitlines()
        summary_lines = []
        for line in lines:
            if line.startswith("diff --git"):
                summary_lines.append(line)
            elif line.startswith("+++") or line.startswith("---"):
                summary_lines.append(line)
            elif "file changed" in line or "insertions" in line or "deletions" in line:
                summary_lines.append(line)
        
        if summary_lines:
            return "\n".join(summary_lines)
        return raw_git[:1000] + "\n[Git output compressed]"

    @staticmethod
    def _compress_grep(raw_grep: str) -> str:
        """
        Filters grep lists to include filename, line numbers, and clean snippets.
        """
        lines = raw_grep.splitlines()
        if len(lines) <= 15:
            return raw_grep
        
        # Only keep top 10 and bottom 5 lines
        compressed = lines[:10] + ["... [truncated intermediate grep results] ..."] + lines[-5:]
        return "\n".join(compressed)
