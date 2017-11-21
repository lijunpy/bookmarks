# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib.auth import authenticate, login
from django.http import HttpResponse
from django.shortcuts import render

from .forms import LoginForm


# Create your views here.
def user_login(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            user = authenticate(username=cd['username'],
                                password=cd['password'])
            if user is not None:
                if user.is_active:
                    login(request, user)
                    return HttpResponse('Authenticated successfully')
                else:
                    return HttpResponse('Disabled account')
            else:
                return HttpResponse('Invalid login')
        else:
            form = LoginForm()
            return render(request, 'account/login.html', {'form': form})


from django.urls import reverse_lazy
from django.contrib.auth.views import PasswordChangeView

class PasswordChange(PasswordChangeView):
    success_url = reverse_lazy('account:password_change_done')


from django.contrib.auth.views import PasswordResetView,PasswordResetConfirmView


class PasswordReset(PasswordResetView):
    from_email = 'email-username@hotmail.com'
    html_email_template_name = 'registration/password_reset_email.html'
    success_url = reverse_lazy('account:password_reset_done')


class PasswordResetConfirm(PasswordResetConfirmView):
    success_url = reverse_lazy('account:password_reset_complete')


from django.contrib.auth.decorators import login_required


@login_required
def dashboard(request):
    return render(request, 'account/dashboard.html', {'section': 'dashboard'})