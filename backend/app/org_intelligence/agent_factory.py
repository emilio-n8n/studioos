AGENT_NAMES = [
    "Alexis", "Morgan", "Jordan", "Casey", "Riley", "Quinn", "Avery", "Sage",
    "Rowan", "Ellis", "Parker", "Blake", "Cameron", "Drew", "Hayden", "Reese",
    "Skyler", "Sloane", "Emerson", "Finley",
]


def generate_agent_name(used_names: set[str]) -> str:
    for name in AGENT_NAMES:
        if name not in used_names:
            used_names.add(name)
            return name
    i = len(used_names) + 1
    name = f"Agent_{i}"
    used_names.add(name)
    return name


def create_agents(roles: list[dict]) -> list[dict]:
    agents = []
    used_names = set()
    for role in roles:
        agent = {
            "role_title": role["title"],
            "department_name": role["department_name"],
            "name": generate_agent_name(used_names),
            "status": "created",
        }
        agents.append(agent)
    return agents


def generate_initial_tasks(agents: list[dict]) -> list[dict]:
    tasks = []
    for agent in agents:
        task = {
            "title": f"Initial setup - {agent['name']}",
            "description": f"Complete onboarding and initial orientation as {agent['role_title']} in {agent['department_name']}",
            "assigned_agent_name": agent["name"],
            "department_name": agent["department_name"],
            "priority": 1,
            "status": "TODO",
            "estimated_cost": 1.0,
        }
        tasks.append(task)
    return tasks
