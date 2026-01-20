class ClientProfileService:

    @staticmethod
    def update_profile(client, data):
        for attr, value in data.items():
            setattr(client, attr, value)
        client.save()
        return client
