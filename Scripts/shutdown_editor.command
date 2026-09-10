#!/bin/zsh
set -e
PROJECT_DIR="${0:A:h:h}"
export NO_PROXY=127.0.0.1,localhost
exec /Users/rare/.local/share/ashwell-mcp/venv/bin/python "$PROJECT_DIR/Scripts/chapter01_mcp.py" call_tool '{"toolset_name":"Users.rare.dev.ash-well-ue.Scripts.chapter01_tools.ChapterOneTools","tool_name":"run_stage","arguments":{"stage":"shutdown"}}'
