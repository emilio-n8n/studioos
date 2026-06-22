import pytest
from unittest.mock import patch, AsyncMock
from app.workforce.task_executor import generate_task_output, parse_files_from_llm


def test_parse_files_from_llm():
    text = "===FILE:output/1/report.md===\n# My Report\n\nContent\n===FILE:output/1/result.json===\n{\"status\": \"ok\"}\n"
    files = parse_files_from_llm(text)
    assert len(files) == 2
    assert files[0]["path"] == "output/1/report.md"
    assert files[0]["content"] == "# My Report\n\nContent"
    assert files[1]["path"] == "output/1/result.json"


def test_parse_files_from_llm_empty():
    assert parse_files_from_llm("No files here") == []


def test_parse_files_from_llm_single():
    text = "===FILE:test.txt===\nhello"
    files = parse_files_from_llm(text)
    assert len(files) == 1
    assert files[0]["path"] == "test.txt"


@pytest.mark.asyncio
async def test_generate_task_output_parses_files():
    with patch("app.workforce.task_executor.AsyncOpenAI") as mock_openai:
        mock_instance = AsyncMock()
        mock_instance.chat.completions.create = AsyncMock(return_value=AsyncMock(
            choices=[AsyncMock(message=AsyncMock(content="===FILE:output/42/report.md===\n# My Task\nDone!\n"))]
        ))
        mock_openai.return_value = mock_instance

        files = await generate_task_output(
            task_title="Build feature X",
            task_description="Implement the login system",
            role_title="Backend Developer",
            department_name="Engineering",
            project_name="MyApp",
            project_summary="A web app",
            task_id=42,
            api_key="test-key",
            provider="openai",
        )
        assert len(files) == 1
        assert files[0]["path"] == "output/42/report.md"
        assert "My Task" in files[0]["content"]


@pytest.mark.asyncio
async def test_generate_task_output_fallback():
    with patch("app.workforce.task_executor.AsyncOpenAI") as mock_openai:
        mock_instance = AsyncMock()
        mock_instance.chat.completions.create = AsyncMock(return_value=AsyncMock(
            choices=[AsyncMock(message=AsyncMock(content="Just raw text, no files"))]
        ))
        mock_openai.return_value = mock_instance

        files = await generate_task_output(
            task_title="Test",
            task_description="Desc",
            role_title="Worker",
            department_name="General",
            project_name="P",
            project_summary="S",
            task_id=99,
            api_key="demo",
        )
        assert len(files) == 1
        assert files[0]["path"] == "output/99/report.md"
