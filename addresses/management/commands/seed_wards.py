# addresses/management/commands/seed_wards.py

from django.core.management.base import BaseCommand
from django.db import connection
from pathlib import Path


class Command(BaseCommand):
    help = "Seed Nepal wards"

    def handle(self, *args, **options):
        sql_file = Path(__file__).resolve().parent.parent.parent / "seeds" / "ward.sql"

        if not sql_file.exists():
            self.stderr.write(self.style.ERROR("ward.sql not found"))
            return

        with connection.cursor() as cursor:
            cursor.execute(sql_file.read_text())

        self.stdout.write(self.style.SUCCESS("Wards seeded successfully"))
