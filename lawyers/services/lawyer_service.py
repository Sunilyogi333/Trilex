from lawyers.models import Lawyer


class LawyerService:

    @staticmethod
    def update_services(lawyer, services):
        lawyer.services.set(services)
        lawyer.save()
        return lawyer
