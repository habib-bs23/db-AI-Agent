import streamlit as st
import pyodbc
import pandas as pd
import requests
import time
from datetime import datetime

# Configuration for speed optimization
SPEED_CONFIG = {
    "model": "llama3",  # You can change to "llama3:8b" for faster responses
    "temperature": 0.1,  # Lower = faster, more deterministic
    "top_p": 0.9,       # Lower = faster generation
    "top_k": 40,        # Lower = faster token selection
    "max_tokens": 200,   # Limit response length
    "summary_max_tokens": 100,  # Shorter summaries
    "enable_streaming": False,  # Set to True for real-time streaming
    "cache_responses": True,    # Cache similar queries
}

# Page configuration
st.set_page_config(
    page_title="🧠 SQL Natural Language Agent",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS for better styling with improved contrast
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #2c3e50 0%, #34495e 100%);
        padding: 2rem;
        border-radius: 10px;
        margin-bottom: 2rem;
        color: white;
        text-align: center;
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
    }
    
    .success-box {
        background-color: #d1e7dd;
        border: 2px solid #0f5132;
        border-radius: 8px;
        padding: 1rem;
        margin: 1rem 0;
        color: #0f5132;
        font-weight: 500;
    }
    
    .info-box {
        background-color: #cff4fc;
        border: 2px solid #055160;
        border-radius: 8px;
        padding: 1rem;
        margin: 1rem 0;
        color: #055160;
        font-weight: 500;
    }
    
    .warning-box {
        background-color: #fff3cd;
        border: 2px solid #664d03;
        border-radius: 8px;
        padding: 1rem;
        margin: 1rem 0;
        color: #664d03;
        font-weight: 500;
    }
    
    .error-box {
        background-color: #f8d7da;
        border: 2px solid #721c24;
        border-radius: 8px;
        padding: 1rem;
        margin: 1rem 0;
        color: #721c24;
        font-weight: 500;
    }
    
    .table-grid {
        display: grid;
        grid-template-columns: repeat(5, 1fr);
        gap: 10px;
        margin: 1rem 0;
    }
    
    .table-button {
        background: linear-gradient(135deg, #2c3e50 0%, #34495e 100%);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 12px;
        cursor: pointer;
        transition: all 0.3s ease;
        text-align: center;
        font-weight: 500;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    .table-button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
    }
    
    .table-button.selected {
        background: linear-gradient(135deg, #198754 0%, #20c997 100%);
        box-shadow: 0 4px 8px rgba(25, 135, 84, 0.3);
        border: 2px solid #198754;
    }
    
    .qa-container {
        background: #2c3e50;
        border-radius: 10px;
        padding: 1.5rem;
        margin: 1rem 0;
        border-left: 4px solid #3498db;
        box-shadow: 0 4px 8px rgba(0,0,0,0.3);
        color: white;
    }
    
    .question-box {
        background: #34495e;
        border-radius: 8px;
        padding: 1rem;
        margin: 1rem 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.2);
        border: 1px solid #4a5568;
        color: white;
    }
    
    .result-box {
        background: #34495e;
        border-radius: 8px;
        padding: 1rem;
        margin: 1rem 0;
        border-left: 4px solid #27ae60;
        box-shadow: 0 2px 4px rgba(0,0,0,0.2);
        color: white;
    }
    
    .stButton > button {
        background: linear-gradient(135deg, #2c3e50 0%, #34495e 100%);
        color: white !important;
        border: none;
        border-radius: 8px;
        padding: 12px 24px;
        font-weight: 500;
        transition: all 0.3s ease;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
        background: linear-gradient(135deg, #34495e 0%, #2c3e50 100%);
    }
    
    .stTextInput > div > div > input {
        border-radius: 8px;
        border: 2px solid #dee2e6;
        padding: 12px;
        font-size: 16px;
        color: #212529;
        background-color: white;
    }
    
    .stTextInput > div > div > input:focus {
        border-color: #2c3e50;
        box-shadow: 0 0 0 0.2rem rgba(44, 62, 80, 0.25);
        outline: none;
    }
    
    .stTextArea > div > div > textarea {
        border-radius: 8px;
        border: 2px solid #dee2e6;
        padding: 12px;
        font-size: 16px;
        color: #212529;
        background-color: white;
    }
    
    .stTextArea > div > div > textarea:focus {
        border-color: #2c3e50;
        box-shadow: 0 0 0 0.2rem rgba(44, 62, 80, 0.25);
        outline: none;
    }
    
    .stSelectbox > div > div > select {
        border-radius: 8px;
        border: 2px solid #dee2e6;
        padding: 8px 12px;
        font-size: 16px;
        color: #212529;
        background-color: white;
    }
    
    .stSelectbox > div > div > select:focus {
        border-color: #2c3e50;
        box-shadow: 0 0 0 0.2rem rgba(44, 62, 80, 0.25);
        outline: none;
    }
    
    /* Ensure text is visible in all containers */
    .qa-container, .question-box, .result-box {
        color: white;
    }
    
    .qa-container h4, .qa-container h5, .question-box h4, .result-box h4, .result-box h5 {
        color: #3498db;
        font-weight: 600;
    }
    
    .qa-container p, .question-box p, .result-box p {
        color: #ecf0f1;
        line-height: 1.6;
    }
    
    .qa-container code, .result-box code {
        background-color: #2c3e50;
        color: #e74c3c;
        padding: 2px 6px;
        border-radius: 4px;
        font-family: 'Courier New', monospace;
        border: 1px solid #4a5568;
    }
    
    .qa-container pre, .result-box pre {
        background-color: #2c3e50;
        border: 1px solid #4a5568;
        border-radius: 4px;
        padding: 12px;
        color: #ecf0f1;
        font-family: 'Courier New', monospace;
        overflow-x: auto;
    }
    
    /* Progress bar styling */
    .stProgress > div > div > div > div {
        background-color: #2c3e50;
    }
    
    /* Status text styling */
    .status-text {
        color: #2c3e50;
        font-weight: 500;
        margin: 8px 0;
    }
</style>
""", unsafe_allow_html=True)

# Main header
st.markdown("""
<div class="main-header">
    <h1>🧠 SQL Natural Language Agent</h1>
    <p>Transform your questions into SQL queries with AI-powered intelligence</p>
</div>
""", unsafe_allow_html=True)

# Initialize session state for context tracking
if "current_context" not in st.session_state:
    st.session_state.current_context = {
        "database": None,
        "table": None,
        "schema": None,
        "schema_name": "dbo",
        "connection": None
    }

# Step 1: Ask for server connection (not DB yet)
with st.form("server_credentials"):
    st.subheader("🔗 Connect to SQL Server")
    
    col1, col2 = st.columns(2)
    with col1:
        server = st.text_input("Host (e.g. 127.0.0.1 or SERVER\\INSTANCE)", value="localhost")
        username = st.text_input("Username", value="sa")
    with col2:
        port = st.text_input("Port (optional)", value="1433")
        password = st.text_input("Password", type="password", value="")

    submitted = st.form_submit_button("🚀 Connect to Server", use_container_width=True)

if submitted:
    with st.spinner("🔄 Connecting to server..."):
        driver = "ODBC Driver 17 for SQL Server"
        port_str = f",{port}" if port else ""
        try:
            conn_str = f"DRIVER={{{driver}}};SERVER={server}{port_str};UID={username};PWD={password};DATABASE=master"
            test_conn = pyodbc.connect(conn_str)
            test_cursor = test_conn.cursor()

            # Step 2: Fetch all databases
            test_cursor.execute("SELECT name FROM sys.databases WHERE database_id > 4")
            db_list = [row[0] for row in test_cursor.fetchall()]

            if db_list:
                st.markdown('<div class="success-box">✅ Connected successfully!</div>', unsafe_allow_html=True)
                st.session_state.server_info = {
                    "server": server,
                    "port": port,
                    "username": username,
                    "password": password
                }
                st.session_state.db_list = db_list
                # Reset context when connecting to new server
                st.session_state.current_context = {
                    "database": None,
                    "table": None,
                    "schema": None,
                    "schema_name": "dbo",
                    "connection": None
                }
            else:
                st.markdown('<div class="warning-box">⚠️ No user databases found.</div>', unsafe_allow_html=True)
        except Exception as e:
            st.markdown(f'<div class="error-box">❌ Connection failed: {e}</div>', unsafe_allow_html=True)

# Step 3: Select database and automatically load tables
if "db_list" in st.session_state:
    st.subheader("📦 Select a Database")
    selected_db = st.selectbox("Available Databases", st.session_state.db_list)

    if selected_db:
        st.markdown(f'<div class="info-box">🎯 You selected database: <strong>{selected_db}</strong></div>', unsafe_allow_html=True)
        
        # Check if database changed
        if selected_db != st.session_state.get("selected_db", None):
            st.session_state.selected_db = selected_db
            
            # Automatically load tables when database changes
            with st.spinner("🔄 Loading tables..."):
                server = st.session_state.server_info["server"]
                port = st.session_state.server_info["port"]
                username = st.session_state.server_info["username"]
                password = st.session_state.server_info["password"]
                database = selected_db

                port_str = f",{port}" if port else ""
                conn_str = f"DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={server}{port_str};DATABASE={database};UID={username};PWD={password}"

                try:
                    conn = pyodbc.connect(conn_str)
                    cursor = conn.cursor()

                    cursor.execute("""
                        SELECT TABLE_NAME 
                        FROM INFORMATION_SCHEMA.TABLES 
                        WHERE TABLE_TYPE='BASE TABLE'
                    """)
                    tables = [row[0] for row in cursor.fetchall()]

                    if tables:
                        st.markdown('<div class="success-box">✅ Tables loaded automatically!</div>', unsafe_allow_html=True)
                        st.session_state.conn = conn
                        st.session_state.tables = tables
                        # Update context with new database
                        st.session_state.current_context["database"] = database
                        st.session_state.current_context["connection"] = conn
                        st.session_state.current_context["table"] = None
                        st.session_state.current_context["schema"] = None
                        st.session_state.current_context["schema_name"] = "dbo"
                        # Clear previous table selection when database changes
                        if "selected_table" in st.session_state:
                            del st.session_state.selected_table
                        if "schema" in st.session_state:
                            del st.session_state.schema
                        st.rerun()
                    else:
                        st.markdown('<div class="warning-box">⚠️ No tables found in this database.</div>', unsafe_allow_html=True)
                except Exception as e:
                    st.markdown(f'<div class="error-box">❌ Failed to connect to database: {e}</div>', unsafe_allow_html=True)
        else:
            st.session_state.selected_db = selected_db

# Step 4: Select table and load schema
if "tables" in st.session_state:
    st.subheader("📋 Select a Table to Explore")
    
    # Display tables in a grid format
    tables = st.session_state.tables
    
    # Create columns for the grid (5 columns)
    col1, col2, col3, col4, col5 = st.columns(5)
    
    # Distribute tables across columns
    for i, table in enumerate(tables):
        if i % 5 == 0:
            col = col1
        elif i % 5 == 1:
            col = col2
        elif i % 5 == 2:
            col = col3
        elif i % 5 == 3:
            col = col4
        else:
            col = col5
            
        # Create a button for each table with proper selection highlighting
        selected_table = st.session_state.get("selected_table", None)
        is_selected = table == selected_table
        
        # Use different button types for selected vs unselected
        if is_selected:
            if col.button(f"✅ {table}", key=f"table_{table}", use_container_width=True, type="primary"):
                st.session_state.selected_table = table
                st.rerun()
        else:
            if col.button(f"📄 {table}", key=f"table_{table}", use_container_width=True, type="secondary"):
                st.session_state.selected_table = table
                st.rerun()
    
    # Show currently selected table
    if "selected_table" in st.session_state:
        st.markdown(f'<div class="info-box">🎯 <strong>Selected Table:</strong> {st.session_state.selected_table}</div>', unsafe_allow_html=True)
        
        # Load schema for selected table
        if st.session_state.selected_table != st.session_state.get("last_loaded_table", None):
            st.session_state.last_loaded_table = st.session_state.selected_table
            
            with st.spinner(f"🔄 Loading schema for {st.session_state.selected_table}..."):
                cursor = st.session_state.conn.cursor()
                try:
                    # First, get the schema name for this table
                    cursor.execute(f"""
                        SELECT TABLE_SCHEMA 
                        FROM INFORMATION_SCHEMA.TABLES 
                        WHERE TABLE_NAME = ?
                    """, st.session_state.selected_table)
                    
                    schema_result = cursor.fetchone()
                    if schema_result:
                        schema_name = schema_result[0]
                        st.session_state.current_context["schema_name"] = schema_name
                    else:
                        schema_name = "dbo"  # Default fallback
                        st.session_state.current_context["schema_name"] = schema_name
                    
                    # Execute the query to get column information
                    cursor.execute(f"""
                        SELECT COLUMN_NAME, DATA_TYPE 
                        FROM INFORMATION_SCHEMA.COLUMNS 
                        WHERE TABLE_NAME = ? AND TABLE_SCHEMA = ?
                    """, st.session_state.selected_table, schema_name)
                    
                    # Fetch all rows as proper tuples
                    rows = []
                    for row in cursor.fetchall():
                        # Convert each row to a proper tuple of values
                        rows.append((row.COLUMN_NAME, row.DATA_TYPE))  # Access by column name
                    
                    # Create DataFrame
                    if rows:
                        schema_df = pd.DataFrame(rows, columns=['COLUMN_NAME', 'DATA_TYPE'])
                        st.session_state.schema = schema_df
                        # Update context with new table and schema
                        st.session_state.current_context["table"] = st.session_state.selected_table
                        st.session_state.current_context["schema"] = schema_df
                        st.markdown(f'<div class="success-box">✅ Schema loaded for table <strong>{st.session_state.selected_table}</strong> (Schema: <strong>{schema_name}</strong>)</div>', unsafe_allow_html=True)
                    else:
                        st.markdown(f'<div class="warning-box">No columns found for table {st.session_state.selected_table}</div>', unsafe_allow_html=True)
                        
                except Exception as e:
                    st.markdown(f'<div class="error-box">Error fetching schema: {str(e)}</div>', unsafe_allow_html=True)

# Step 5: Show schema
if "schema" in st.session_state:
    st.subheader(f"📑 Schema for table `{st.session_state.selected_table}`")
    
    # Display schema in a nice format
    schema_df = st.session_state.schema
    st.dataframe(schema_df, use_container_width=True)

# Step 6: Continuous Q&A with context awareness
if "schema" in st.session_state and "selected_table" in st.session_state:
    st.subheader("💬 Ask Questions About Your Data")
    if "qa_history" not in st.session_state:
        st.session_state.qa_history = []

    # Display current context
    current_db = st.session_state.current_context["database"]
    current_table = st.session_state.current_context["table"]
    st.markdown(f'<div class="info-box">🔍 <strong>Current Context:</strong> Database: <code>{current_db}</code> | Table: <code>{current_table}</code></div>', unsafe_allow_html=True)

    # Display Q&A history first
    if st.session_state.qa_history:
        st.subheader("📚 Q&A History")
        
        # Add a button to clear history
        col1, col2 = st.columns([1, 4])
        with col1:
            if st.button("🗑️ Clear History", type="secondary"):
                st.session_state.qa_history = []
                st.rerun()
        
        # Display history in chronological order (oldest first, latest at bottom)
        for i, qa in enumerate(st.session_state.qa_history):
            with st.container():
                # Parse the result string to create a proper table
                result_lines = qa['result'].strip().split('\n')
                if len(result_lines) > 1:
                    # First line contains headers
                    headers = result_lines[0].split('\t')
                    # Remaining lines contain data
                    data_rows = []
                    for line in result_lines[1:]:
                        if line.strip():  # Skip empty lines
                            data_rows.append(line.split('\t'))
                    
                    # Create DataFrame for display
                    if data_rows:
                        result_df = pd.DataFrame(data_rows, columns=headers)
                    else:
                        result_df = pd.DataFrame(columns=headers)
                else:
                    result_df = pd.DataFrame()
                
                st.markdown(f"""
                <div class="qa-container">
                    <div class="question-box">
                        <h4>❓ Question {i + 1}</h4>
                        <p><strong>Context:</strong> Database: <code>{qa.get('database', 'N/A')}</code> | Table: <code>{qa.get('table', 'N/A')}</code></p>
                        <p><strong>Q:</strong> {qa['question']}</p>
                    </div>
                    <div class="result-box">
                        <h5>🔍 Generated SQL:</h5>
                        <pre><code>{qa['sql']}</code></pre>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                # Display results in a table format
                if not result_df.empty:
                    st.dataframe(result_df, use_container_width=True)
                else:
                    st.info("No results to display")
                
                st.markdown(f"""
                <div class="result-box">
                    <h5>💡 Summary:</h5>
                    <p>{qa['summary']}</p>
                    <small>🕒 {qa.get('timestamp', 'N/A').strftime('%Y-%m-%d %H:%M:%S') if hasattr(qa.get('timestamp', ''), 'strftime') else 'N/A'}</small>
                </div>
                """, unsafe_allow_html=True)
                st.markdown("---")

    # Question input at the bottom
    st.subheader("🤖 Ask a New Question")
    
    # Create a form for the question
    with st.form("question_form"):
        user_question = st.text_area(
            "Enter your question (e.g., show top 10 customers by revenue)",
            key="nl_question",
            height=100,
            placeholder="Ask anything about your data..."
        )
        
        col1, col2, col3 = st.columns([1, 1, 2])
        with col1:
            ask_button = st.form_submit_button("🚀 Ask", use_container_width=True)
        with col2:
            if st.form_submit_button("🔄 Clear", type="secondary", use_container_width=True):
                st.session_state.qa_history = []
                st.rerun()

    if ask_button and user_question:
        # Get current context
        table_name = st.session_state.current_context["table"]
        schema_df = st.session_state.current_context["schema"]
        database_name = st.session_state.current_context["database"]
        schema_name = st.session_state.current_context.get("schema_name", "dbo")
        
        schema_lines = [
            f"{row['COLUMN_NAME']} ({row['DATA_TYPE']})"
            for _, row in schema_df.iterrows()
        ]
        schema_str = "\n".join(schema_lines)
        prompt = (
            f"Table: [{schema_name}].[{table_name}]\n"
            f"Columns: {schema_str}\n"
            f"Task: {user_question}\n\n"
            f"IMPORTANT: Return ONLY the SQL query. No explanations, no comments, no text before or after.\n"
            f"Rules: Use aggregates when possible, TOP N for limits, WHERE for filters, GROUP BY with aggregates.\n\n"
            f"SQL:"
        )

        # Create progress indicators
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        # Step 1: Generate SQL
        status_text.text("🤖 Generating SQL query...")
        progress_bar.progress(25)
        
        # Call Ollama API with optimized settings for speed
        ollama_url = "http://localhost:11434/api/generate"
        payload = {
            "model": SPEED_CONFIG["model"],
            "prompt": prompt,
            "stream": SPEED_CONFIG["enable_streaming"],
            "options": {
                "temperature": SPEED_CONFIG["temperature"],
                "top_p": SPEED_CONFIG["top_p"],
                "top_k": SPEED_CONFIG["top_k"],
                "num_predict": SPEED_CONFIG["max_tokens"],
                "stop": ["```", "---", "\n\n\n"]  # Stop at common SQL endings
            }
        }
        
        try:
            response = requests.post(ollama_url, json=payload)
            sql_query = response.json().get("response", "").strip()
            
            # Clean up SQL Server syntax - remove backticks and fix common issues
            import re
            
            # Remove any explanatory text before/after SQL
            sql_query = sql_query.strip()
            
            # Remove common explanatory prefixes
            sql_query = re.sub(r'^(Here\'s|Here is|This|The SQL query is|SQL query:|Query:)\s*', '', sql_query, flags=re.IGNORECASE)
            
            # Remove markdown code blocks
            sql_query = re.sub(r'^```sql\s*', '', sql_query, flags=re.IGNORECASE)
            sql_query = re.sub(r'^```\s*', '', sql_query)
            sql_query = re.sub(r'\s*```$', '', sql_query)
            
            # Remove backticks around the entire query
            if sql_query.startswith('`') and sql_query.endswith('`'):
                sql_query = sql_query[1:-1]
            
            # Remove square brackets around the entire query
            if sql_query.startswith('[') and sql_query.endswith(']'):
                sql_query = sql_query[1:-1]
            
            # Replace backticks around identifiers with square brackets
            sql_query = re.sub(r'`([^`]+)`', r'[\1]', sql_query)
            
            # Extract only the first SQL statement if multiple lines
            lines = sql_query.split('\n')
            sql_lines = []
            for line in lines:
                line = line.strip()
                if line and not line.startswith('--') and not line.lower().startswith('note:') and not line.lower().startswith('explanation:'):
                    sql_lines.append(line)
                elif sql_lines:  # Stop at first explanatory text after SQL started
                    break
            
            sql_query = ' '.join(sql_lines).strip()
            
            # Debug: Show generated SQL
            st.subheader("🔍 Generated SQL (Debug)")
            st.code(sql_query, language="sql")
            
            progress_bar.progress(50)
            status_text.text("🔍 Executing SQL query...")
            
            # Execute the generated SQL query
            try:
                # Create a fresh connection to ensure proper database context
                server = st.session_state.server_info["server"]
                port = st.session_state.server_info["port"]
                username = st.session_state.server_info["username"]
                password = st.session_state.server_info["password"]
                
                port_str = f",{port}" if port else ""
                conn_str = f"DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={server}{port_str};DATABASE={database_name};UID={username};PWD={password}"
                
                query_conn = pyodbc.connect(conn_str)
                cursor = query_conn.cursor()
                
                cursor.execute(sql_query)
                result_rows = cursor.fetchall()
                result_columns = [desc[0] for desc in cursor.description]

                # Format result as a string
                result_str = "\t".join(result_columns) + "\n"
                for row in result_rows:
                    result_str += "\t".join(str(item) for item in row) + "\n"
                
                # Close the query connection
                query_conn.close()
                
                progress_bar.progress(75)
                status_text.text("💡 Generating summary...")
                
                # Generate human-readable summary using Ollama with optimized settings
                summary_prompt = (
                    f"Question: {user_question}\n"
                    f"Database: {database_name}\n"
                    f"Table: {table_name}\n"
                    f"SQL Result:\n{result_str}\n"
                    "Summarize the result above in one sentence for a non-technical user."
                )
                summary_payload = {
                    "model": SPEED_CONFIG["model"],
                    "prompt": summary_prompt,
                    "stream": SPEED_CONFIG["enable_streaming"],
                    "options": {
                        "temperature": SPEED_CONFIG["temperature"],
                        "top_p": SPEED_CONFIG["top_p"],
                        "top_k": SPEED_CONFIG["top_k"],
                        "num_predict": SPEED_CONFIG["summary_max_tokens"],
                        "stop": ["\n", ".", "---"]
                    }
                }
                summary_response = requests.post(ollama_url, json=summary_payload)
                summary_text = summary_response.json().get("response", "").strip()
                
                progress_bar.progress(100)
                status_text.text("✅ Complete!")
                
                # Save to history with context
                st.session_state.qa_history.append({
                    "question": user_question,
                    "sql": sql_query,
                    "result": result_str,
                    "summary": summary_text,
                    "database": database_name,
                    "table": table_name,
                    "timestamp": datetime.now()
                })
                
                # Clear the progress indicators
                time.sleep(1)
                progress_bar.empty()
                status_text.empty()
                
                # Show success message
                st.success("🎉 Question processed successfully!")
                st.rerun()
                
            except Exception as e:
                st.session_state.qa_history.append({
                    "question": user_question,
                    "sql": sql_query,
                    "result": "",
                    "summary": f"Error executing SQL: {str(e)}",
                    "database": database_name,
                    "table": table_name,
                    "timestamp": datetime.now()
                })
                progress_bar.empty()
                status_text.empty()
                st.error(f"❌ Error executing SQL: {str(e)}")
                
        except Exception as e:
            progress_bar.empty()
            status_text.empty()
            st.error(f"❌ Error generating SQL: {str(e)}")

