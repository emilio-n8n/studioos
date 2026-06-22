import asyncio

from app.integration.native_provider import NativeProvider
from app.integration.mock_provider import MockProvider
from app.integration.base import TaskSpec


class TestNativeProvider:
    async def test_native_discover(self):
        provider = NativeProvider()
        agents = await provider.discover_agents()
        assert len(agents) == 4
        names = [a.name for a in agents]
        assert "Strategic Planner" in names
        assert "Organization Architect" in names
        assert "Recruiter" in names
        assert "Agent Executor" in names

    async def test_native_get_capabilities(self):
        provider = NativeProvider()
        caps = await provider.get_capabilities("planner")
        cap_names = [c.name for c in caps]
        assert "strategic_planning" in cap_names
        assert "analysis" in cap_names
        assert "project_design" in cap_names


class TestMockProvider:
    async def test_mock_discover(self):
        provider = MockProvider()
        agents = await provider.discover_agents()
        assert len(agents) == 3
        names = [a.name for a in agents]
        assert "Backend Developer (Mock)" in names
        assert "Frontend Developer (Mock)" in names
        assert "Content Writer (Mock)" in names

    async def test_mock_get_capabilities(self):
        provider = MockProvider()
        caps = await provider.get_capabilities("backend_dev")
        cap_names = [c.name for c in caps]
        assert "backend" in cap_names
        assert "python" in cap_names

    async def test_mock_assign_and_poll(self):
        provider = MockProvider(delay=0.1)
        task = TaskSpec(
            task_id=1,
            title="Build API",
            description="Create a REST API",
            context={},
            required_capabilities=["backend"],
        )
        run_id = await provider.assign_task("backend_dev", task)
        assert run_id is not None

        status = await provider.get_status(run_id)
        assert status.status == "running"

        await asyncio.sleep(0.15)

        status = await provider.get_status(run_id)
        assert status.status == "completed"

        result = await provider.collect_results(run_id)
        assert result.status == "completed"
        assert "report.md" in str(result.output)
