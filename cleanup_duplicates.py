from main import engine, DailyTaskTemplate, Session, select
from collections import defaultdict

with Session(engine) as session:
    templates = session.exec(select(DailyTaskTemplate)).all()
    print(f'Found {len(templates)} total templates')
    
    # Group by name to find duplicates
    name_counts = defaultdict(list)
    for t in templates:
        name_counts[t.name].append(t)
    
    # Keep only the first one of each name, delete the rest
    deleted_count = 0
    for name, template_list in name_counts.items():
        if len(template_list) > 1:
            print(f'Found {len(template_list)} duplicates of "{name}"')
            # Keep the first one, delete the rest
            for template in template_list[1:]:
                session.delete(template)
                deleted_count += 1
    
    session.commit()
    print(f'Deleted {deleted_count} duplicate templates')
    
    # Show remaining templates
    remaining = session.exec(select(DailyTaskTemplate)).all()
    print(f'Remaining {len(remaining)} unique templates:')
    for t in remaining:
        print(f'- {t.name} ({t.task_type}, {t.priority})')
