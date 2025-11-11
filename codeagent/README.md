# 代码Agent

基于ReAct方法的代码生成和执行Agent，专门用于处理XLSX文件并执行数据查询任务。

## 功能特性

1. **读取XLSX文件**：读取前20行数据，分析列结构和内容
2. **生成Python代码**：基于列信息和用户查询生成数据处理代码
3. **执行代码**：安全执行生成的Python代码并返回结果

## 工具说明

### 1. read_xlsx
- **功能**：读取XLSX文件的前20行数据
- **输入**：file_path（XLSX文件路径）
- **输出**：JSON格式的列信息和前20行数据

### 2. execute_code
- **功能**：执行Python代码
- **输入**：
  - code：要执行的Python代码
  - file_path：XLSX文件路径
- **输出**：执行结果

## 使用方法

### 启动服务

```bash
cd codeagent
pip install -r requirements.txt
python server.py
```

服务默认运行在端口 5002。

### API接口

#### 1. 健康检查
```bash
GET /health
```

#### 2. 单次查询
```bash
POST /query
Content-Type: application/json

{
    "query": "查询所有年龄大于30的员工姓名和部门",
    "file_path": "/path/to/data.xlsx",
    "max_iterations": 10
}
```

#### 3. 多轮对话
```bash
POST /chat
Content-Type: application/json

{
    "query": "查询所有年龄大于30的员工姓名和部门",
    "file_path": "/path/to/data.xlsx",
    "conversation_history": [...]
}
```

## 工作流程

1. **读取文件**：Agent首先调用 `read_xlsx` 读取前20行，分析列结构
2. **生成代码**：LLM基于列信息和用户查询，直接在回复中生成完整的Python代码（用 ```python ... ``` 包裹）
3. **自动执行**：系统自动提取代码并调用 `execute_code` 执行
4. **展示结果**：LLM解析执行结果，以友好方式展示筛选出的用户信息
5. **询问用户**：询问用户是否还有其他问题

## 注意事项

- 代码执行在临时文件中进行，执行完成后自动清理
- 代码执行有30秒超时限制
- 代码必须输出JSON格式的结果
- 代码中必须使用 `FILE_PATH` 变量访问文件路径

## 环境变量

- `DEEPSEEK_API_KEY`：DeepSeek API密钥（默认：sk-1e6a5099e785466789ea6243ef517aac）
- `CODEAGENT_PORT`：服务端口（默认：5002）

