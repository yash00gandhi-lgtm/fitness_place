from django.conf import settings
from django.db import models
from django.utils import timezone
from dateutil.relativedelta import relativedelta


class Plan(models.Model):
    name = models.CharField(max_length=100)
    price = models.IntegerField()
    duration = models.IntegerField(help_text="Duration in months")

    def __str__(self):
        return self.name


class Membership(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('active', 'Active'),
        ('expired', 'Expired'),
        ('cancelled', 'Cancelled'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    plan = models.ForeignKey(Plan, on_delete=models.PROTECT)

    order_id = models.CharField(max_length=200, blank=True, null=True)
    payment_id = models.CharField(max_length=200, blank=True, null=True)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    start_date = models.DateField(blank=True, null=True)
    end_date = models.DateField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def activate(self):
        """Payment success ke baad member activate hoga."""
        if not self.start_date:
            self.start_date = timezone.now().date()

        # plan.duration = number of months
        if self.plan.duration:
            self.end_date = self.start_date + relativedelta(months=self.plan.duration)

        self.status = 'active'
        self.save()

    def __str__(self):
        return f"{self.user} - {self.plan} ({self.status})"
    
class Invoice(models.Model):
    membership = models.OneToOneField('Membership', on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    invoice_number = models.CharField(max_length=50, unique=True)
    amount = models.DecimalField(max_digits=8, decimal_places=2)

    razorpay_payment_id = models.CharField(max_length=100, blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.invoice_number
    
class Lead(models.Model):
    STATUS_CHOICES = [
        ("new", "New"),
        ("contacted", "Contacted"),
        ("joined", "Joined"),
        ("lost", "Lost"),
    ]

    name = models.CharField(max_length=100)
    phone = models.CharField(max_length=15)
    
    goal = models.CharField(max_length=100, blank=True, null=True)
    source = models.CharField(max_length=100, blank=True, null=True)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="new")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class ReminderLog(models.Model):
    membership = models.ForeignKey(Membership, on_delete=models.CASCADE)
    reminder_type = models.CharField(max_length=20)  # "3day", "1day", "expiry"
    sent_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.membership.id} - {self.reminder_type}"
    

class TrialBooking(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("confirmed", "Confirmed"),
        ("completed", "Completed"),
        ("not_interested", "Not Interested"),
    ]

    name = models.CharField(max_length=100)
    phone = models.CharField(max_length=15)
    preferred_time = models.CharField(max_length=50)
    goal = models.CharField(max_length=200, blank=True, null=True)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} - {self.phone}"


