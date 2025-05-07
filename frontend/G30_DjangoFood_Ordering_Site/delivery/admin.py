# from django.contrib import admin
# from .models import Rider
# from .models import ContactMessage  # Import the model
# class RiderAdmin(admin.ModelAdmin):
#     list_display = ('name', 'email', 'is_approved', 'created_at')
#     list_filter = ('is_approved',)
#     search_fields = ('name', 'email')

#     def get_queryset(self, request):
#         queryset = super().get_queryset(request)
#         if not request.user.is_superuser:
#             queryset = queryset.filter(is_approved=False)  # Show only unapproved riders for regular users
#         return queryset

#     def approve_rider(self, request, rider_id):
#         rider = Rider.objects.get(id=rider_id)
#         rider.is_approved = True
#         rider.save()
#         return HttpResponse("Rider approved successfully.")

# admin.site.register(Rider, RiderAdmin)

# from django.contrib import admin
# from .models import ContactMessage  # Import the model

# # Define an admin class to customize the admin view (optional)
# class ContactMessageAdmin(admin.ModelAdmin):
#     list_display = ('name', 'email', 'subject', 'created_at')
#     search_fields = ('name', 'email', 'subject', 'message')
#     list_filter = ('created_at',)

# # Register the model with its admin class
# admin.site.register(ContactMessage, ContactMessageAdmin)

# delivery/admin.py
from django.contrib import admin
from .models import Rider

@admin.register(Rider)
class RiderAdmin(admin.ModelAdmin):
    list_display = ['name', 'email', 'is_approved', 'on_duty', 'created_at']
    list_filter = ['is_approved', 'on_duty']
    search_fields = ['name', 'email']
    actions = ['approve_rider', 'deactivate_rider']

    def approve_rider(self, request, queryset):
        queryset.update(is_approved=True)
    approve_rider.short_description = "Approve selected riders"

    def deactivate_rider(self, request, queryset):
        queryset.update(on_duty=False)
    deactivate_rider.short_description = "Deactivate selected riders"
