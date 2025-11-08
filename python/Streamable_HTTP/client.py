"""
Intelligent Cosmos DB Client (ReAct + MCP) — Generalized
- Streamable-HTTP Cosmos MCP client (configurable database & container)
- ReAct agent (hub: hwchase17/react) with AgentExecutor + strict guardrails
- Safe wrappers:
    • query_cosmos  -> strips ```sql fences + injects c.latest = 0 (if column exists)
    • count_documents -> equality-only; SQL COUNT fallback for LIKE/range/date
    • describe_container -> no-arg shim for JSON-schema tools
- Skips LLM for greetings/acks
- Uses early_stopping_method='force'
- Sequential location fallback (configurable field cascade)
"""

import os
import asyncio
import json
import logging
import re
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
from dotenv import load_dotenv
load_dotenv()

from langchain import hub
from langchain.agents import create_react_agent, AgentExecutor
from langchain_core.prompts import PromptTemplate
from langchain_core.tools import Tool
from langchain_openai import AzureChatOpenAI
from langchain_mcp_adapters.client import MultiServerMCPClient

# ---------------- Logging ----------------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("cosmos_client")
logger.setLevel(logging.INFO)

# ---------------- Config ----------------
@dataclass
class Settings:
    # Azure OpenAI (env overrides)
    azure_endpoint: str = os.getenv("AZURE_OPENAI_ENDPOINT", "https://YOUR_AZURE_RESOURCE.openai.azure.com/")
    azure_deployment: str = os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4o")
    azure_api_key: str = os.getenv("AZURE_OPENAI_API_KEY", "REPLACE_ME")
    azure_api_version: str = os.getenv("AZURE_OPENAI_API_VERSION", "2024-05-01-preview")

    # MCP (streamable HTTP)
    mcp_url: str = os.getenv("MCP_URL", "http://localhost:8000/mcp")
    connect_timeout: int = 10

    # Agent controls
    max_iterations: int = 4
    agent_timeout: int = 60
    tool_timeout: int = 45

    # Behavior
    default_top_n: int = 50
    enable_sql_count_fallback: bool = True
    enforce_latest_guard: bool = False  # Set to True if your data has a 'latest' field for versioning

    # Location fallback fields (ordered by priority)
    # Customize these based on your schema
    location_fallback_fields: List[str] = field(default_factory=lambda: ["City", "Region", "Area", "District"])
    
    # Context
    today: str = datetime.now().strftime("%Y-%m-%d")
    current_month: str = datetime.now().strftime("%B %Y")

# ---------------- Helpers ----------------
GREETING_PAT = re.compile(
    r'^(hi|hello|hey|greetings|good\s+(morning|afternoon|evening)|thanks?|thank\s+you|ok|okay|alright|bye|goodbye)[\s!.]*$',
    re.IGNORECASE,
)

FENCE_RE = re.compile(r"^\s*```(?:sql)?\s*|\s*```\s*$", re.IGNORECASE | re.MULTILINE)

def strip_sql_fences(s: str) -> str:
    if not isinstance(s, str):
        return s
    return FENCE_RE.sub("", s).strip()

def parse_temporal_window(text: str, today_iso: str) -> Optional[Tuple[str, str]]:
    today = datetime.fromisoformat(today_iso)
    t = text.lower()
    if "this month" in t:
        start = today.replace(day=1)
        end = (start.replace(day=28) + timedelta(days=4)).replace(day=1)
        return start.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d")
    if "last month" in t:
        first_this = today.replace(day=1)
        end = first_this
        start = (first_this - timedelta(days=1)).replace(day=1)
        return start.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d")
    if "last year" in t:
        start = today.replace(month=1, day=1, year=today.year - 1)
        end = today.replace(month=1, day=1, year=today.year)
        return start.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d")
    if "past 30 days" in t or "last 30 days" in t:
        start = today - timedelta(days=30)
        end = today + timedelta(days=1)
        return start.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d")
    return None

def has_keywords(text: str, words: List[str]) -> bool:
    tl = text.lower()
    return any(w in tl for w in words)

def inject_latest_guard(sql: str, enforce: bool) -> str:
    """Inject c.latest = 0 clause if enforce is True and not already present."""
    if not enforce:
        return sql
    if re.search(r"\bc\.latest\s*=\s*0\b", sql, flags=re.IGNORECASE):
        return sql
    if re.search(r"\bwhere\b", sql, flags=re.IGNORECASE):
        return re.sub(r"(\bwhere\b)", r"\1 c.latest = 0 AND", sql, count=1, flags=re.IGNORECASE)
    parts = re.split(r"(\border\s+by\b|\boffset\b|\blimit\b)", sql, flags=re.IGNORECASE)
    if len(parts) > 1:
        return f"{parts[0].rstrip()} WHERE c.latest = 0 " + "".join(parts[1:])
    return sql.rstrip() + " WHERE c.latest = 0"

def clean_filter_keys(d: Dict[str, Any]) -> Dict[str, Any]:
    out = {}
    for k, v in d.items():
        if not isinstance(k, str):
            raise ValueError("Filter keys must be strings")
        ck = k.strip().strip('"').strip("'")
        if ck.startswith("c."):
            ck = ck[2:]
        out[ck] = v
    return out

def has_operatorish_key(key: str) -> bool:
    l = key.lower()
    if " " in l:
        return True
    for tok in [" like", ">", "<", ">=", "<=", "!=", " between ", " in "]:
        if tok in l:
            return True
    return False

def to_sql_count_from_eq_filters(filters: Dict[str, Any], enforce_latest: bool) -> str:
    clauses = []
    if enforce_latest:
        clauses.append("c.latest = 0")
    for k, v in filters.items():
        if k == "latest":
            continue
        if isinstance(v, str):
            v = v.replace("'", "''")
            clauses.append(f"c.{k} = '{v}'")
        else:
            clauses.append(f"c.{k} = {json.dumps(v)}")
    where_clause = " AND ".join(clauses) if clauses else "1=1"
    return f"SELECT VALUE COUNT(1) FROM c WHERE {where_clause}"

def obs_zero(observation: Any) -> bool:
    """True if tool observation represents zero results."""
    try:
        obj = observation
        if isinstance(obj, str):
            obj = json.loads(obj)
        if isinstance(obj, dict):
            if "results" in obj and isinstance(obj["results"], list):
                if len(obj["results"]) == 1 and obj["results"][0] == 0:
                    return True
                if len(obj["results"]) == 0:
                    return True
            if obj.get("count") == 0:
                return True
    except Exception:
        pass
    return False

def obs_count(observation: Any) -> Optional[int]:
    """Extract integer count from COUNT or listings observation."""
    try:
        obj = observation
        if isinstance(obj, str):
            obj = json.loads(obj)
        if isinstance(obj, dict):
            if isinstance(obj.get("results"), list):
                # COUNT result style: [N]
                if len(obj["results"]) == 1 and isinstance(obj["results"][0], (int, float)):
                    return int(obj["results"][0])
                # listings style: number of rows
                return len(obj["results"])
            if isinstance(obj.get("count"), int):
                return obj["count"]
    except Exception:
        return None
    return None

# --- Sequential location fallback helpers ---
def extract_location_term(sql: str, field: str) -> Optional[str]:
    """Extract the search term from c.<field> = 'X' or c.<field> LIKE '%X%'."""
    # Try equality first
    eq_re = re.compile(rf"(c\.{field}\s*=\s*')([^']+)(')", re.IGNORECASE)
    m = eq_re.search(sql)
    if m:
        return m.group(2).strip()
    # Try LIKE
    like_re = re.compile(rf"(c\.{field}\s+LIKE\s*'%)([^']+)(%')", re.IGNORECASE)
    m = like_re.search(sql)
    if m:
        return m.group(2).strip()
    return None

def replace_location_field(sql: str, old_field: str, new_field: str, term: str) -> str:
    """Replace c.<old_field> predicate with c.<new_field> LIKE '%term%'."""
    # Try equality pattern
    eq_re = re.compile(rf"(c\.{old_field}\s*=\s*')([^']+)(')", re.IGNORECASE)
    m = eq_re.search(sql)
    if m:
        like_clause = f"c.{new_field} LIKE '%{term}%'"
        return sql[:m.start()] + like_clause + sql[m.end():]
    # Try LIKE pattern
    like_re = re.compile(rf"(c\.{old_field}\s+LIKE\s*'%)([^']+)(%')", re.IGNORECASE)
    m = like_re.search(sql)
    if m:
        like_clause = f"c.{new_field} LIKE '%{term}%'"
        return sql[:m.start()] + like_clause + sql[m.end():]
    return sql

# ---------------- Client ----------------
class CosmosClient:
    def __init__(self, cfg: Settings):
        self.cfg = cfg
        self.llm: Optional[AzureChatOpenAI] = None
        self.mcp: Optional[MultiServerMCPClient] = None
        self.agent_executor: Optional[AgentExecutor] = None
        self._orig_query = None
        self._orig_count = None
        self.tools: List[Tool] = []
        self.schema_cache: Optional[Dict[str, Any]] = None

    # -------------- Tool wrappers --------------
    def _wrap_query_cosmos(self) -> Tool:
        async def _run(*args, **kwargs):
            query = None
            if args and len(args) == 1 and isinstance(args[0], str):
                query = args[0]
            else:
                query = kwargs.get("query", "")

            if not isinstance(query, str) or not query.strip():
                raise ValueError("query_cosmos expects a non-empty SQL string")

            query = strip_sql_fences(query)
            query = inject_latest_guard(query, self.cfg.enforce_latest_guard)

            try:
                return await self._orig_query.ainvoke({"query": query})
            except Exception as e:
                raise ValueError(f"query_cosmos failed: {e}")

        return Tool.from_function(
            name="query_cosmos",
            description="Execute Cosmos SQL. Strips ```sql fences and optionally enforces c.latest = 0.",
            func=lambda *a, **kw: asyncio.run(_run(*a, **kw)),
            coroutine=_run,
        )

    def _wrap_count_documents(self) -> Tool:
        async def _run(*args, **kwargs):
            # Gather raw
            raw = None
            if args and len(args) == 1:
                raw = args[0]
            elif "filters" in kwargs:
                raw = kwargs["filters"]
            elif "filter" in kwargs:
                raw = kwargs["filter"]
            else:
                raw = kwargs

            if isinstance(raw, str):
                try:
                    raw = json.loads(raw)
                except Exception:
                    raw = {}

            if isinstance(raw, dict):
                if "filters" in raw and isinstance(raw["filters"], dict):
                    raw = raw["filters"]
                elif "filter" in raw and isinstance(raw["filter"], dict):
                    raw = raw["filter"]
            else:
                raw = {}

            if not isinstance(raw, dict):
                raise ValueError("count_documents expects a filters dict or JSON string")

            clean = clean_filter_keys(raw)

            for k in list(clean.keys()):
                if has_operatorish_key(k):
                    if self.cfg.enable_sql_count_fallback and self._orig_query:
                        sql = to_sql_count_from_eq_filters(
                            {"latest": 0} if self.cfg.enforce_latest_guard else {},
                            self.cfg.enforce_latest_guard
                        )
                        return await self._orig_query.ainvoke({"query": sql})
                    raise ValueError(f"count_documents invalid key '{k}' (operators not allowed)")

            if self.cfg.enforce_latest_guard and "latest" not in clean:
                clean["latest"] = 0

            try:
                return await self._orig_count.ainvoke({"filters": clean})
            except Exception as e:
                if self.cfg.enable_sql_count_fallback and self._orig_query:
                    try:
                        sql = to_sql_count_from_eq_filters(clean, self.cfg.enforce_latest_guard)
                        return await self._orig_query.ainvoke({"query": sql})
                    except Exception as inner:
                        raise ValueError(f"count_documents failed; SQL COUNT fallback failed: {inner}") from e
                raise ValueError(f"count_documents failed: {e}")

        return Tool.from_function(
            name="count_documents",
            description=("STRICT equality-only counter. Accepts {'filters': {...}} / {'filter': {...}} / dict / JSON. "
                         "For LIKE/range/date, uses SQL COUNT via query_cosmos."),
            func=lambda *a, **kw: asyncio.run(_run(*a, **kw)),
            coroutine=_run,
        )

    def _wrap_noarg_json_tool(self, name: str, orig_tool) -> Tool:
        async def _run(*args, **kwargs):
            try:
                return await orig_tool.ainvoke({})
            except Exception as e:
                raise ValueError(f"{name} failed: {e}")

        return Tool.from_function(
            name=name,
            description=f"{name} (no-arg). Accepts no parameters.",
            func=lambda *a, **kw: asyncio.run(_run(*a, **kw)),
            coroutine=_run,
        )

    # -------------- Connect / setup --------------
    async def connect(self):
        if "YOUR_AZURE_RESOURCE" in self.cfg.azure_endpoint or self.cfg.azure_api_key == "REPLACE_ME":
            raise RuntimeError(
                "Azure settings are not configured. Set AZURE_OPENAI_ENDPOINT / AZURE_OPENAI_API_KEY / "
                "AZURE_OPENAI_DEPLOYMENT / AZURE_OPENAI_API_VERSION, or edit Settings()."
            )

        self.llm = AzureChatOpenAI(
            azure_endpoint=self.cfg.azure_endpoint,
            api_key=self.cfg.azure_api_key,
            api_version=self.cfg.azure_api_version,
            azure_deployment=self.cfg.azure_deployment,
            temperature=0,
            timeout=self.cfg.agent_timeout,
            max_retries=1,
        )

        self.mcp = MultiServerMCPClient({
            "cosmos-server": {"url": self.cfg.mcp_url, "transport": "streamable_http"}
        })
        if hasattr(self.mcp, "start"):
            await asyncio.wait_for(self.mcp.start(), timeout=self.cfg.connect_timeout)

        base_tools = await asyncio.wait_for(self.mcp.get_tools(), timeout=self.cfg.connect_timeout)
        tmap = {t.name: t for t in base_tools}
        self._orig_query = tmap.get("query_cosmos")
        self._orig_count = tmap.get("count_documents")

        wrapped: List[Tool] = []
        for t in base_tools:
            if t.name == "query_cosmos" and self._orig_query:
                wrapped.append(self._wrap_query_cosmos())
            elif t.name == "count_documents" and self._orig_count:
                wrapped.append(self._wrap_count_documents())
            elif t.name == "describe_container":
                wrapped.append(self._wrap_noarg_json_tool("describe_container", t))
            else:
                wrapped.append(t)
        self.tools = wrapped

        react_prompt = hub.pull("hwchase17/react")
        system_rules = self._system_rules_block()

        if isinstance(react_prompt, PromptTemplate):
            react_prompt = PromptTemplate(
                input_variables=react_prompt.input_variables,
                template=system_rules + "\n\n" + react_prompt.template,
                template_format=getattr(react_prompt, "template_format", "f-string"),
                partial_variables=getattr(react_prompt, "partial_variables", None) or {},
            )
        else:
            react_prompt = PromptTemplate(
                input_variables=["input", "agent_scratchpad", "tools", "tool_names"],
                template=system_rules + "\n\n{input}\n\n{agent_scratchpad}",
            )

        agent = create_react_agent(llm=self.llm, tools=self.tools, prompt=react_prompt)
        self.agent_executor = AgentExecutor(
            agent=agent,
            tools=self.tools,
            verbose=True,
            max_iterations=self.cfg.max_iterations,
            return_intermediate_steps=True,
            handle_parsing_errors=True,
            early_stopping_method="force",
        )
        logger.info("✓ Connected. Tools loaded: %d", len(self.tools))

    def _system_rules_block(self) -> str:
        latest_rule = ""
        if self.cfg.enforce_latest_guard:
            latest_rule = "- Always enforce `WHERE c.latest = 0` in SQL to get current records only.\n"
        
        return f"""
You are a Cosmos DB data assistant. You help users query and analyze data from their Cosmos DB container.

CRITICAL RULES
{latest_rule}- Do NOT wrap SQL in ``` code fences. Return raw SQL only.
- All column references must use the alias 'c.' (e.g., c.FieldName)

TOOL SELECTION
- Counts with equality-only filters → use count_documents
- Counts with LIKE/range/date → use query_cosmos with: SELECT VALUE COUNT(1) FROM c WHERE ...
- Data retrieval, filters, sorting → use query_cosmos
- Distinct values (one field) → list_distinct_values (if available)
- Schema/sample checks → describe_container or get_sample_documents

COSMOS SQL RULES
- Prefix all columns with c. (e.g., c.id, c.FieldName)
- String comparison: c.FieldName = 'Value' (exact) or c.FieldName LIKE '%Value%' (contains)
- TOP N if user specifies a number; else TOP {self.cfg.default_top_n} for data retrieval
- Default ordering: ORDER BY c.id DESC unless specified otherwise

TEMPORAL INTELLIGENCE
- "Today" = {self.cfg.today}
- "This month" = {self.cfg.current_month}
- Date format: YYYY-MM-DD for date comparisons
- Examples:
  • c.DateField >= '{self.cfg.today}'
  • c.DateField >= 'YYYY-MM-01' AND c.DateField < 'YYYY-MM-01'+1month

VERIFICATION
- After a tool call, sanity check results:
  • If 0 results but query seems valid → suggest relaxing filters or using LIKE instead of =
  • If too many results → suggest refinement or add TOP N
  • If field error occurs → check schema with describe_container and retry with correct field name

EXAMPLE QUERIES
- Count all documents:
  SELECT VALUE COUNT(1) FROM c{' WHERE c.latest = 0' if self.cfg.enforce_latest_guard else ''}

- Get top 10 documents:
  SELECT TOP 10 * FROM c{' WHERE c.latest = 0' if self.cfg.enforce_latest_guard else ''} ORDER BY c.id DESC

- Filter and count:
  SELECT VALUE COUNT(1) FROM c WHERE{' c.latest = 0 AND' if self.cfg.enforce_latest_guard else ''} c.Status = 'Active'
"""

    # -------------- Public API --------------
    async def ainvoke(self, user_query: str) -> Dict[str, Any]:
        if not self.agent_executor:
            raise RuntimeError("Client not connected. Call connect() first.")

        if GREETING_PAT.match(user_query.strip()):
            return {
                "text": "Hi! I can help you query and analyze data from your Cosmos DB. What would you like to explore?",
                "intermediate_steps": [],
                "elapsed_sec": 0.0
            }

        start = time.time()

        hints: List[str] = []
        win = parse_temporal_window(user_query, self.cfg.today)
        if win:
            hints.append(f"(Temporal window: {win[0]} → {win[1]})")
        prefix = (" ".join(hints) + " ").strip()

        result = await self.agent_executor.ainvoke({"input": f"{prefix}{user_query}"})
        output_text = result.get("output", "") or ""
        steps = result.get("intermediate_steps", [])

        # --- Sequential location fallback (configurable fields) ---
        fallback_applied = False
        if len(self.cfg.location_fallback_fields) > 1:
            try:
                last_q = None
                last_obs = None
                for stp in reversed(steps):
                    action, observation = stp
                    if getattr(action, "tool", "") == "query_cosmos":
                        last_q = str(getattr(action, "tool_input", "")).strip()
                        last_obs = observation
                        break

                if last_q and last_obs and obs_zero(last_obs):
                    base_sql = strip_sql_fences(last_q)
                    primary_field = self.cfg.location_fallback_fields[0]
                    
                    # Check if SQL contains the primary location field
                    if re.search(rf"\bc\.{primary_field}\b", base_sql, flags=re.IGNORECASE):
                        term = extract_location_term(base_sql, primary_field)
                        if term:
                            # Try each fallback field in order
                            for fallback_field in self.cfg.location_fallback_fields[1:]:
                                sql_fallback = replace_location_field(base_sql, primary_field, fallback_field, term)
                                sql_fallback = inject_latest_guard(sql_fallback, self.cfg.enforce_latest_guard)
                                
                                obs_fb = await self._orig_query.ainvoke({"query": sql_fallback})
                                steps.append((f"client_fallback_{fallback_field}", {"query": sql_fallback, "observation": obs_fb}))
                                
                                count = obs_count(obs_fb)
                                if isinstance(count, int) and count > 0:
                                    output_text = f"Found {count} records using {fallback_field} LIKE '%{term}%'."
                                    fallback_applied = True
                                    break
            except Exception as e:
                steps.append(("client_fallback_error", str(e)))

        # Gentle retry only if no fallback answer
        if (not fallback_applied) and has_keywords(user_query, ["show", "find", "list", "get", "retrieve"]) and len(output_text.strip()) < 2:
            retry_hint = f"When querying data, add `TOP {self.cfg.default_top_n}` if no limit specified."
            result2 = await self.agent_executor.ainvoke({"input": retry_hint + " " + user_query})
            output_text = result2.get("output", "") or output_text
            steps.extend(result2.get("intermediate_steps", []))

        elapsed = round(time.time() - start, 2)
        return {"text": output_text, "intermediate_steps": steps, "elapsed_sec": elapsed}

# ---------------- CLI ----------------
async def main():
    cfg = Settings()
    client = CosmosClient(cfg)
    print("=" * 66)
    print("Intelligent Cosmos DB Assistant (ReAct + MCP)")
    print("=" * 66)
    try:
        await client.connect()
        print("\n✓ Connected! Ask questions about your data.")
        print("Type 'exit' to quit.\n")
        while True:
            try:
                q = input("You: ").strip()
                if not q:
                    continue
                if q.lower() in {"exit", "quit", "q"}:
                    break
                resp = await client.ainvoke(q)
                print("\nAssistant:\n" + resp["text"])
                if resp["intermediate_steps"]:
                    print("\n— Intermediate Steps —")
                    for i, st in enumerate(resp["intermediate_steps"], 1):
                        try:
                            action, observation = st
                            print(f"[{i}] Action: {getattr(action, 'tool', str(action))}")
                            print(f"    Args:  {getattr(action, 'tool_input', '')}")
                            print(f"    Obs:   {str(observation)[:600]}")
                        except Exception:
                            print(f"[{i}] {st}")
                print(f"\n(time: {resp['elapsed_sec']}s)\n")
            except KeyboardInterrupt:
                print("\nBye!")
                break
    except Exception as e:
        logger.exception("Failed to start: %s", e)

if __name__ == "__main__":
    asyncio.run(main())