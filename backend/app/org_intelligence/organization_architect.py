from app.org_intelligence.strategic_planner import ProjectAnalysis


def build_hierarchy(departments: list[dict]) -> list[dict]:
    edges = []
    for i, dept in enumerate(departments):
        node = {
            "id": dept["name"],
            "type": "department",
            "label": dept["name"],
            "description": dept["description"],
        }
        edges.append(node)
        if i > 0:
            edges.append({
                "id": f"edge-{departments[i-1]['name']}-{dept['name']}",
                "source": departments[i - 1]["name"],
                "target": dept["name"],
                "type": "hierarchy",
            })
    return edges


def design_organization(analysis: ProjectAnalysis) -> dict:
    departments = analysis.suggested_departments
    hierarchy = build_hierarchy(departments)
    return {
        "name": f"{analysis.name} Org",
        "departments": departments,
        "hierarchy": hierarchy,
    }
