# 🧠 SQL Natural Language Agent

A powerful Streamlit application that allows you to interact with SQL Server databases using natural language queries. The agent uses AI to convert your questions into SQL queries and provides human-readable summaries of the results.

## ✨ Features

- **🔗 Database Connection**: Connect to SQL Server instances with secure authentication
- **📋 Table Grid Interface**: Beautiful 5-column grid layout for easy table selection
- **🎯 Context Awareness**: Maintains database and table context throughout the session
- **🤖 AI-Powered Queries**: Converts natural language to SQL using Ollama
- **📊 Schema Detection**: Automatically detects correct schema names (dbo, Sales, Production, etc.)
- **📚 Q&A History**: Keeps track of all your questions and results
- **🔄 Dynamic Schema Loading**: Loads table schemas on-demand
- **💡 Smart Summaries**: AI-generated summaries of query results

## 🚀 Quick Start

### Prerequisites

1. **Python 3.8+**
2. **SQL Server ODBC Driver 17**
3. **Ollama** running locally with `llama3` model

### Installation

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd db-AI-Agent
   ```

2. **Create virtual environment:**
   ```bash
   python -m venv venv
   ```

3. **Activate virtual environment:**
   - Windows: `venv\Scripts\activate`
   - Linux/Mac: `source venv/bin/activate`

4. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

5. **Start Ollama (if not running):**
   ```bash
   ollama run llama3
   ```

6. **Run the application:**
   ```bash
   streamlit run app.py
   ```

## 📖 Usage

1. **Connect to Server**: Enter your SQL Server connection details
2. **Select Database**: Choose from available databases
3. **Load Tables**: Click "Load Tables" to see available tables
4. **Select Table**: Click on any table in the grid to select it
5. **Ask Questions**: Type natural language questions about your data
6. **View Results**: See SQL queries, results, and AI-generated summaries

## 🔧 Configuration

### Database Connection
- **Host**: SQL Server instance (e.g., `localhost` or `SERVER\INSTANCE`)
- **Port**: Optional port number
- **Username**: SQL Server username
- **Password**: SQL Server password

### Ollama Configuration
- **Model**: Uses `llama3` by default
- **URL**: `http://localhost:11434/api/generate`
- **Stream**: Disabled for better response handling

## 🛠️ Dependencies

- **streamlit**: Web application framework
- **pyodbc**: SQL Server database connectivity
- **pandas**: Data manipulation and analysis
- **requests**: HTTP library for Ollama API calls

## 🎨 Features in Detail

### Smart Schema Detection
- Automatically detects schema names (dbo, Sales, Production, etc.)
- Generates correct SQL with proper database.table.schema references
- Handles different database naming conventions

### Context Management
- Maintains database and table context throughout the session
- Q&A history includes context information
- Seamless switching between databases and tables

### Enhanced UI
- 5-column responsive grid for table selection
- Visual highlighting of selected tables
- Clear context indicators
- Professional styling and layout

### Error Handling
- Comprehensive error messages
- SQL syntax cleanup (backticks to square brackets)
- Connection validation and retry logic

## 📝 Example Queries

- "Show me the top 10 customers by revenue"
- "How many orders were placed last month?"
- "What are the most popular products?"
- "Show customer distribution by region"
- "Find customers with no orders in the last 6 months"

## 🔒 Security Notes

- Passwords are handled securely through Streamlit
- Database connections are established per query
- No sensitive data is stored in session state
- Virtual environment keeps dependencies isolated

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License.

## 🆘 Troubleshooting

### Common Issues

1. **ODBC Driver Error**: Install SQL Server ODBC Driver 17
2. **Ollama Connection**: Ensure Ollama is running on localhost:11434
3. **Model Not Found**: Run `ollama pull llama3` to download the model
4. **Database Connection**: Verify server details and credentials

### Getting Help

- Check the error messages in the Streamlit interface
- Verify your SQL Server connection details
- Ensure Ollama is running with the correct model
- Check the console output for detailed error information 