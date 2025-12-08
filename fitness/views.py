from django.shortcuts import render, HttpResponse, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login as auth_login
from django.conf import settings
from django.utils import timezone
from django.http import HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
from .models import TrialBooking
import razorpay
from datetime import timedelta
from django.db import models  
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required

# MODELS
from .models import Plan, Membership, Invoice, Lead, ReminderLog


# --------------------------------------------------
# WHATSAPP PLACEHOLDER 
# --------------------------------------------------
def send_whatsapp_message(phone, message):
    print(f"[WHATSAPP] To: {phone} | Msg: {message}")


# --------------------------------------------------
# BASIC PAGES
# --------------------------------------------------
def index(request):
    return render(request, 'index.html')


def contact(request):
    if request.method == "POST":
        name = request.POST.get("name")
        phone = request.POST.get("phone")
        message = request.POST.get("message")

        if not name or not phone:
            messages.error(request, "Please enter your name and phone number.")
            return redirect("contact")

        Lead.objects.create(
            name=name,
            phone=phone,
            goal=message,
            source="Contact Page",
        )

        messages.success(request, "Thank you! Our team will contact you soon.")
        return redirect("contact")

    return render(request, "contact.html")


def about(request):
    return render(request, 'about.html')


def services(request):
    return HttpResponse("hey this is Services page")


def trainer(request):
    return render(request, 'trainer.html')


def membership(request):
    return plans(request)


# --------------------------------------------------
# SIGNUP
# --------------------------------------------------
def signup(request):
    next_url = request.GET.get('next') or request.POST.get('next')

    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            auth_login(request, user)

            if next_url:
                return redirect(next_url)
            return redirect('plans')
    else:
        form = UserCreationForm()

    return render(request, 'signup.html', {"form": form, "next": next_url})


# --------------------------------------------------
# PLANS PAGE
# --------------------------------------------------
def plans(request):
    all_plans = Plan.objects.all()
    return render(request, "member.html", {"plans": all_plans})


# --------------------------------------------------
# CREATE ORDER
# --------------------------------------------------
@login_required
def create_order(request, plan_id):
    plan = get_object_or_404(Plan, id=plan_id)

    client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID,
                                   settings.RAZORPAY_KEY_SECRET))

    amount_paise = int(plan.price) * 100

    order = client.order.create({
        "amount": amount_paise,
        "currency": "INR",
        "payment_capture": 1,
    })

    membership = Membership.objects.create(
        user=request.user,
        plan=plan,
        order_id=order["id"],
        status='pending'
    )

    return render(request, "checkout.html", {
        "plan": plan,
        "order": order,
        "membership": membership,
        "razorpay_key_id": settings.RAZORPAY_KEY_ID,
    })


# --------------------------------------------------
# PAYMENT SUCCESS (ACTIVATE MEMBERSHIP + REDIRECT TO INVOICE)
# --------------------------------------------------
@csrf_exempt
def payment_success(request):
    if request.method != "POST":
        return HttpResponseBadRequest("Invalid request")

    razorpay_payment_id = request.POST.get("razorpay_payment_id")
    razorpay_order_id = request.POST.get("razorpay_order_id")
    razorpay_signature = request.POST.get("razorpay_signature")

    if not all([razorpay_payment_id, razorpay_order_id, razorpay_signature]):
        return HttpResponseBadRequest("Missing parameters")

    client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID,
                                   settings.RAZORPAY_KEY_SECRET))

    params_dict = {
        "razorpay_order_id": razorpay_order_id,
        "razorpay_payment_id": razorpay_payment_id,
        "razorpay_signature": razorpay_signature,
    }

    try:
        client.utility.verify_payment_signature(params_dict)
    except razorpay.errors.SignatureVerificationError:
        return HttpResponseBadRequest("Signature verification failed")

    membership = get_object_or_404(Membership, order_id=razorpay_order_id)
    membership.payment_id = razorpay_payment_id
    membership.activate()

    ReminderLog.objects.filter(membership=membership).delete()

    # ⭐ Redirect to correct invoice immediately
    return redirect("generate_invoice", membership_id=membership.id)


# --------------------------------------------------
# USER MEMBERSHIP DASHBOARD  (LATEST ACTIVE MEMBERSHIP)
# --------------------------------------------------
@login_required
def membership_dashboard(request):
    membership = Membership.objects.filter(
        user=request.user,
        status='active'
    ).order_by('-id').first()   # ⭐ FIXED HERE

    days_left = None
    if membership and membership.end_date:
        days_left = (membership.end_date - timezone.now().date()).days

    return render(request, "membership_dashboard.html", {
        "membership": membership,
        "days_left": days_left,
    })


# --------------------------------------------------
# INVOICE VIEW
# --------------------------------------------------
@login_required
def generate_invoice(request, membership_id):
    membership = get_object_or_404(Membership, id=membership_id, user=request.user)

    date_str = timezone.now().strftime("%Y%m%d")
    invoice_no = f"INV-{date_str}-{membership.id}"

    invoice, created = Invoice.objects.get_or_create(
        membership=membership,
        defaults={
            "user": request.user,
            "amount": membership.plan.price,
            "invoice_number": invoice_no,
        }
    )

    return render(request, "invoice.html", {"invoice": invoice})


# --------------------------------------------------
# OWNER DASHBOARD
# --------------------------------------------------
@staff_member_required
def owner_dashboard(request):
    today = timezone.now().date()
    week_later = today + timedelta(days=7)

    total_active = Membership.objects.filter(status='active').count()
    expiring_soon = Membership.objects.filter(end_date__lte=week_later, end_date__gte=today).count()

    month_start = today.replace(day=1)
    monthly_revenue = Invoice.objects.filter(
        created_at__date__gte=month_start
    ).aggregate(models.Sum('amount'))['amount__sum'] or 0

    leads_this_week = Lead.objects.filter(
        created_at__gte=today - timedelta(days=7)
    ).count()

    expiring_list = Membership.objects.filter(
        end_date__lte=week_later, end_date__gte=today
    ).order_by('end_date')[:10]

    recent_payments = Invoice.objects.order_by('-created_at')[:10]
    recent_leads = Lead.objects.order_by('-created_at')[:10]

    return render(request, "owner_dashboard.html", {
        "total_active": total_active,
        "expiring_soon": expiring_soon,
        "monthly_revenue": monthly_revenue,
        "leads_this_week": leads_this_week,
        "expiring_list": expiring_list,
        "recent_payments": recent_payments,
        "recent_leads": recent_leads,
    })


# --------------------------------------------------
# LEAD FORM
# --------------------------------------------------
def lead_form(request):
    if request.method == "POST":
        Lead.objects.create(
            name=request.POST.get("name"),
            phone=request.POST.get("phone"),
            goal=request.POST.get("goal"),
            source=request.POST.get("source")
        )
        return render(request, "lead_success.html")

    return render(request, "lead_form.html")


@staff_member_required
def owner_leads(request):
    leads = Lead.objects.order_by('-created_at')
    return render(request, "owner_leads.html", {"leads": leads})


# --------------------------------------------------
# REMINDER SYSTEM
# --------------------------------------------------
def send_expiry_reminders(request):
    today = timezone.now().date()
    memberships = Membership.objects.filter(status="active")

    for m in memberships:
        days_left = (m.end_date - today).days
        phone = m.user.username

        if days_left == 3:
            if not ReminderLog.objects.filter(membership=m, reminder_type="3day").exists():
                send_whatsapp_message(phone, "Your gym membership expires in 3 days. Renew soon!")
                ReminderLog.objects.create(membership=m, reminder_type="3day")

        if days_left == 1:
            if not ReminderLog.objects.filter(membership=m, reminder_type="1day").exists():
                send_whatsapp_message(phone, "Reminder: Your membership expires tomorrow.")
                ReminderLog.objects.create(membership=m, reminder_type="1day")

        if days_left == 0:
            if not ReminderLog.objects.filter(membership=m, reminder_type="expiry").exists():
                send_whatsapp_message(phone, "Your membership expires today. Renew anytime!")
                ReminderLog.objects.create(membership=m, reminder_type="expiry")

    return render(request, "reminder_done.html")


# --------------------------------------------------
# TRIAL BOOKING
# --------------------------------------------------
def trial_booking(request):
    if request.method == "POST":
        name = request.POST.get("name")
        phone = request.POST.get("phone")
        preferred_time = request.POST.get("time")
        goal = request.POST.get("goal")

        if TrialBooking.objects.filter(phone=phone).exists():
            return render(request, "trial_error.html", {
                "msg": "You have already used your FREE Trial!"
            })

        trial = TrialBooking.objects.create(
            name=name,
            phone=phone,
            preferred_time=preferred_time,
            goal=goal
        )

        Lead.objects.create(
            name=name,
            phone=phone,
            goal=goal,
            source="Trial Booking"
        )

        return render(request, "trial_success.html")

    return render(request, "trial_form.html")


@staff_member_required
def owner_trials(request):
    trials = TrialBooking.objects.order_by('-created_at')
    return render(request, "owner_trials.html", {"trials": trials})
