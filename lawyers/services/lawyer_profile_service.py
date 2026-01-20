class LawyerProfileService:

    @staticmethod
    def update_profile(lawyer, data):
        services = data.pop("services", None)

        for attr, value in data.items():
            setattr(lawyer, attr, value)

        lawyer.save()

        if services is not None:
            lawyer.services.set(services)

        return lawyer
