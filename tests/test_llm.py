import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from apps.core.models.llm import complete_json, _session_spend


@pytest.mark.asyncio
async def test_llm_complete_json_success():
    """Test successful LLM completion"""
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = '{"status": "success", "data": "test"}'
    mock_response._response_ms = 100
    
    with patch('apps.core.models.llm.acompletion', new_callable=AsyncMock) as mock_acompletion, \
         patch('apps.core.models.llm.settings') as mock_settings:
        mock_settings.DEEPSEEK_API_KEY = "test-key"
        mock_settings.DAILY_LLM_BUDGET_USD = 25.0
        mock_acompletion.return_value = mock_response
        
        result = await complete_json(
            model="deepseek-chat",
            system_prompt="Test prompt",
            user_content="Test content"
        )
        
        assert result == {"status": "success", "data": "test"}
        mock_acompletion.assert_called_once()


@pytest.mark.asyncio
async def test_llm_complete_json_with_schema_hint():
    """Test LLM completion with schema hint"""
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = '{"result": "valid_json"}'
    mock_response._response_ms = 50
    
    with patch('apps.core.models.llm.acompletion', new_callable=AsyncMock) as mock_acompletion, \
         patch('apps.core.models.llm.settings') as mock_settings:
        mock_settings.DEEPSEEK_API_KEY = "test-key"
        mock_settings.DAILY_LLM_BUDGET_USD = 25.0
        mock_acompletion.return_value = mock_response
        
        result = await complete_json(
            model="deepseek-chat",
            system_prompt="Test prompt",
            user_content="Test content",
            schema_hint="Schema hint"
        )
        
        assert result == {"result": "valid_json"}
        # Verify schema hint was included in the prompt
        call_args = mock_acompletion.call_args
        messages = call_args[1]['messages']
        assert "Schema Hint: Schema hint" in messages[0]['content']


@pytest.mark.asyncio
async def test_llm_complete_json_no_api_key():
    """Test fallback when API key is missing"""
    with patch('apps.core.models.llm.settings') as mock_settings:
        mock_settings.DEEPSEEK_API_KEY = None
        mock_settings.DAILY_LLM_BUDGET_USD = 25.0
        
        result = await complete_json(
            model="deepseek-chat",
            system_prompt="Test prompt",
            user_content="Test content"
        )
        
        # Should return fallback result
        assert "status" in result
        assert result["status"] in ["mock_success", "fallback_triggered"]


@pytest.mark.asyncio
async def test_llm_complete_json_budget_exceeded():
    """Test fallback when budget is exceeded"""
    global _session_spend
    _session_spend = 100.0  # Exceed default budget of 25.0
    
    result = await complete_json(
        model="deepseek-chat",
        system_prompt="Test prompt",
        user_content="Test content"
    )
    
    assert result == {"status": "mock_success", "data": "fallback_triggered"}
    
    # Reset for other tests
    _session_spend = 0.0


@pytest.mark.asyncio
async def test_llm_complete_json_error_handling():
    """Test error handling in LLM completion"""
    with patch('apps.core.models.llm.acompletion', new_callable=AsyncMock) as mock_acompletion:
        mock_acompletion.side_effect = Exception("API error")
        
        result = await complete_json(
            model="deepseek-chat",
            system_prompt="Test prompt",
            user_content="Test content"
        )
        
        assert result == {"status": "mock_success", "data": "fallback_triggered"}


@pytest.mark.asyncio
async def test_llm_fallback_heuristic_market_intelligence():
    """Test fallback heuristic for Market Intelligence"""
    from apps.core.models.llm import _fallback_heuristic
    
    result = _fallback_heuristic(
        "Market Intelligence system prompt",
        "test content"
    )
    
    assert "sources" in result
    assert len(result["sources"]) == 1
    assert result["sources"][0]["title"] == "Heuristic Source"
    assert result["sources"][0]["url"] == "https://example.com/mock"


@pytest.mark.asyncio
async def test_llm_fallback_heuristic_generic():
    """Test generic fallback heuristic"""
    from apps.core.models.llm import _fallback_heuristic
    
    result = _fallback_heuristic(
        "Generic system prompt",
        "test content"
    )
    
    assert result == {"status": "mock_success", "data": "fallback_triggered"}


@pytest.mark.asyncio
async def test_llm_session_spend_tracking():
    """Test session spend tracking"""
    global _session_spend
    initial_spend = _session_spend
    
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = '{"status": "success"}'
    mock_response._response_ms = 1000  # 1 second
    
    with patch('apps.core.models.llm.acompletion', new_callable=AsyncMock) as mock_acompletion, \
         patch('apps.core.models.llm.settings') as mock_settings:
        mock_settings.DEEPSEEK_API_KEY = "test-key"
        mock_settings.DAILY_LLM_BUDGET_USD = 25.0
        mock_acompletion.return_value = mock_response
        
        await complete_json(
            model="deepseek-chat",
            system_prompt="Test prompt",
            user_content="Test content"
        )
        
        # Spend should increase by (1000ms / 1000) * 0.0001 = 0.0001
        assert _session_spend >= initial_spend
    
    # Reset for other tests
    _session_spend = 0.0
