class FirmProfileService:

    @staticmethod
    def update_profile(firm, data):
        services = data.pop("services", None)

        for attr, value in data.items():
            setattr(firm, attr, value)

        firm.save()

        if services is not None:
            firm.services.set(services)

        return firm
