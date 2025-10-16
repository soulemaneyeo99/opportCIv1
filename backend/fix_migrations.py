#!/usr/bin/env python3
import os
import re
from pathlib import Path

def fix_migrations():
    apps = ['accounts', 'opportunities', 'courses', 'formations', 'credibility', 'notifications']
    
    for app in apps:
        migrations_dir = Path('backend/apps') / app / 'migrations'
        
        if not migrations_dir.exists():
            continue
        
        for file in migrations_dir.glob('*.py'):
            if file.name == '__init__.py':
                continue
            
            content = file.read_text()
            
            # Corrections
            content = content.replace(f'import {app}.models', f'import apps.{app}.models')
            content = content.replace(f'from {app}.models', f'from apps.{app}.models')
            content = re.sub(rf"'{app}\.", f"'apps.{app}.", content)
            
            file.write_text(content)
            print(f"✅ {file}")

if __name__ == '__main__':
    fix_migrations()
