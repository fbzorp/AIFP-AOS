
import pytest
import respx
from httpx import Response
from unittest.mock import AsyncMock, patch
from apps.api.config import settings
from apps.integrations.moltbook.client import MoltbookClient

@pytest.mark.asyncio
async def test_publish_post_with_verification_success():
    # Patch settings for testing
    original_autopublish = settings.MOLTBOOK_AUTOPUBLISH
    original_deepseek_api_key = settings.DEEPSEEK_API_KEY
    original_deepseek_primary_model = settings.DEEPSEEK_PRIMARY_MODEL
    original_deepseek_api_base = settings.DEEPSEEK_API_BASE

    settings.MOLTBOOK_AUTOPUBLISH = True
    settings.DEEPSEEK_API_KEY = "mock_deepseek_key"
    settings.DEEPSEEK_PRIMARY_MODEL = "mock_model"
    settings.DEEPSEEK_API_BASE = "https://mock.deepseek.com"

    client = MoltbookClient(base_url="https://www.moltbook.com")

    with respx.mock(base_url="https://www.moltbook.com") as respx_mock:
        # Mock the initial publish_post call that returns a verification challenge
        respx_mock.post("/api/v1/posts").mock(return_value=Response(
            200, 
            json={
                "verification_required": True,
                "post": {
                    "id": "post-123",
                    "verification": {
                        "verification_code": "abc-123",
                        "challenge_text": "What is 5 + 3?"
                    }
                }
            }
        ))

        # Mock the verify_challenge call
        respx_mock.post("/api/v1/verify").mock(return_value=Response(
            200,
            json={
                "success": True,
                "message": "Verification successful"
            }
        ))

        with patch("litellm.acompletion", new_callable=AsyncMock) as mock_acompletion:
            mock_acompletion.return_value.choices = [AsyncMock()]
            mock_acompletion.return_value.choices[0].message.content = "8"

            result = await client.publish_post("test-submolt", "Test Title", "Test Body")

            assert result["success"] is True
            assert result["post_id"] == "post-123"
            assert result["post_url"] == "https://www.moltbook.com/posts/post-123"
            mock_acompletion.assert_called_once_with(
                model="mock_model",
                api_key="mock_deepseek_key",
                api_base="https://mock.deepseek.com",
                messages=[
                    {"role": "user", "content": "Solve this Moltbook AI verification challenge. It is an obfuscated math problem. Extract the two numbers and the operation, compute the result, and respond with ONLY the number (e.g., '15.00').\n\nChallenge: What is 5 + 3?"}
                ],
                timeout=30
            )

    # Restore original settings
    settings.MOLTBOOK_AUTOPUBLISH = original_autopublish
    settings.DEEPSEEK_API_KEY = original_deepseek_api_key
    settings.DEEPSEEK_PRIMARY_MODEL = original_deepseek_primary_model
    settings.DEEPSEEK_API_BASE = original_deepseek_api_base

@pytest.mark.asyncio
async def test_publish_post_with_verification_failure():
    # Patch settings for testing
    original_autopublish = settings.MOLTBOOK_AUTOPUBLISH
    original_deepseek_api_key = settings.DEEPSEEK_API_KEY
    original_deepseek_primary_model = settings.DEEPSEEK_PRIMARY_MODEL
    original_deepseek_api_base = settings.DEEPSEEK_API_BASE

    settings.MOLTBOOK_AUTOPUBLISH = True
    settings.DEEPSEEK_API_KEY = "mock_deepseek_key"
    settings.DEEPSEEK_PRIMARY_MODEL = "mock_model"
    settings.DEEPSEEK_API_BASE = "https://mock.deepseek.com"

    client = MoltbookClient(base_url="https://www.moltbook.com")

    with respx.mock(base_url="https://www.moltbook.com") as respx_mock:
        # Mock the initial publish_post call that returns a verification challenge
        respx_mock.post("/api/v1/posts").mock(return_value=Response(
            200, 
            json={
                "verification_required": True,
                "post": {
                    "id": "post-123",
                    "verification": {
                        "verification_code": "abc-123",
                        "challenge_text": "What is 5 + 3?"
                    }
                }
            }
        ))

        # Mock the verify_challenge call to fail
        respx_mock.post("/api/v1/verify").mock(return_value=Response(
            200,
            json={
                "success": False,
                "error": "Incorrect answer"
            }
        ))

        with patch("litellm.acompletion", new_callable=AsyncMock) as mock_acompletion:
            mock_acompletion.return_value.choices = [AsyncMock()]
            mock_acompletion.return_value.choices[0].message.content = "9" # Incorrect answer

            # With our new implementation, verification failure returns an error structure
            result = await client.publish_post("test-submolt", "Test Title", "Test Body")
            
            # Should return error structure instead of raising ValueError
            assert result["success"] is False
            assert result["dry_run"] is False
            assert result["post_id"] is None
            assert result["post_url"] is None
            assert "Verification failed" in result["error"]

            mock_acompletion.assert_called_once()

    # Restore original settings
    settings.MOLTBOOK_AUTOPUBLISH = original_autopublish
    settings.DEEPSEEK_API_KEY = original_deepseek_api_key
    settings.DEEPSEEK_PRIMARY_MODEL = original_deepseek_primary_model
    settings.DEEPSEEK_API_BASE = original_deepseek_api_base

@pytest.mark.asyncio
async def test_publish_post_with_missing_deepseek_api_key():
    # Patch settings for testing
    original_autopublish = settings.MOLTBOOK_AUTOPUBLISH
    original_deepseek_api_key = settings.DEEPSEEK_API_KEY

    settings.MOLTBOOK_AUTOPUBLISH = True
    settings.DEEPSEEK_API_KEY = None # Simulate missing API key

    client = MoltbookClient(base_url="https://www.moltbook.com")

    with respx.mock(base_url="https://www.moltbook.com") as respx_mock:
        # Mock the initial publish_post call that returns a verification challenge
        respx_mock.post("/api/v1/posts").mock(return_value=Response(
            200, 
            json={
                "verification_required": True,
                "post": {
                    "id": "post-123",
                    "verification": {
                        "verification_code": "abc-123",
                        "challenge_text": "What is 5 + 3?"
                    }
                }
            }
        ))

        # No litellm.acompletion mock needed as it should not be called
        result = await client.publish_post("test-submolt", "Test Title", "Test Body")

        # With our new implementation, it returns an error structure when DEEPSEEK_API_KEY is missing
        assert result["success"] is False
        assert result["dry_run"] is False
        assert result["post_id"] is None
        assert result["post_url"] is None
        assert "DEEPSEEK_API_KEY not found" in result["error"]
        assert settings.DEEPSEEK_API_KEY is None # Ensure API key remains None

    # Restore original settings
    settings.MOLTBOOK_AUTOPUBLISH = original_autopublish
    settings.DEEPSEEK_API_KEY = original_deepseek_api_key

