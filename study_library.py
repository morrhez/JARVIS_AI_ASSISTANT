import os

def find_materials_folder():
    home = os.path.expanduser("~")
    onedrive = os.environ.get("OneDrive")
    candidates = []
    if onedrive:
        candidates.append(os.path.join(onedrive, "Desktop", "materials"))
    candidates += [
        os.path.join(home, "OneDrive", "Desktop", "materials"),
        os.path.join(home, "Desktop", "materials"),
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "materials"),  # next to the code
    ]
    for p in candidates:
        if os.path.isdir(p):
            return p
    return candidates[-1]

BASE = find_materials_folder()
print("Study library folder:", BASE)

SUFFIXES = ("", " notes", " material", " folder")
ALIASES = {"math": "maths", "chem": "chemistry", "bio": "biology"}  # short name -> folder name

study = {}
if os.path.isdir(BASE):
    for folder in os.listdir(BASE):
        full = os.path.join(BASE, folder)
        if os.path.isdir(full):
            for s in SUFFIXES:
                study[folder.lower() + s] = full

for short, long in ALIASES.items():
    for s in SUFFIXES:
        if long + s in study:
            study[short + s] = study[long + s]