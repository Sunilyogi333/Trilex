class FirmService:

    @staticmethod
    def update_services(firm, services):
        firm.services.set(services)
        firm.save()
        return firm
