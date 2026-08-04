# ADK Orchestration Documentation

## Overview

The AIFP-AOS system now features a Google ADK (Agent Development Kit) based orchestration system with a "Marketing Manager" root agent that intelligently routes tasks to specialized agents. This replaces the previous hand-rolled static `steps` orchestration with dynamic, LLM-driven routing while maintaining full backward compatibility.

## Architecture

### Marketing Manager Root Agent

The Marketing Manager is an ADK `LlmAgent` that acts as the central routing coordinator. It uses DeepSeek's reasoning model (via the existing `LiteLlm` wrapper) to determine the optimal sequence of specialist agents for each marketing campaign.

**Key Characteristics:**
- **Model**: DeepSeek v4 Pro (reasoning model) via `deepseek_reasoning()`
- **Instruction**: Contains detailed descriptions of all 8 specialist agents and their roles
- **Delegation**: Routes to specialist agents based on campaign objectives
- **Fallback**: Gracefully degrades to static steps when `DEEPSEEK_API_KEY` is unavailable

### Specialist Agents

The system maintains 9 specialized agents, each wrapped as an ADK `FunctionTool`:

1. **Market Intelligence** - Researches market trends, discussions, and opportunities
2. **Content Strategy** - Plans content strategy and editorial calendar
3. **Technical Content** - Creates technical documentation and tutorials
4. **Founder Content** - Creates founder-led content and thought leadership
5. **SEO Content** - Creates Google-search-optimized long-form content with SEO metadata
6. **Social Publishing** - Manages social media publishing (Moltbook access)
7. **Community Engagement** - Handles community interactions (Moltbook access)
8. **Analytics** - Tracks content performance and provides insights
9. **Compliance & Brand** - Ensures content meets brand guidelines

### Model Gateway

The system uses the existing `LiteLlm` wrapper from `google.adk.models.lite_llm` as the model gateway:

```python
from apps.core.models.factory import deepseek_reasoning

# Returns LiteLlm instance when DEEPSEEK_API_KEY is present
# Returns None when DEEPSEEK_API_KEY is absent (graceful degradation)
model = deepseek_reasoning()
```

**Models Used:**
- **Root Agent**: `deepseek/deepseek-v4-pro` (reasoning model)
- **Specialists**: Existing models remain unchanged (can use `deepseek_fast()` or other models)

## Implementation Details

### ADK Orchestrator (`apps/agents/adk_orchestrator.py`)

The `ADKOrchestrator` class manages the Marketing Manager lifecycle:

```python
class ADKOrchestrator:
    def __init__(self):
        self.root_agent = None
        self.runner = None
        self._initialized = False
    
    def initialize(self) -> bool:
        """Initialize ADK Marketing Manager if DEEPSEEK_API_KEY is available."""
        model = deepseek_reasoning()
        if model is None:
            return False  # No key available, will use static fallback
        
        self.root_agent = LlmAgent(
            name="marketing_manager",
            model=model,
            instruction=MARKETING_MANAGER_INSTRUCTION
        )
        self.runner = Runner(self.root_agent)
        self._initialized = True
        return True
```

### No-Key Fallback

When `DEEPSEEK_API_KEY` is not available (CI, tests, or no-key environments), the system automatically falls back to the static steps:

```python
def _static_fallback(self, objective: str, db_session) -> Dict[str, Any]:
    """Static fallback orchestration when ADK is not available."""
    steps = [
        {"agent": "Market Intelligence", "input": {"topic": objective}},
        {"agent": "Content Strategy", "input": {"objective": objective}},
        {"agent": "Community Engagement", "input": {"discussions": discussions}}
    ]
    return {"routing_method": "static_fallback", "steps": steps, "objective": objective}
```

**Audit Events:**
- `adk_routed`: When Marketing Manager successfully routes via ADK
- `static_fallback`: When system falls back to static steps (no key)

### Integration with Existing Infrastructure

The ADK orchestrator preserves all existing infrastructure:

- **Persistence**: CampaignModel/TaskModel remain unchanged
- **Audit Logging**: Uses existing `record_event()` service
- **Policy Engine**: Approval gates remain enforced
- **Dramatiq Queue**: Task queue integration unchanged
- **Moltbook Tools**: Permission gating preserved
- **Real Execution**: `_execute_specialist` now truly executes specialists with proper async handling

## Routing Flow

### With ADK (DEEPSEEK_API_KEY present)

1. User creates campaign via API
2. `GrowthOrchestratorAgent.execute()` calls `ADKOrchestrator.orchestrate_campaign()`
3. Marketing Manager receives objective via ADK Runner
4. LLM determines optimal specialist sequence
5. Steps parsed from ADK response
6. Steps fed into existing `_dispatch_campaign()`/`Orchestrator.create_campaign()`
7. Audit event recorded as `adk_routed`
8. Tasks enqueued via dramatiq as usual

### Without ADK (DEEPSEEK_API_KEY absent)

1. User creates campaign via API
2. `GrowthOrchestratorAgent.execute()` calls `ADKOrchestrator.orchestrate_campaign()`
3. `deepseek_reasoning()` returns `None`
4. System automatically uses static fallback
5. Static steps fed into existing `_dispatch_campaign()`/`Orchestrator.create_campaign()`
6. Audit event recorded as `static_fallback`
7. Tasks enqueued via dramatiq as usual

### Specialist Tool Execution

The `_execute_specialist` method now truly executes specialist agents by calling their async `execute()` method:

- **Async Handling**: Safely handles async execution in both sync and async contexts
- **Event Loop Detection**: Uses `asyncio.get_running_loop()` to detect if called from within an event loop
- **Thread Pool Execution**: When called from within an event loop, runs the coroutine in a fresh loop using `ThreadPoolExecutor` + `asyncio.run()`
- **Direct Execution**: When no event loop is running, uses `asyncio.run()` directly
- **Error Handling**: Preserves existing try/except error envelope for graceful degradation
- **Result Return**: Returns the actual specialist result dict with `{"specialist": name, "result": result}`

This ensures ADK tools can genuinely execute specialists while maintaining compatibility with the existing async/await infrastructure.

## Moltbook Tool Integration

### Permission Gating

Moltbook publish tools are only exposed to authorized specialists:

- **Social Publishing**: Has Moltbook publish access
- **Community Engagement**: Has Moltbook publish access
- **Other Specialists**: No direct Moltbook publish access

The existing permission gating in `apps/workers/tasks.py:_perform_publish_logic` remains enforced:

```python
# Existing gate (unchanged)
if not settings.MOLTBOOK_AUTOPUBLISH:
    await policy_engine.check_approval(content_item)
```

### Approval Process

The ADK orchestrator does NOT bypass the approval process:

1. Specialist requests Moltbook publish
2. Check `MOLTBOOK_AUTOPUBLISH` setting
3. If disabled, require human approval via policy engine
4. If approved, execute publish operation
5. Record audit event

## SEO Content Generation

### SEO Content Specialist

The system includes a dedicated SEO Content specialist for Google-search-optimized content:

- **Agent**: `SEOContentAgent` in `apps/agents/specialized.py`
- **Role**: SEO Writer
- **Purpose**: Creates Google-search-optimized long-form content with SEO metadata
- **Routing**: Items with `channel="google"` or `channel="seo"` are routed to SEO Content
- **SEO Metadata**: Generates and stores:
  - SEO title tag (50-60 characters)
  - Meta description (150-160 characters)
  - Target keyword list (3-5 keywords)
  - H1 heading
  - H2 subheadings
  - Article body
- **Storage**: SEO metadata stored in `ContentItemModel.variants` (JSON field)
- **Workflow**: SEO Content → Compliance & Brand → Approval → Dashboard display

### SEO Routing Logic

The task routing in `apps/workers/tasks.py` extends the Content Strategy follow-on logic:

```python
# Check for SEO/Google channel
seo_keywords = ["google", "seo", "article", "blog"]
if any(kw in (item.channel or "").lower() for kw in seo_keywords) or \
   any(kw in (item.format or "").lower() for kw in seo_keywords) or \
   any(kw in (item.objective or "").lower() for kw in seo_keywords):
    target_agent = "SEO Content"
```

### SEO Content Publishing

Google SEO content is NOT a Moltbook submolt - it follows a different publishing path:

- **Publish Path**: Approved SEO items remain at "approved"/"published" status as demonstrable artifacts
- **Dashboard Display**: SEO body and metadata visible in dashboard Content Queue
- **Audit Logging**: SEO operations logged honestly (no dry-run masquerading as live publish)
- **No Moltbook Force**: SEO items are not forced through Moltbook allowlist

## Testing

### ADK Orchestration Tests (`tests/test_adk_orchestration.py`)

Comprehensive test suite with 13 tests:

1. **Initialization Tests**
   - `test_adk_orchestrator_initialization_with_key` - Verifies ADK initialization with key
   - `test_adk_orchestrator_initialization_without_key` - Verifies graceful degradation without key

2. **Routing Tests**
   - `test_adk_orchestrator_adk_routing` - Tests ADK routing with mocked Runner
   - `test_adk_orchestrator_static_fallback` - Tests static fallback without key

3. **Tool Tests**
   - `test_specialist_tool_creation` - Verifies 9 specialist tools created (added SEO Content)
   - `test_specialist_tool_execution` - Tests real specialist execution via async/await
   - `test_specialist_tool_not_found` - Tests error handling for missing agents

4. **Integration Tests**
   - `test_existing_orchestration_still_works` - Backward compatibility test
   - `test_moltbook_tools_permission_gating` - Verifies permission gating

5. **Response Parsing Tests**
   - `test_adk_response_parsing_json` - Tests JSON array parsing
   - `test_adk_response_parsing_fallback` - Tests parse error fallback
   - `test_adk_response_parsing_no_json` - Tests non-JSON response handling

6. **Utility Tests**
   - `test_singleton_instance` - Verifies singleton pattern

### SEO Content Tests (`tests/test_seo_content.py`)

Test suite for SEO Content specialist (3 tests):

1. **SEO Content Generation**
   - `test_seo_content_agent_generates_seo_content` - Tests SEO metadata generation and persistence
   - `test_seo_content_agent_handles_missing_item` - Tests error handling for missing items
   - `test_seo_content_agent_capabilities` - Verifies agent capabilities

### Orchestration Flow Tests (`tests/test_orchestration_flow.py`)

Extended test suite for SEO routing (2 tests):

1. **SEO Routing Test**
   - `test_seo_content_routing_flow` - Tests google/seo channel routing to SEO Content → Compliance & Brand
2. **Regression Test**
   - `test_dispatch_happens_after_commit_regression` - Ensures .send() only called after commit

### Key Test Features

- **No Live Keys Required**: All tests use mocked ADK Runner/DeepSeek
- **Backward Compatibility**: Existing tests (`test_orchestration_flow.py`, `test_api_campaigns.py`) remain green
- **CI Compatibility**: Tests pass without `DEEPSEEK_API_KEY` (uses static fallback)

## Configuration

### Environment Variables

```bash
# Required for ADK routing (optional for static fallback)
DEEPSEEK_API_KEY=sk-your-deepseek-api-key
DEEPSEEK_REASONING_MODEL=deepseek/deepseek-v4-pro
DEEPSEEK_API_BASE=https://api.deepseek.com
```

### No-Key Operation

When `DEEPSEEK_API_KEY` is not set:
- System automatically uses static fallback
- No errors or crashes
- Full functionality preserved
- Audit events clearly mark as `static_fallback`

## Monitoring and Debugging

### Audit Events

The system records detailed audit events:

```python
{
    "agent_name": "Marketing Manager (ADK)" or "Growth Orchestrator (Static)",
    "event_type": "campaign_orchestrated",
    "message": "ADK-routed campaign: {objective}" or "Static-fallback campaign: {objective}",
    "metadata": {
        "objective": objective,
        "routing_method": "adk_routed" or "static_fallback",
        "steps": [...]
    }
}
```

### Logging

Key log messages:

```
INFO:apps.agents.adk_orchestrator:ADK Marketing Manager initialized successfully
WARNING:apps.agents.adk_orchestrator:DEEPSEEK_API_KEY not available, ADK orchestrator will use static fallback
INFO:apps.agents.adk_orchestrator:Using ADK Marketing Manager to orchestrate campaign: {objective}
INFO:apps.agents.adk_orchestrator:ADK not available, using static fallback for campaign orchestration
INFO:apps.agents.adk_orchestrator:Using static fallback for campaign: {objective}
```

## Performance Considerations

### ADK Routing Overhead

- **With ADK**: Additional ~500ms-2s for LLM routing decision
- **Without ADK**: No overhead (immediate static steps)
- **Trade-off**: Dynamic routing flexibility vs. latency

### Optimization

- Static fallback used in CI/tests for immediate results
- Production deployments with `DEEPSEEK_API_KEY` get intelligent routing
- Routing decision cached per campaign (single LLM call per campaign)

## Security Considerations

### Model Gateway Security

- `DEEPSEEK_API_KEY` stored in environment variables (never committed)
- LiteLlm wrapper provides secure API key handling
- No model output directly exposed to users without sanitization

### Permission Gating

- Moltbook tools respect existing permission gates
- Approval process unchanged
- Policy engine still enforces constraints

### Audit Trail

- All routing decisions logged with method used
- Specialist execution logged per agent
- Moltbook operations logged with approval status

## Future Enhancements

### Potential Improvements

1. **Routing Optimization**: Cache routing decisions for similar objectives
2. **Custom Instructions**: Allow Marketing Manager instruction customization
3. **Multi-Model Support**: Support for other LLM providers via LiteLlm
4. **Routing Analytics**: Track which agent sequences perform best
5. **A/B Testing**: Compare ADK routing vs. static fallback performance

### Extensibility

The ADK orchestrator is designed for easy extension:

- Add new specialists by updating `MARKETING_MANAGER_INSTRUCTION`
- Modify routing logic by updating the instruction prompt
- Add new tools by extending `create_specialist_tools()`
- Support for additional LLM providers via LiteLlm

## Troubleshooting

### Common Issues

**Issue**: ADK routing not working
- **Check**: `DEEPSEEK_API_KEY` is set in environment
- **Check**: DeepSeek API key is valid and has credits
- **Log**: Look for "DEEPSEEK_API_KEY not available" warning

**Issue**: Tests failing with KeyError
- **Check**: Mock setup includes SessionLocal if needed
- **Check**: All dependencies properly mocked

**Issue**: Static fallback always used
- **Check**: `DEEPSEEK_API_KEY` environment variable
- **Check**: LiteLlm wrapper returns non-None model
- **Log**: Look for "ADK Marketing Manager initialized successfully"

## References

- **Google ADK Documentation**: https://github.com/google/generative-ai-sdk
- **LiteLlm Documentation**: https://docs.litellm.ai/
- **DeepSeek API**: https://api.deepseek.com/docs
- **dev-guide.txt §3**: Marketing Manager root agent specification
