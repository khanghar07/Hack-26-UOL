import os

# Stable challenge IDs also serve as Firebase UIDs for the seeded demo accounts.
PEOPLE = [
    ("ADMIN", "Admin", "ADMIN", "Administrator", ["Company overview", "Transcript creation"]),
    ("PM01", "Ayesha Khan", "MANAGER", "Web PM", ["Web projects", "Client coordination"]),
    ("PM02", "Bilal Ahmed", "MANAGER", "Mobile PM", ["Mobile projects", "Delivery planning"]),
    ("PM03", "Hina Malik", "MANAGER", "AI PM", ["AI projects", "Requirement review"]),
    ("DEV01", "Ali Raza", "AGENT", "Full-Stack", ["React", "Frontend integration"]),
    ("DEV02", "Hamza Shah", "AGENT", "Full-Stack", ["Node.js", "Databases", "APIs"]),
    ("DEV03", "Sara Noor", "AGENT", "App Developer", ["Flutter", "Mobile UI"]),
    ("DEV04", "Usman Tariq", "AGENT", "App Developer", ["Flutter", "Integration", "Testing"]),
    ("DEV05", "Zain Abbas", "AGENT", "AI Developer", ["LLMs", "Extraction", "Prompts"]),
    ("DEV06", "Maryam Asif", "AGENT", "AI Developer", ["Retrieval", "Document processing"]),
]

def email_for(name):
    if name.lower() == "admin":
        return os.getenv("ADMIN_EMAIL", "admin@novaworks.example").strip().lower()
    return name.split()[0].lower() + "@novaworks.example"

def password_for(name):
    if name.lower() == "admin":
        password = os.getenv("ADMIN_PASSWORD", "Demo123!")
        if not password:
            raise ValueError("Set ADMIN_PASSWORD privately before running the seeder.")
        return password
    return "Demo123!"
