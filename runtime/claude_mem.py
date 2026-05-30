# -*- coding: utf-8 -*-
"""
Claude Mem Module.
Hooks into the session lifecycle, logs events (file edits, commands, decisions)
to a local SQLite database, retrieves relevant historical logs via text matches,
and automatically generates/updates a folder-level CLAUDE.md.
"""
import os
import sqlite3
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ClaudeMem")

class ClaudeMem:
    def __init__(self, memory_dir: str = "../memory", workspace_dir: str = "."):
        self.memory_dir = os.path.abspath(memory_dir)
        self.workspace_dir = os.path.abspath(workspace_dir)
        os.makedirs(self.memory_dir, exist_ok=True)
        
        self.db_path = os.path.join(self.memory_dir, "claude_mem.db")
        self._init_db()

    def _init_db(self):
        """
        Initializes SQLite database schema.
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS memories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT,
                    category TEXT,
                    details TEXT,
                    file_path TEXT,
                    session_id TEXT
                )
            """)
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Failed to initialize SQLite memory database: {e}")

    def log_event(self, category: str, details: str, file_path: str = "", session_id: str = "default_session"):
        """
        Logs a lifecycle event into SQLite.
        """
        timestamp = datetime.now().isoformat()
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO memories (timestamp, category, details, file_path, session_id) VALUES (?, ?, ?, ?, ?)",
                (timestamp, category, details, file_path, session_id)
            )
            conn.commit()
            conn.close()
            logger.info(f"[ClaudeMem Log] {category}: {details[:60]}...")
            
            # Keep CLAUDE.md synchronized
            self.generate_claude_md()
        except Exception as e:
            logger.error(f"Failed to write log event to memory: {e}")

    def retrieve_relevant_memories(self, query: str, limit: int = 5) -> str:
        """
        Searches SQLite database for historical events containing query keywords.
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            # Simple SQL LIKE search mimicking vector search similarity retrieval
            cursor.execute(
                "SELECT timestamp, category, details, file_path FROM memories WHERE details LIKE ? OR category LIKE ? OR file_path LIKE ? ORDER BY id DESC LIMIT ?",
                (f"%{query}%", f"%{query}%", f"%{query}%", limit)
            )
            rows = cursor.fetchall()
            conn.close()
            
            if not rows:
                return ""
            
            memory_block = "\n=== RETRIEVED RELEVANT HISTORICAL MEMORIES ===\n"
            for row in rows:
                memory_block += f"[{row[0]}] {row[1]} in {row[3] or 'N/A'}: {row[2]}\n"
            return memory_block
        except Exception as e:
            logger.error(f"Failed to query SQLite memories: {e}")
            return ""

    def generate_claude_md(self):
        """
        Automatically compiles and updates the root-level CLAUDE.md file
        summarizing active commands, guidelines, and technical decisions.
        """
        claude_md_path = os.path.join(self.workspace_dir, "CLAUDE.md")
        
        # Pull last 5 decisions from SQLite
        recent_decisions = []
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT details FROM memories WHERE category='decision' ORDER BY id DESC LIMIT 5")
            recent_decisions = [r[0] for r in cursor.fetchall()]
            conn.close()
        except Exception:
            pass

        decisions_str = ""
        if recent_decisions:
            decisions_str = "\n## Recent Technical Decisions\n"
            for dec in recent_decisions:
                decisions_str += f"- {dec}\n"

        content = f"""# CLAUDE.md (AIOS Workspace Guide)

## Core Development Commands
- **Install dependencies:** `pip install -e .` or `./.venv/bin/pip install -e .`
- **Run Workflow Engine:** `python3 -m runtime.cli -w workflows/<pipeline>.yaml -s .`
- **Verify test suites:** `./.venv/bin/pytest` or python3 unit-testing command.

## Quality & Style Guidelines
- Keep critical computational loops (like DSP filtering) 100% allocation-free to prevent GC pauses.
- Never let `NaN` or `Infinity` propagate through digital feedback systems (always reset/clamp states).
- Flush subnormal numbers smaller than $10^{{-30}}$ to cleanly protect CPU latency.
{decisions_str}
## Active Plugins
- **Context Mode:** Enabled (raw tool output sandbox filtering).
- **Claude Mem:** Enabled (local SQLite persistence of decisions & lifecycle triggers).
- **GSD Orchestrator:** Enabled (autonomous task decomposition & sub-agent validation).

*Last updated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}*
"""
        try:
            with open(claude_md_path, "w", encoding="utf-8") as f:
                f.write(content)
            logger.info("Synchronized and updated CLAUDE.md successfully.")
        except Exception as e:
            logger.error(f"Failed to write CLAUDE.md file: {e}")
