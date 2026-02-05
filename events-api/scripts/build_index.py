import os
import sys


def main():
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "events_api.settings")
    import django

    django.setup()
    from events.recommender import build_index

    result = build_index()
    print(result)


if __name__ == "__main__":
    main()
