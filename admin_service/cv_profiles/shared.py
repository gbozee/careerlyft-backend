
class GeneralMixin(object):
    actions = ["delete_user"]

    def delete_user(self, request, queryset):
        queryset.all().delete()
        self.message_user(request, "Users deleted")

    def get_actions(self, request):
        actions = super().get_actions(request)
        del actions['delete_selected']
        return actions

