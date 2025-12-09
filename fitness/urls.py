from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='home'),
    path('about/', views.about, name='about'),
    path('contact/', views.contact, name='contact'),
    path('services/', views.services, name='services'),
    
    path("lead/", views.lead_form, name="lead_form"),
    path("owner/leads/", views.owner_leads, name="owner_leads"),
    path("run/reminders/", views.send_expiry_reminders, name="send_expiry_reminders"),
    path("trial/", views.trial_booking, name="trial_booking"),
    path("owner/trials/", views.owner_trials, name="owner_trials"),
    path('membership/', views.plans, name='plans'),
    path('signup/', views.signup, name='signup'),
    path('payment/success/', views.payment_success, name='payment_success'),
    path("create-order/<int:plan_id>/", views.create_order, name="create_order"),

    path('my/membership/', views.membership_dashboard, name='membership_dashboard'),
    path("invoice/<int:membership_id>/", views.generate_invoice, name="generate_invoice"),
    path("owner/dashboard/", views.owner_dashboard, name="owner_dashboard"),

]

   

   

 
