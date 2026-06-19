DEPARTMENT_ROLE_TEMPLATES: dict[str, list[dict]] = {
    "Game Design": [
        {"title": "Game Director", "responsibilities": ["Define creative vision", "Approve game design decisions"], "authority": ["Final call on design"], "reports_to": None, "required_skills": ["Game design", "Leadership"]},
        {"title": "Gameplay Designer", "responsibilities": ["Design core mechanics", "Prototype gameplay systems"], "authority": ["Mechanics design"], "reports_to": "Game Director", "required_skills": ["Game design", "Systems thinking"]},
        {"title": "Level Designer", "responsibilities": ["Design levels and environments", "Balance difficulty curves"], "authority": ["Level layout decisions"], "reports_to": "Game Director", "required_skills": ["Level design", "Spatial reasoning"]},
    ],
    "Engineering": [
        {"title": "Technical Director", "responsibilities": ["Architecture decisions", "Technology stack selection"], "authority": ["Technical architecture"], "reports_to": None, "required_skills": ["Software architecture", "Engineering management"]},
        {"title": "Engine Programmer", "responsibilities": ["Core engine features", "Performance optimization"], "authority": ["Engine implementation"], "reports_to": "Technical Director", "required_skills": ["C++", "Game engines"]},
        {"title": "Tools Programmer", "responsibilities": ["Build development tools", "Pipeline automation"], "authority": ["Tooling decisions"], "reports_to": "Technical Director", "required_skills": ["Python", "Tool development"]},
    ],
    "Art": [
        {"title": "Art Director", "responsibilities": ["Visual style guide", "Art quality standards"], "authority": ["Visual direction"], "reports_to": None, "required_skills": ["Art direction", "Visual design"]},
        {"title": "3D Artist", "responsibilities": ["Create 3D models and assets", "Texture and material creation"], "authority": ["Asset creation"], "reports_to": "Art Director", "required_skills": ["Blender", "3D modeling"]},
        {"title": "UI/UX Designer", "responsibilities": ["Design user interfaces", "User experience flows"], "authority": ["UI/UX design"], "reports_to": "Art Director", "required_skills": ["UI design", "Figma"]},
    ],
    "Management": [
        {"title": "CEO", "responsibilities": ["Overall project vision", "Strategic decisions", "Resource allocation"], "authority": ["Final decision on all matters"], "reports_to": None, "required_skills": ["Leadership", "Strategy", "Management"]},
        {"title": "Producer", "responsibilities": ["Schedule management", "Team coordination", "Risk management"], "authority": ["Production priorities"], "reports_to": None, "required_skills": ["Project management", "Communication"]},
    ],
    "Quality Assurance": [
        {"title": "QA Lead", "responsibilities": ["Test strategy", "QA process definition"], "authority": ["Quality sign-off"], "reports_to": None, "required_skills": ["Testing", "Quality processes"]},
        {"title": "QA Tester", "responsibilities": ["Execute test cases", "Bug reporting and verification"], "authority": ["Bug reporting"], "reports_to": "QA Lead", "required_skills": ["Testing", "Attention to detail"]},
    ],
    "Marketing": [
        {"title": "Marketing Lead", "responsibilities": ["Marketing strategy", "Brand management"], "authority": ["Marketing decisions"], "reports_to": None, "required_skills": ["Marketing", "Brand strategy"]},
    ],
    "DevOps": [
        {"title": "DevOps Engineer", "responsibilities": ["CI/CD pipeline", "Infrastructure management", "Deployment automation"], "authority": ["Infrastructure decisions"], "reports_to": None, "required_skills": ["Docker", "CI/CD", "Cloud"]},
    ],
    "Data": [
        {"title": "Data Engineer", "responsibilities": ["Data pipelines", "Database management"], "authority": ["Data architecture"], "reports_to": None, "required_skills": ["SQL", "Data engineering"]},
        {"title": "Data Scientist", "responsibilities": ["Analytics", "Player behavior analysis"], "authority": ["Data insights"], "reports_to": None, "required_skills": ["ML", "Statistics", "Python"]},
    ],
    "Content": [
        {"title": "Content Lead", "responsibilities": ["Content strategy", "Writing guidelines"], "authority": ["Content decisions"], "reports_to": None, "required_skills": ["Writing", "Content strategy"]},
        {"title": "Writer", "responsibilities": ["Write narrative content", "Dialog and lore"], "authority": ["Narrative writing"], "reports_to": "Content Lead", "required_skills": ["Creative writing", "Narrative design"]},
    ],
    "Product": [
        {"title": "Product Manager", "responsibilities": ["Product strategy", "Feature prioritization", "Stakeholder management"], "authority": ["Product roadmap"], "reports_to": None, "required_skills": ["Product management", "Strategy"]},
    ],
}


def get_department_name_key(raw_name: str) -> str | None:
    normalized = raw_name.lower().strip()
    for key in DEPARTMENT_ROLE_TEMPLATES:
        if key.lower() in normalized or normalized in key.lower():
            return key
    return None


def define_roles(departments: list[dict]) -> list[dict]:
    all_roles = []
    for dept in departments:
        dept_name = dept["name"] if isinstance(dept, dict) else dept
        key = get_department_name_key(dept_name)
        if key:
            templates = DEPARTMENT_ROLE_TEMPLATES[key]
        else:
            templates = [
                {"title": f"{dept_name} Lead", "responsibilities": [f"Lead {dept_name} efforts"], "authority": [f"{dept_name} decisions"], "reports_to": None, "required_skills": []},
                {"title": f"{dept_name} Specialist", "responsibilities": [f"Execute {dept_name} tasks"], "authority": [], "reports_to": f"{dept_name} Lead", "required_skills": []},
            ]
        for t in templates:
            all_roles.append({
                "department_name": dept_name,
                "title": t["title"],
                "responsibilities": t["responsibilities"],
                "authority": t["authority"],
                "reports_to": t["reports_to"],
                "required_skills": t["required_skills"],
            })
    return all_roles
