from storage import database

def visible_projects(user, project_id=None):
    conditions = []
    parameters = []
    if user["role"] == "MANAGER":
        conditions.append("p.managerId = ?")
        parameters.append(user["id"])
    if user["role"] == "AGENT":
        conditions.append("EXISTS (SELECT 1 FROM tasks own WHERE own.projectId=p.id AND own.assigneeId=?)")
        parameters.append(user["id"])
    if project_id is not None:
        conditions.append("p.id = ?")
        parameters.append(project_id)
    where = " WHERE " + " AND ".join(conditions) if conditions else ""
    with database() as db:
        projects = db.execute(
            "SELECT p.*, u.name AS managerName FROM projects p JOIN users u ON u.id=p.managerId"
            + where + " ORDER BY p.deadline,p.id", parameters
        ).fetchall()
        result = []
        for project in projects:
            task_parameters = [project["id"]]
            task_filter = ""
            if user["role"] == "AGENT":
                task_filter = " AND t.assigneeId=?"
                task_parameters.append(user["id"])
            tasks = db.execute(
                """SELECT t.*, u.name AS assigneeName FROM tasks t
                   JOIN users u ON u.id=t.assigneeId WHERE t.projectId=?"""
                + task_filter + " ORDER BY t.deadline,t.id", task_parameters
            ).fetchall()
            result.append({**dict(project), "tasks": [dict(task) for task in tasks],
                           "taskCount": len(tasks)})
    return result

def assigned_tasks(user):
    with database() as db:
        rows = db.execute("""
            SELECT t.*, p.name AS projectName, p.clientName,
                   p.deadline AS projectDeadline, p.managerId, u.name AS managerName
            FROM tasks t JOIN projects p ON p.id=t.projectId
            JOIN users u ON u.id=p.managerId
            WHERE t.assigneeId=? ORDER BY t.deadline,t.id
        """, (user["id"],)).fetchall()
    return [dict(row) for row in rows]
