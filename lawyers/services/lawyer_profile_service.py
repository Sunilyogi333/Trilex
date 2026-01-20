from addresses.services.address_service import AddressService

class LawyerProfileService:

    @staticmethod
    def update_profile(lawyer, data):
        services = data.pop("services", None)
        address_data = data.pop("address", None)

        # Simple fields
        for attr, value in data.items():
            setattr(lawyer, attr, value)

        # Address handling
        if address_data:
            address = AddressService.update(
                lawyer.address.id,
                address_data
            )
            lawyer.address = address

        lawyer.save()

        if services is not None:
            lawyer.services.set(services)

        return lawyer
