# 🐬 MCP Server – MySQL Tools (PyMySQL + FastMCP)

This project provides a **Model Context Protocol (MCP)** server that exposes MySQL operations as tools for AI assistants such as **Claude Desktop** or **ChatGPT Desktop**.

It allows an AI to:
- Run SQL queries  
- Describe tables  
- Fetch index information  
- Fetch foreign key details  

All using a secure MySQL connection.

---

## ✨ Features

- ✔ Connects to MySQL using **PyMySQL**
- ✔ Exposes tools using **FastMCP**
- ✔ Supports:
  - `run_query`
  - `describe_table`
  - `describe_indexes_and_foreign_keys`
- ✔ Reads environment configuration via `.env`
- ✔ Fully compatible with **Python 3.12**

---

## 📂 Project Structure

```
mcp_server_mysql/
│── mssql_mcp_server.py   # Main MCP server (MySQL version)
│── requirements.txt       # Python dependencies
│── .env.example           # Environment variable template
│── README.md
```

---

## 🔧 Requirements

- Python **3.12.x**
- MySQL server (local or remote)
- Claude Desktop or any MCP-compatible client

Install Python dependencies:

```bash
pip install -r requirements.txt
```

---

## ⚙️ Environment Variables (`.env`)

Create a `.env` file in the project root:

```
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=yourpassword
MYSQL_DB=yourdatabase
```

> You can rename `.env.example` → `.env`

---

## 🚀 Running the MCP Server

Activate your Python environment:

```bash
source .venv/bin/activate
```

Start the server:

```bash
python mssql_mcp_server.py
```

⚠️ MCP servers **do not run on an HTTP port**.  
They run using **stdio** and must be launched by an MCP client like Claude Desktop.

---

## 💻 Using with Claude Desktop (macOS)

Edit your Claude config file:

```
~/Library/Application Support/Claude/claude_desktop_config.json
```

Add:

```json
{
  "mcpServers": {
    "mysql": {
      "type": "python",
      "command": "/FULL/PATH/TO/.venv/bin/python3.12",
      "args": [
        "/FULL/PATH/TO/mcp_server_mysql/mssql_mcp_server.py"
      ]
    }
  }
}
```

Restart Claude Desktop.

You will now see the tools:

- `mysql-db.run_query`
- `mysql-db.describe_table`
- `mysql-db.describe_indexes_and_foreign_keys`

---

## 🧪 Example Usage

### Run a SQL query:

```
run_query("SELECT * FROM users LIMIT 10")
```

### Describe a table:

```
describe_table("your_schema", "users")
```

### Get index + foreign key info:

```
describe_indexes_and_foreign_keys("your_schema", "orders")
```

---

## 🛠 Development

To recreate the environment:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

---

## 🐛 Troubleshooting

### ❗ Python version wrong inside venv  
Delete and recreate venv:

```bash
rm -rf .venv
python3.12 -m venv .venv
```

### ❗ Claude shows “ENOENT”  
Check your Python path in `claude_desktop_config.json`.

### ❗ MySQL connection fails  
Verify credentials in `.env`.

---

## 🤝 Contributing

PRs are welcome!  
You may add:
- List tables tool
- Schema explorer tool
- Insert/update helpers

---

## 📄 License

MIT License — free to use, modify, and distribute.

---

## ⭐ Support

If you found this useful, please ⭐ the repo:

👉 https://github.com/jasbir125/mcp_server_mysql
