# addresses/management/commands/seed_addresses.py

from django.core.management.base import BaseCommand
from django.core.management import call_command


class Command(BaseCommand):
    help = "Seed all Nepal address data (province → district → municipality → ward)"

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE("🚀 Seeding Nepal address data..."))

        try:
            self.stdout.write("→ Seeding provinces...")
            call_command("seed_provinces")

            self.stdout.write("→ Seeding districts...")
            call_command("seed_districts")

            self.stdout.write("→ Seeding municipalities...")
            call_command("seed_municipalities")

            self.stdout.write("→ Seeding wards...")
            call_command("seed_wards")

        except Exception as e:
            self.stderr.write(self.style.ERROR("Address seeding failed"))
            self.stderr.write(self.style.ERROR(str(e)))
            return

        self.stdout.write(self.style.SUCCESS("All address data seeded successfully"))
