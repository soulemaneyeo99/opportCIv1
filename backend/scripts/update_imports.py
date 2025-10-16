import os
import re

# === CONFIG ===
# Répertoires à scanner (selon la nouvelle structure)
SEARCH_DIRS = [
    "backend/apps",
    "backend/config",
]

# Mappage des anciens imports vers les nouveaux chemins
REPLACEMENTS = {
    # Anciens chemins Django vers la nouvelle architecture
    "from accounts.": "from apps.accounts.",
    "from opportunities.": "from apps.opportunities.",
    "from core.": "from config.",
    "import core.": "import config.",
    "from payments.": "from apps.payments.",
    "from users.": "from apps.users.",
    "from learning.": "from apps.learning.",
    "from ai_engine.": "from apps.ai_engine.",
}

# === LOGIC ===
def update_imports(file_path):
    """Met à jour les imports Django selon le nouveau schéma du projet."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
    except (UnicodeDecodeError, FileNotFoundError):
        return

    original_content = content
    for old, new in REPLACEMENTS.items():
        content = content.replace(old, new)

    if content != original_content:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"✅ Imports mis à jour dans : {file_path}")


def run_update():
    for base_dir in SEARCH_DIRS:
        for root, _, files in os.walk(base_dir):
            for file in files:
                if file.endswith(".py"):
                    update_imports(os.path.join(root, file))


if __name__ == "__main__":
    print("🔍 Mise à jour des imports en cours...")
    run_update()
    print("🎯 Mise à jour terminée avec succès !")
