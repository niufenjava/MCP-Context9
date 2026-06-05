# AGENTS.md

## 项目路径

`/Users/niufen/my-projects/MCP-Context9`

## 打包命令

代码改动后执行：

```bash
cd /Users/niufen/my-projects/MCP-Context9 && ./package.sh
```

输出：`~/.mcp/context9.pyz`

## MCP 部署

所有 AI Agent（OpenClaw / OpenCode 等）共用同一配置：

```json
"context9": {
  "type": "local",
  "command": ["/Users/niufen/.mcp/context9.pyz", "--skip-update"],
  "enabled": true
}
```

## 开发调试

项目目录下直接运行：

```bash
./context9.sh start
```

## 索引目录

`~/.index/doc-index`（含 sqlite 数据库和 JSON 元数据）
