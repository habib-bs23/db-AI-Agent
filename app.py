import streamlit as st
import pyodbc
import pandas as pd
import requests

st.title("🧠 SQL Natural Language Agent")

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
    st.subheader("Connect to SQL Server")

    server = st.text_input("Host (e.g. 127.0.0.1 or SERVER\\INSTANCE)")
    port = st.text_input("Port (optional)", value="")
    username = st.text_input("Username")
    password = st.text_input("Password") #, type="password"

    submitted = st.form_submit_button("Connect to Server")

if submitted:
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
            st.success("✅ Connected successfully!")
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
            st.warning("⚠️ No user databases found.")
    except Exception as e:
        st.error(f"❌ Connection failed: {e}")

# Step 3: Select database
if "db_list" in st.session_state:
    st.subheader("Select a Database")
    selected_db = st.selectbox("Available Databases", st.session_state.db_list)

    if selected_db:
        st.success(f"🎯 You selected database: **{selected_db}**")
        st.session_state.selected_db = selected_db

if "selected_db" in st.session_state:
    st.subheader(f"📦 Database: `{st.session_state.selected_db}`")

    if st.button("🔄 Load Tables"):
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
                st.success("✅ Tables loaded!")
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
                st.warning("⚠️ No tables found in this database.")
        except Exception as e:
            st.error(f"❌ Failed to connect to database: {e}")

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
        st.info(f"🎯 **Selected Table:** {st.session_state.selected_table}")
        
        # Load schema for selected table
        if st.session_state.selected_table != st.session_state.get("last_loaded_table", None):
            st.session_state.last_loaded_table = st.session_state.selected_table
            
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
                    st.success(f"✅ Schema loaded for table **{st.session_state.selected_table}** (Schema: **{schema_name}**)")
                else:
                    st.warning(f"No columns found for table {st.session_state.selected_table}")
                    
            except Exception as e:
                st.error(f"Error fetching schema: {str(e)}")

# Step 5: Show schema
if "schema" in st.session_state:
    st.subheader(f"📑 Schema for table `{st.session_state.selected_table}`")
    st.dataframe(st.session_state.schema)

# Step 6: Continuous Q&A with context awareness
if "schema" in st.session_state and "selected_table" in st.session_state:
    st.subheader("Ask questions about your data (continuous Q&A)")
    if "qa_history" not in st.session_state:
        st.session_state.qa_history = []

    # Display current context
    current_db = st.session_state.current_context["database"]
    current_table = st.session_state.current_context["table"]
    st.info(f"🔍 **Current Context:** Database: `{current_db}` | Table: `{current_table}`")

    user_question = st.text_input(
        "Enter your question (e.g., show top 10 customers by revenue)",
        key="nl_question"
    )

    if st.button("Ask", key="ask_button"):
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

        # Call Ollama API
        ollama_url = "http://localhost:11434/api/generate"
        payload = {
            "model": "llama3",
            "prompt": prompt,
            "stream": False
        }
        response = requests.post(ollama_url, json=payload)
        sql_query = response.json().get("response", "").strip()
        
        # Clean up SQL Server syntax - replace backticks with square brackets
        # Handle paired backticks properly
        import re
        sql_query = re.sub(r'`([^`]+)`', r'[\1]', sql_query)
        
        # Debug: Show the generated SQL query
        st.write("**Generated SQL Query:**")
        st.code(sql_query, language="sql")

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

            # Save to history with context
            st.session_state.qa_history.append({
                "question": user_question,
                "sql": sql_query,
                "result": result_str,
                "summary": summary_text,
                "database": database_name,
                "table": table_name,
                "timestamp": pd.Timestamp.now()
            })
        except Exception as e:
            st.session_state.qa_history.append({
                "question": user_question,
                "sql": sql_query,
                "result": "",
                "summary": f"Error executing SQL: {str(e)}",
                "database": database_name,
                "table": table_name,
                "timestamp": pd.Timestamp.now()
            })

    # Display Q&A history with context
    if st.session_state.qa_history:
        st.subheader("📚 Q&A History")
        for qa in st.session_state.qa_history[::-1]:
            # Show context for each Q&A entry
            context_info = f"**Context:** Database: `{qa.get('database', 'N/A')}` | Table: `{qa.get('table', 'N/A')}`"
            st.write(context_info)
            st.write(f"**Q:** {qa['question']}")
            st.write("**SQL Query:**")
            st.code(qa['sql'], language="sql")
            st.write("**Result:**")
            st.text(qa['result'])
            st.write("**Summary:**")
            st.write(qa['summary'])
            st.markdown("---")

# Add a button to clear Q&A history
if "qa_history" in st.session_state and st.session_state.qa_history:
    if st.button("🗑️ Clear Q&A History"):
        st.session_state.qa_history = []
        st.rerun()

