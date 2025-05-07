# from django.contrib import admin
# from .models import MenuItem
# from .models import Restaurant
# from .models import Order, OrderItem, MenuItem

# admin.site.register(MenuItem)
# admin.site.register(Restaurant)


# # Inline model for OrderItem
# class OrderItemInline(admin.TabularInline):
#     model = OrderItem
#     extra = 0  # No extra empty forms will be shown by default
#     fields = ('product', 'quantity', 'price')  # Fields to display in the inline

# # Custom admin for Order
# class OrderAdmin(admin.ModelAdmin):
#     list_display = ('id', 'user', 'status', 'full_name', 'email', 'total_price', 'created_at')  # Customize this based on your needs
#     search_fields = ('user__username', 'status', 'full_name', 'email')  # Search by user, status, full name, or email
#     inlines = [OrderItemInline]  # Include the OrderItem inline form in the Order form

# # Register Order and OrderItem models with the admin site
# admin.site.register(Order, OrderAdmin)
# admin.site.register(OrderItem)

# from .models import ContactMessage  # Import the model

# # Define an admin class to customize the admin view (optional)
# class ContactMessageAdmin(admin.ModelAdmin):
#     list_display = ('name', 'email', 'subject', 'created_at')
#     search_fields = ('name', 'email', 'subject', 'message')
#     list_filter = ('created_at',)

# # Register the model with its admin class
# admin.site.register(ContactMessage, ContactMessageAdmin)

