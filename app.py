import streamlit as st
import pyodbc
import pandas as pd
import requests
import time
from datetime import datetime

# Page configuration
st.set_page_config(
    page_title="🧠 SQL Natural Language Agent",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 10px;
        margin-bottom: 2rem;
        color: white;
        text-align: center;
    }
    
    .success-box {
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        border-radius: 8px;
        padding: 1rem;
        margin: 1rem 0;
    }
    
    .info-box {
        background-color: #d1ecf1;
        border: 1px solid #bee5eb;
        border-radius: 8px;
        padding: 1rem;
        margin: 1rem 0;
    }
    
    .warning-box {
        background-color: #fff3cd;
        border: 1px solid #ffeaa7;
        border-radius: 8px;
        padding: 1rem;
        margin: 1rem 0;
    }
    
    .error-box {
        background-color: #f8d7da;
        border: 1px solid #f5c6cb;
        border-radius: 8px;
        padding: 1rem;
        margin: 1rem 0;
    }
    
    .table-grid {
        display: grid;
        grid-template-columns: repeat(5, 1fr);
        gap: 10px;
        margin: 1rem 0;
    }
    
    .table-button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 12px;
        cursor: pointer;
        transition: all 0.3s ease;
        text-align: center;
        font-weight: 500;
    }
    
    .table-button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
    }
    
    .table-button.selected {
        background: linear-gradient(135deg, #28a745 0%, #20c997 100%);
        box-shadow: 0 4px 8px rgba(40, 167, 69, 0.3);
    }
    
    .qa-container {
        background: #f8f9fa;
        border-radius: 10px;
        padding: 1.5rem;
        margin: 1rem 0;
        border-left: 4px solid #667eea;
    }
    
    .question-box {
        background: white;
        border-radius: 8px;
        padding: 1rem;
        margin: 1rem 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    .result-box {
        background: white;
        border-radius: 8px;
        padding: 1rem;
        margin: 1rem 0;
        border-left: 4px solid #28a745;
    }
    
    .stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 12px 24px;
        font-weight: 500;
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
    }
    
    .stTextInput > div > div > input {
        border-radius: 8px;
        border: 2px solid #e9ecef;
        padding: 12px;
        font-size: 16px;
    }
    
    .stTextInput > div > div > input:focus {
        border-color: #667eea;
        box-shadow: 0 0 0 0.2rem rgba(102, 126, 234, 0.25);
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
        server = st.text_input("Host (e.g. 127.0.0.1 or SERVER\\INSTANCE)")
        username = st.text_input("Username")
    with col2:
        port = st.text_input("Port (optional)", value="")
        password = st.text_input("Password", type="password")

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

# Step 3: Select database
if "db_list" in st.session_state:
    st.subheader("📦 Select a Database")
    selected_db = st.selectbox("Available Databases", st.session_state.db_list)

    if selected_db:
        st.markdown(f'<div class="info-box">🎯 You selected database: <strong>{selected_db}</strong></div>', unsafe_allow_html=True)
        st.session_state.selected_db = selected_db

if "selected_db" in st.session_state:
    st.subheader(f"📦 Database: `{st.session_state.selected_db}`")

    if st.button("🔄 Load Tables", use_container_width=True):
        with st.spinner("🔄 Loading tables..."):
            server = st.session_state.server_info["server"]
            port = st.session_state.server_info["port"]
            username = st.session_state.server_info["username"]
            password = st.session_state.server_info["password"]
            database = st.session_state.selected_db

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
                    st.markdown('<div class="success-box">✅ Tables loaded successfully!</div>', unsafe_allow_html=True)
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
                else:
                    st.markdown('<div class="warning-box">⚠️ No tables found in this database.</div>', unsafe_allow_html=True)
            except Exception as e:
                st.markdown(f'<div class="error-box">❌ Failed to connect to database: {e}</div>', unsafe_allow_html=True)

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
            
        # Create a button for each table
        selected_table = st.session_state.get("selected_table", None)
        button_text = f"{table}" if table == selected_table else f"{table}"
        button_color = "primary" if table == selected_table else "secondary"
        
        if col.button(button_text, key=f"table_{table}", use_container_width=True, type=button_color):
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
        
        # Display history in reverse chronological order
        for i, qa in enumerate(st.session_state.qa_history[::-1]):
            with st.container():
                st.markdown(f"""
                <div class="qa-container">
                    <div class="question-box">
                        <h4>❓ Question {len(st.session_state.qa_history) - i}</h4>
                        <p><strong>Context:</strong> Database: <code>{qa.get('database', 'N/A')}</code> | Table: <code>{qa.get('table', 'N/A')}</code></p>
                        <p><strong>Q:</strong> {qa['question']}</p>
                    </div>
                    <div class="result-box">
                        <h5>🔍 Generated SQL:</h5>
                        <pre><code>{qa['sql']}</code></pre>
                        <h5>📊 Results:</h5>
                        <pre>{qa['result']}</pre>
                        <h5>💡 Summary:</h5>
                        <p>{qa['summary']}</p>
                        <small>🕒 {qa.get('timestamp', 'N/A').strftime('%Y-%m-%d %H:%M:%S') if hasattr(qa.get('timestamp', ''), 'strftime') else 'N/A'}</small>
                    </div>
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
            f"You are a SQL Server expert. Here is the schema for table '{table_name}' in database '{database_name}' with schema '{schema_name}':\n"
            f"{schema_str}\n"
            f"Write a SQL Server query for this request: {user_question}\n"
            f"Only use columns from the schema above and only reference the table '{database_name}.{schema_name}.{table_name}'."
            f"Only return the SQL query, do not include any explanation."
            f"Make sure to use the correct SQL syntax for SQL Server."
            f"IMPORTANT: Use square brackets [] for identifiers, NOT backticks. For example: [ColumnName] not `ColumnName`."
            f"Do not use any comment or other symbols in the query, just return the SQL code."
        )

        # Create progress indicators
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        # Step 1: Generate SQL
        status_text.text("🤖 Generating SQL query...")
        progress_bar.progress(25)
        
        # Call Ollama API
        ollama_url = "http://localhost:11434/api/generate"
        payload = {
            "model": "llama3",
            "prompt": prompt,
            "stream": False
        }
        
        try:
            response = requests.post(ollama_url, json=payload)
            sql_query = response.json().get("response", "").strip()
            
            # Clean up SQL Server syntax - replace backticks with square brackets
            # Handle paired backticks properly
            import re
            sql_query = re.sub(r'`([^`]+)`', r'[\1]', sql_query)
            
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
                
                # Generate human-readable summary using Ollama
                summary_prompt = (
                    f"Question: {user_question}\n"
                    f"Database: {database_name}\n"
                    f"Table: {table_name}\n"
                    f"SQL Result:\n{result_str}\n"
                    "Summarize the result above in one sentence for a non-technical user."
                )
                summary_payload = {
                    "model": "llama3",
                    "prompt": summary_prompt,
                    "stream": False
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

