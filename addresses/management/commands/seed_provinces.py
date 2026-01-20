# addresses/management/commands/seed_provinces.py

from django.core.management.base import BaseCommand
from django.db import connection
from pathlib import Path


class Command(BaseCommand):
    help = "Seed Nepal provinces"

    def handle(self, *args, **options):
        sql_file = Path(__file__).resolve().parent.parent.parent / "seeds" / "province.sql"

        if not sql_file.exists():
            self.stderr.write(self.style.ERROR("province.sql not found"))
            return

        with connection.cursor() as cursor:
            cursor.execute(sql_file.read_text())

        self.stdout.write(self.style.SUCCESS("Provinces seeded successfully"))
