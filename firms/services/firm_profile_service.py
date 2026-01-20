from addresses.services.address_service import AddressService

class FirmProfileService:

    @staticmethod
    def update_profile(firm, data):
        services = data.pop("services", None)
        address_data = data.pop("address", None)

        for attr, value in data.items():
            setattr(firm, attr, value)

        if address_data:
            if firm.address:
                AddressService.update(firm.address.id, address_data)
            else:
                firm.address = AddressService.create(address_data)

        firm.save()

        if services is not None:
            firm.services.set(services)

        return firm
