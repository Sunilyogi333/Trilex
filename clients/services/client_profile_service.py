from addresses.services.address_service import AddressService
from addresses.models.address import Address

class ClientProfileService:

    @staticmethod
    def update_profile(client, data):
        phone_number = data.get("phone_number")
        address_data = data.get("address")

        if phone_number is not None:
            client.phone_number = phone_number

        if address_data:
            if client.address:
                address = AddressService.update(
                    client.address.id,
                    address_data
                )
            else:
                address = AddressService.create(address_data)

            client.address = address

        client.save()
        return client
