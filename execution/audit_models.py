#!/usr/bin/env python3
"""
Audit des modèles Django existants
==================================
Génère un rapport JSON des modèles, champs, et relations.

Usage:
    python execution/audit_models.py

Output:
    .tmp/audit_models_report.json
"""

import os
import sys
import json
import ast
from pathlib import Path
from datetime import datetime

# Configuration
BACKEND_PATH = Path(__file__).parent.parent / "backend"
APPS_PATH = BACKEND_PATH / "apps"
OUTPUT_PATH = Path(__file__).parent.parent / ".tmp"


def extract_models_from_file(file_path: Path) -> list:
    """
    Parse un fichier Python et extrait les définitions de modèles Django.
    """
    models = []

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        tree = ast.parse(content)

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                # Vérifier si c'est un modèle Django (hérite de models.Model)
                is_model = False
                for base in node.bases:
                    base_name = ""
                    if isinstance(base, ast.Attribute):
                        base_name = f"{base.value.id}.{base.attr}" if isinstance(base.value, ast.Name) else base.attr
                    elif isinstance(base, ast.Name):
                        base_name = base.id

                    if "Model" in base_name or base_name in ["AbstractUser", "BaseUserManager"]:
                        is_model = True
                        break

                if is_model:
                    model_info = {
                        "name": node.name,
                        "file": str(file_path.relative_to(BACKEND_PATH)),
                        "line": node.lineno,
                        "fields": [],
                        "methods": [],
                        "meta": {}
                    }

                    # Extraire les champs et méthodes
                    for item in node.body:
                        if isinstance(item, ast.Assign):
                            for target in item.targets:
                                if isinstance(target, ast.Name):
                                    field_info = extract_field_info(target.name, item.value)
                                    if field_info:
                                        model_info["fields"].append(field_info)

                        elif isinstance(item, ast.FunctionDef):
                            model_info["methods"].append(item.name)

                        elif isinstance(item, ast.ClassDef) and item.name == "Meta":
                            model_info["meta"] = extract_meta_info(item)

                    models.append(model_info)

    except Exception as e:
        print(f"  ⚠️  Erreur parsing {file_path}: {e}")

    return models


def extract_field_info(name: str, value_node) -> dict:
    """
    Extrait les informations d'un champ Django.
    """
    if not isinstance(value_node, ast.Call):
        return None

    field_type = ""
    if isinstance(value_node.func, ast.Attribute):
        field_type = value_node.func.attr
    elif isinstance(value_node.func, ast.Name):
        field_type = value_node.func.id

    # Filtrer les non-champs
    django_fields = [
        "CharField", "TextField", "IntegerField", "FloatField", "BooleanField",
        "DateField", "DateTimeField", "EmailField", "URLField", "FileField",
        "ImageField", "ForeignKey", "OneToOneField", "ManyToManyField",
        "JSONField", "UUIDField", "PositiveIntegerField", "SlugField",
        "GenericIPAddressField", "GenericForeignKey"
    ]

    if field_type not in django_fields:
        return None

    field_info = {
        "name": name,
        "type": field_type,
        "required": True,
        "related_model": None
    }

    # Extraire les arguments
    for keyword in value_node.keywords:
        if keyword.arg == "blank" and isinstance(keyword.value, ast.Constant):
            if keyword.value.value:
                field_info["required"] = False
        elif keyword.arg == "null" and isinstance(keyword.value, ast.Constant):
            if keyword.value.value:
                field_info["required"] = False
        elif keyword.arg == "default":
            field_info["has_default"] = True

    # Extraire le modèle lié pour ForeignKey/etc
    if field_type in ["ForeignKey", "OneToOneField", "ManyToManyField"]:
        if value_node.args:
            arg = value_node.args[0]
            if isinstance(arg, ast.Constant):
                field_info["related_model"] = arg.value
            elif isinstance(arg, ast.Attribute):
                field_info["related_model"] = f"{arg.value.id}.{arg.attr}" if isinstance(arg.value, ast.Name) else arg.attr
            elif isinstance(arg, ast.Name):
                field_info["related_model"] = arg.id

    return field_info


def extract_meta_info(meta_node) -> dict:
    """
    Extrait les informations de la classe Meta.
    """
    meta = {}

    for item in meta_node.body:
        if isinstance(item, ast.Assign):
            for target in item.targets:
                if isinstance(target, ast.Name):
                    if target.name == "verbose_name":
                        meta["verbose_name"] = True
                    elif target.name == "ordering":
                        meta["ordering"] = True
                    elif target.name == "unique_together":
                        meta["unique_together"] = True
                    elif target.name == "indexes":
                        meta["has_indexes"] = True

    return meta


def audit_app(app_path: Path) -> dict:
    """
    Audit une app Django complète.
    """
    app_name = app_path.name
    app_info = {
        "name": app_name,
        "models": [],
        "has_api": False,
        "has_admin": False,
        "has_tests": False,
        "has_tasks": False,
        "has_services": False,
        "files_count": 0,
        "lines_count": 0
    }

    # Scanner les modèles
    models_path = app_path / "models"
    if models_path.exists():
        for py_file in models_path.glob("*.py"):
            if py_file.name != "__init__.py":
                models = extract_models_from_file(py_file)
                app_info["models"].extend(models)

    # Vérifier la présence de composants
    app_info["has_api"] = (app_path / "api").exists()
    app_info["has_admin"] = (app_path / "admin.py").exists()
    app_info["has_tests"] = (app_path / "tests").exists() and any((app_path / "tests").glob("test_*.py"))
    app_info["has_tasks"] = (app_path / "tasks").exists()
    app_info["has_services"] = (app_path / "services").exists()

    # Compter les fichiers et lignes
    for py_file in app_path.rglob("*.py"):
        app_info["files_count"] += 1
        try:
            with open(py_file, 'r', encoding='utf-8') as f:
                app_info["lines_count"] += len(f.readlines())
        except:
            pass

    return app_info


def generate_summary(apps: list) -> dict:
    """
    Génère un résumé de l'audit.
    """
    total_models = sum(len(app["models"]) for app in apps)
    total_fields = sum(
        len(model["fields"])
        for app in apps
        for model in app["models"]
    )
    total_files = sum(app["files_count"] for app in apps)
    total_lines = sum(app["lines_count"] for app in apps)

    apps_with_tests = sum(1 for app in apps if app["has_tests"])
    apps_with_api = sum(1 for app in apps if app["has_api"])

    return {
        "total_apps": len(apps),
        "total_models": total_models,
        "total_fields": total_fields,
        "total_files": total_files,
        "total_lines": total_lines,
        "apps_with_tests": apps_with_tests,
        "apps_with_api": apps_with_api,
        "test_coverage_apps": f"{apps_with_tests}/{len(apps)}",
        "api_coverage_apps": f"{apps_with_api}/{len(apps)}"
    }


def main():
    print("🔍 Audit des modèles OpportuCI")
    print("=" * 50)

    # Vérifier que le chemin existe
    if not APPS_PATH.exists():
        print(f"❌ Chemin apps non trouvé: {APPS_PATH}")
        sys.exit(1)

    # Créer le dossier output
    OUTPUT_PATH.mkdir(exist_ok=True)

    # Scanner chaque app
    apps = []
    for app_dir in sorted(APPS_PATH.iterdir()):
        if app_dir.is_dir() and not app_dir.name.startswith("_"):
            print(f"\n📦 Scanning {app_dir.name}...")
            app_info = audit_app(app_dir)
            apps.append(app_info)
            print(f"   └── {len(app_info['models'])} modèles, {app_info['files_count']} fichiers")

    # Générer le résumé
    summary = generate_summary(apps)

    # Rapport complet
    report = {
        "generated_at": datetime.now().isoformat(),
        "summary": summary,
        "apps": apps
    }

    # Sauvegarder
    output_file = OUTPUT_PATH / "audit_models_report.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    # Afficher le résumé
    print("\n" + "=" * 50)
    print("📊 RÉSUMÉ DE L'AUDIT")
    print("=" * 50)
    print(f"  Apps:     {summary['total_apps']}")
    print(f"  Modèles:  {summary['total_models']}")
    print(f"  Champs:   {summary['total_fields']}")
    print(f"  Fichiers: {summary['total_files']}")
    print(f"  Lignes:   {summary['total_lines']}")
    print(f"  Tests:    {summary['test_coverage_apps']} apps")
    print(f"  API:      {summary['api_coverage_apps']} apps")
    print(f"\n✅ Rapport sauvegardé: {output_file}")

    return report


if __name__ == "__main__":
    main()
