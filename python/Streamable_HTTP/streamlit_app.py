"""
Streamlit UI for Cosmos DB Query Assistant
Interactive web interface for querying Cosmos DB via the intelligent MCP client
"""

import streamlit as st
import asyncio
import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional
import pandas as pd

# Add the current directory to path to import cosmos_client
sys.path.insert(0, str(Path(__file__).parent))

from client import CosmosClient, Settings

# ============================================================================
# PAGE CONFIG
# ============================================================================
st.set_page_config(
    page_title="Cosmos DB Query Assistant",
    page_icon="🗄️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================================
# CUSTOM CSS
# ============================================================================
st.markdown("""
<style>
    .stAlert > div {
        padding: 0.5rem 1rem;
    }
    .query-box {
        background-color: #f0f2f6;
        border-radius: 5px;
        padding: 15px;
        margin: 10px 0;
    }
    .metric-card {
        background-color: #ffffff;
        border: 1px solid #e0e0e0;
        border-radius: 8px;
        padding: 20px;
        margin: 10px 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .step-container {
        background-color: #f8f9fa;
        border-left: 3px solid #4CAF50;
        padding: 10px;
        margin: 5px 0;
        border-radius: 3px;
    }
    .error-container {
        background-color: #ffebee;
        border-left: 3px solid #f44336;
        padding: 10px;
        margin: 5px 0;
        border-radius: 3px;
    }
    .success-container {
        background-color: #e8f5e9;
        border-left: 3px solid #4CAF50;
        padding: 10px;
        margin: 5px 0;
        border-radius: 3px;
    }
</style>
""", unsafe_allow_html=True)

# ============================================================================
# SESSION STATE INITIALIZATION
# ============================================================================
def initialize_session_state():
    """Initialize all session state variables"""
    if 'client' not in st.session_state:
        st.session_state.client = None
    if 'connected' not in st.session_state:
        st.session_state.connected = False
    if 'query_history' not in st.session_state:
        st.session_state.query_history = []
    if 'current_response' not in st.session_state:
        st.session_state.current_response = None
    if 'schema_cache' not in st.session_state:
        st.session_state.schema_cache = None
    if 'show_intermediate' not in st.session_state:
        st.session_state.show_intermediate = False

initialize_session_state()

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================
def parse_json_response(response_text: str) -> Optional[Dict]:
    """Try to parse JSON from response text"""
    try:
        return json.loads(response_text)
    except:
        return None

def extract_table_data(response_text: str) -> Optional[pd.DataFrame]:
    """Extract table data from JSON response"""
    data = parse_json_response(response_text)
    if data and isinstance(data, dict):
        if 'results' in data and isinstance(data['results'], list) and data['results']:
            try:
                return pd.DataFrame(data['results'])
            except:
                pass
        if 'documents' in data and isinstance(data['documents'], list) and data['documents']:
            try:
                return pd.DataFrame(data['documents'])
            except:
                pass
    return None

def format_timestamp(ts: Optional[str] = None) -> str:
    """Format timestamp for display"""
    if ts:
        return datetime.fromisoformat(ts).strftime("%Y-%m-%d %H:%M:%S")
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def add_to_history(query: str, response: Dict[str, Any]):
    """Add query and response to history"""
    st.session_state.query_history.insert(0, {
        'timestamp': datetime.now().isoformat(),
        'query': query,
        'response': response
    })
    # Keep only last 50 queries
    if len(st.session_state.query_history) > 50:
        st.session_state.query_history = st.session_state.query_history[:50]

async def connect_client(config: Settings) -> bool:
    """Connect to the Cosmos DB client"""
    try:
        client = CosmosClient(config)
        await client.connect()
        st.session_state.client = client
        st.session_state.connected = True
        return True
    except Exception as e:
        st.error(f"❌ Connection failed: {str(e)}")
        return False

async def execute_query(query: str) -> Dict[str, Any]:
    """Execute a query using the connected client"""
    if not st.session_state.client or not st.session_state.connected:
        return {
            'text': 'Error: Not connected to Cosmos DB',
            'intermediate_steps': [],
            'elapsed_sec': 0.0
        }
    
    try:
        response = await st.session_state.client.ainvoke(query)
        return response
    except Exception as e:
        return {
            'text': f'Error executing query: {str(e)}',
            'intermediate_steps': [],
            'elapsed_sec': 0.0
        }

# ============================================================================
# SIDEBAR - CONNECTION & SETTINGS
# ============================================================================
with st.sidebar:
    st.title("🗄️ Cosmos DB Assistant")
    st.markdown("---")
    
    # Connection Status
    if st.session_state.connected:
        st.success("✅ Connected")
        if st.button("🔌 Disconnect", use_container_width=True):
            st.session_state.client = None
            st.session_state.connected = False
            st.rerun()
    else:
        st.warning("⚠️ Not Connected")
    
    st.markdown("---")
    st.subheader("⚙️ Configuration")
    
    # Connection Settings
    with st.expander("🔗 Connection Settings", expanded=not st.session_state.connected):
        azure_endpoint = st.text_input(
            "Azure OpenAI Endpoint",
            value=st.secrets.get("AZURE_OPENAI_ENDPOINT", ""),
            type="password",
            help="Your Azure OpenAI endpoint URL"
        )
        
        azure_api_key = st.text_input(
            "Azure OpenAI API Key",
            value=st.secrets.get("AZURE_OPENAI_API_KEY", ""),
            type="password",
            help="Your Azure OpenAI API key"
        )
        
        azure_deployment = st.text_input(
            "Azure Deployment",
            value=st.secrets.get("AZURE_OPENAI_DEPLOYMENT", "gpt-4o"),
            help="Your Azure OpenAI deployment name"
        )
        
        mcp_url = st.text_input(
            "MCP Server URL",
            value="http://localhost:8000/mcp",
            help="URL of the MCP server"
        )
        
        if st.button("🔌 Connect", use_container_width=True, disabled=st.session_state.connected):
            if not azure_endpoint or not azure_api_key:
                st.error("Please provide Azure OpenAI credentials")
            else:
                with st.spinner("Connecting..."):
                    config = Settings(
                        azure_endpoint=azure_endpoint,
                        azure_api_key=azure_api_key,
                        azure_deployment=azure_deployment,
                        mcp_url=mcp_url
                    )
                    success = asyncio.run(connect_client(config))
                    if success:
                        st.success("✅ Connected successfully!")
                        st.rerun()
    
    # Agent Settings
    with st.expander("🤖 Agent Settings"):
        max_iterations = st.slider(
            "Max Iterations",
            min_value=1,
            max_value=10,
            value=4,
            help="Maximum number of agent iterations"
        )
        
        default_top_n = st.slider(
            "Default TOP N",
            min_value=10,
            max_value=500,
            value=50,
            step=10,
            help="Default number of results to return"
        )
        
        enforce_latest = st.checkbox(
            "Enforce Latest Guard",
            value=False,
            help="Add c.latest = 0 filter to all queries"
        )
        
        location_fields = st.text_input(
            "Location Fallback Fields",
            value="City,Region,Area",
            help="Comma-separated list of location fields for fallback (priority order)"
        )
        
        if st.button("💾 Apply Settings", use_container_width=True):
            if st.session_state.client:
                st.session_state.client.cfg.max_iterations = max_iterations
                st.session_state.client.cfg.default_top_n = default_top_n
                st.session_state.client.cfg.enforce_latest_guard = enforce_latest
                st.session_state.client.cfg.location_fallback_fields = [
                    f.strip() for f in location_fields.split(',') if f.strip()
                ]
                st.success("✅ Settings applied!")
    
    # Display Options
    st.markdown("---")
    st.subheader("👁️ Display Options")
    st.session_state.show_intermediate = st.checkbox(
        "Show Intermediate Steps",
        value=st.session_state.show_intermediate,
        help="Display agent's reasoning steps"
    )
    
    show_raw_json = st.checkbox(
        "Show Raw JSON",
        value=False,
        help="Display raw JSON responses"
    )
    
    # Quick Actions
    st.markdown("---")
    st.subheader("⚡ Quick Actions")
    
    if st.button("📋 Get Schema", use_container_width=True, disabled=not st.session_state.connected):
        with st.spinner("Fetching schema..."):
            response = asyncio.run(execute_query("Describe the container schema"))
            st.session_state.current_response = response
            st.session_state.schema_cache = response
            st.rerun()
    
    if st.button("📊 Count Records", use_container_width=True, disabled=not st.session_state.connected):
        with st.spinner("Counting records..."):
            response = asyncio.run(execute_query("How many documents are in the container?"))
            st.session_state.current_response = response
            st.rerun()
    
    if st.button("🔍 Sample Data", use_container_width=True, disabled=not st.session_state.connected):
        with st.spinner("Fetching samples..."):
            response = asyncio.run(execute_query("Show me 5 sample documents"))
            st.session_state.current_response = response
            st.rerun()
    
    # Clear History
    st.markdown("---")
    if st.button("🗑️ Clear History", use_container_width=True):
        st.session_state.query_history = []
        st.session_state.current_response = None
        st.success("History cleared!")
        st.rerun()

# ============================================================================
# MAIN CONTENT
# ============================================================================
st.title("🗄️ Cosmos DB Query Assistant")
st.markdown("Ask questions about your data in natural language")

# Connection Warning
if not st.session_state.connected:
    st.warning("⚠️ Please connect to Cosmos DB using the sidebar configuration")
    st.info("👈 Click on the sidebar to configure your connection settings")
    st.stop()

# ============================================================================
# QUERY INPUT SECTION
# ============================================================================
st.markdown("### 💬 Ask a Question")

# Example queries
with st.expander("💡 Example Queries", expanded=False):
    examples = [
        "How many documents are in the container?",
        "Show me 10 sample documents",
        "What fields are available in the schema?",
        "Count documents where Status = 'Active'",
        "Find all records from last month",
        "List all distinct values for City field",
        "Show top 20 documents ordered by price",
    ]
    
    cols = st.columns(2)
    for i, example in enumerate(examples):
        col = cols[i % 2]
        if col.button(f"📝 {example}", key=f"example_{i}", use_container_width=True):
            st.session_state.current_query = example

# Query input
query_input = st.text_area(
    "Enter your query:",
    value=st.session_state.get('current_query', ''),
    height=100,
    placeholder="E.g., Show me all active properties in Miami...",
    key="query_input_area"
)

col1, col2, col3 = st.columns([2, 1, 1])

with col1:
    execute_button = st.button("🚀 Execute Query", type="primary", use_container_width=True)

with col2:
    if st.button("🔄 Clear", use_container_width=True):
        st.session_state.current_query = ""
        st.session_state.current_response = None
        st.rerun()

with col3:
    if st.button("📋 Copy SQL", use_container_width=True, disabled=True):
        st.info("SQL will be available after execution")

# Execute query
if execute_button and query_input.strip():
    with st.spinner("🔍 Processing your query..."):
        response = asyncio.run(execute_query(query_input))
        st.session_state.current_response = response
        add_to_history(query_input, response)

# ============================================================================
# RESPONSE DISPLAY SECTION
# ============================================================================
if st.session_state.current_response:
    response = st.session_state.current_response
    
    st.markdown("---")
    st.markdown("### 📊 Results")
    
    # Metrics row
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("⏱️ Execution Time", f"{response.get('elapsed_sec', 0):.2f}s")
    
    with col2:
        steps_count = len(response.get('intermediate_steps', []))
        st.metric("🔧 Agent Steps", steps_count)
    
    with col3:
        # Try to extract result count
        result_text = response.get('text', '')
        data = parse_json_response(result_text)
        if data and isinstance(data, dict):
            count = data.get('count', 0)
            st.metric("📝 Results", count)
        else:
            st.metric("📝 Status", "✅ Complete")
    
    # Main response
    st.markdown("#### 💡 Answer")
    
    # Try to parse as JSON and display as table
    df = extract_table_data(response.get('text', ''))
    
    if df is not None and not df.empty:
        st.success(f"Found {len(df)} records")
        
        # Display options
        col1, col2 = st.columns([3, 1])
        with col1:
            display_mode = st.radio(
                "Display as:",
                ["Table", "JSON", "Columns"],
                horizontal=True,
                key="display_mode"
            )
        with col2:
            if st.button("📥 Download CSV", use_container_width=True):
                csv = df.to_csv(index=False)
                st.download_button(
                    label="💾 Save CSV",
                    data=csv,
                    file_name=f"cosmos_query_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv",
                    use_container_width=True
                )
        
        if display_mode == "Table":
            st.dataframe(df, use_container_width=True, height=400)
        elif display_mode == "JSON":
            st.json(df.to_dict(orient='records'))
        else:  # Columns
            selected_columns = st.multiselect(
                "Select columns to display:",
                options=df.columns.tolist(),
                default=df.columns.tolist()[:5] if len(df.columns) > 5 else df.columns.tolist()
            )
            if selected_columns:
                st.dataframe(df[selected_columns], use_container_width=True, height=400)
    else:
        # Display as text
        st.markdown(f'<div class="success-container">{response.get("text", "")}</div>', 
                   unsafe_allow_html=True)
    
    # Show raw JSON if enabled
    if show_raw_json:
        with st.expander("🔍 Raw JSON Response"):
            st.json(response.get('text', ''))
    
    # Intermediate Steps
    if st.session_state.show_intermediate and response.get('intermediate_steps'):
        st.markdown("---")
        st.markdown("#### 🔧 Agent Reasoning Steps")
        
        for i, step in enumerate(response['intermediate_steps'], 1):
            with st.expander(f"Step {i}", expanded=False):
                try:
                    if isinstance(step, tuple) and len(step) == 2:
                        action, observation = step
                        
                        col1, col2 = st.columns([1, 2])
                        with col1:
                            st.markdown("**Action:**")
                            st.code(getattr(action, 'tool', str(action)))
                        
                        with col2:
                            st.markdown("**Input:**")
                            tool_input = getattr(action, 'tool_input', '')
                            if isinstance(tool_input, dict):
                                st.json(tool_input)
                            else:
                                st.code(str(tool_input))
                        
                        st.markdown("**Observation:**")
                        obs_str = str(observation)[:1000]
                        
                        # Try to parse as JSON for better display
                        try:
                            obs_json = json.loads(observation)
                            st.json(obs_json)
                        except:
                            st.code(obs_str)
                    else:
                        st.code(str(step))
                except Exception as e:
                    st.error(f"Error displaying step: {str(e)}")
                    st.code(str(step))

# ============================================================================
# QUERY HISTORY SECTION
# ============================================================================
if st.session_state.query_history:
    st.markdown("---")
    st.markdown("### 📜 Query History")
    
    # Filter options
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        search_term = st.text_input("🔍 Search history", placeholder="Filter queries...")
    with col2:
        show_count = st.selectbox("Show entries", [10, 25, 50], index=0)
    with col3:
        sort_order = st.selectbox("Sort by", ["Newest", "Oldest"])
    
    # Filter and sort history
    filtered_history = st.session_state.query_history
    if search_term:
        filtered_history = [
            h for h in filtered_history 
            if search_term.lower() in h['query'].lower()
        ]
    
    if sort_order == "Oldest":
        filtered_history = list(reversed(filtered_history))
    
    # Display history
    for i, item in enumerate(filtered_history[:show_count]):
        with st.expander(
            f"🕒 {format_timestamp(item['timestamp'])} - {item['query'][:80]}...",
            expanded=False
        ):
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.markdown(f"**Query:** {item['query']}")
                st.markdown(f"**Response:** {item['response'].get('text', '')[:200]}...")
                st.caption(f"⏱️ {item['response'].get('elapsed_sec', 0):.2f}s")
            
            with col2:
                if st.button("🔄 Rerun", key=f"rerun_{i}", use_container_width=True):
                    st.session_state.current_query = item['query']
                    st.rerun()
                
                if st.button("📋 Copy", key=f"copy_{i}", use_container_width=True):
                    st.code(item['query'])

# ============================================================================
# FOOTER
# ============================================================================
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666; padding: 20px;'>
    <p>🗄️ Cosmos DB Query Assistant | Powered by Azure OpenAI & MCP</p>
    <p style='font-size: 0.8em;'>Built with Streamlit • ReAct Agent • LangChain</p>
</div>
""", unsafe_allow_html=True)