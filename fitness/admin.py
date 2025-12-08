from django.contrib import admin
from .models import (
    Plan,
    Membership,
    Invoice,
    Lead,
    ReminderLog,
    TrialBooking,
)


@admin.register(Plan)
class PlanAdmin(admin.ModelAdmin):
    list_display = ("name", "price", "duration")
    search_fields = ("name",)
    list_filter = ("duration",)


@admin.register(Membership)
class MembershipAdmin(admin.ModelAdmin):
    list_display = ("user", "plan", "status", "start_date", "end_date", "created_at")
    list_filter = ("status", "plan", "start_date", "end_date")
    search_fields = ("user__username", "user__email", "plan__name")
    readonly_fields = ("created_at",)


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ("invoice_number", "user", "membership", "amount", "created_at")
    search_fields = ("invoice_number", "user__username", "user__email")
    list_filter = ("created_at",)


@admin.register(Lead)
class LeadAdmin(admin.ModelAdmin):
    list_display = ("name", "phone", "goal", "source", "status", "created_at")
    search_fields = ("name", "phone")
    list_filter = ("status", "source", "created_at")


@admin.register(ReminderLog)
class ReminderLogAdmin(admin.ModelAdmin):
    list_display = ("membership", "reminder_type", "sent_at")
    list_filter = ("reminder_type", "sent_at")
    search_fields = ("membership__user__username",)


@admin.register(TrialBooking)
class TrialBookingAdmin(admin.ModelAdmin):
    list_display = ("name", "phone", "preferred_time", "status", "created_at")
    search_fields = ("name", "phone")
    list_filter = ("status", "preferred_time", "created_at")
