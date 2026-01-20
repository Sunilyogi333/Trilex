from cases.models import CaseCategory

class CaseCategoryService:

    @staticmethod
    def create_category(data):
        return CaseCategory.objects.create(**data)

    @staticmethod
    def get_all_categories(active_only=False):
        qs = CaseCategory.objects.all()
        if active_only:
            qs = qs.filter(is_active=True)
        return qs

    @staticmethod
    def get_category_by_id(category_id):
        return CaseCategory.objects.get(id=category_id)

    @staticmethod
    def update_category(instance, data):
        for attr, value in data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance

    @staticmethod
    def delete_category(instance):
        instance.soft_delete()
