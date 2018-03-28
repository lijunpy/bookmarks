# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from actions.utils import create_action
from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.http import HttpResponse
from django.shortcuts import render

from .models import Profile


# messages.error(request,'Something Went wrong')

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


from django.contrib.auth.views import PasswordResetView, \
    PasswordResetConfirmView


class PasswordReset(PasswordResetView):
    from_email = 'email-username@hotmail.com'
    html_email_template_name = 'registration/password_reset_email.html'
    success_url = reverse_lazy('account:password_reset_done')


class PasswordResetConfirm(PasswordResetConfirmView):
    success_url = reverse_lazy('account:password_reset_complete')


def register(request):
    if request.method == 'POST':
        user_form = UserRegistrationForm(request.POST)
        if user_form.is_valid():
            # create a new user object but avoid saving it yet
            new_user = user_form.save(commit=False)
            # set the chosen password
            new_user.set_password(user_form.cleaned_data['password'])
            new_user.save()
            # save the User object
            profile = Profile.objects.create(user=new_user)
            create_action(new_user, 'has created an account')
            return render(request, 'account/register_done.html',
                          {'new_user': new_user})
        else:
            return render(request, 'account/register.html',
                          {'user_form': user_form})
    else:
        user_form = UserRegistrationForm()
        return render(request, 'account/register.html',
                      {'user_form': user_form})


from django.contrib.auth.decorators import login_required
from .forms import LoginForm, UserRegistrationForm, UserEditForm, \
    ProfileEditForm


@login_required
def edit(request):
    if request.method == 'POST':
        user_form = UserEditForm(instance=request.user, data=request.POST)
        profile_form = ProfileEditForm(instance=request.user.profile,
                                       data=request.POST, files=request.FILES)
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, 'Profileupdated successfull')
    else:
        messages.error(request, 'Error updating your profile')
        user_form = UserEditForm(instance=request.user)
        profile_form = ProfileEditForm(instance=request.user.profile)
    return render(request, 'account/edit.html',
                  {'user_form': user_form, 'profile_form': profile_form})


from actions.models import Action


@login_required
def dashboard(request):
    # Diasplay all actions by default
    actions = Action.objects.exclude(user=request.user)
    following_ids = request.user.following.values_list('id', flat=True)
    if following_ids:
        # if user is following others, retrieve only their actions
        actions = actions.filter(user_id__in=following_ids).select_related(
            'user', 'user__profile').prefetch_related('target')
    actions = actions[:10]
    return render(request, 'account/dashboard.html',
                  {'section': 'dashboard', 'actions': actions})


from django.shortcuts import get_object_or_404
from django.contrib.auth.models import User


@login_required
def user_list(request):
    users = User.objects.filter(is_active=True, is_superuser=False)
    print users
    return render(request, 'account/user/list.html',
                  {'section': 'people', 'users': users})


@login_required
def user_detail(request, username):
    user = get_object_or_404(User, username=username, is_active=True)
    return render(request, 'account/user/detail.html',
                  {'section': 'people', 'user': user})


from django.http import JsonResponse
from django.views.decorators.http import require_POST
from common.decorators import ajax_required
from .models import Contact
from django.db import models


@ajax_required
@require_POST
@login_required
def user_follow(request):
    user_id = request.POST.get('id')
    action = request.POST.get('action')
    if user_id and action:
        try:
            user = User.objects.get(id=user_id)
            if action == 'follow':
                Contact.objects.get_or_create(user_from=request.user,
                                              user_to=user)
            else:
                Contact.objects.filter(user_from=request.user,
                                       user_to=user).delete()
            create_action(request.user, action, user)
            return JsonResponse({'status': 'ok'})
        except models.ObjectDoesNotExist:
            return JsonResponse({'status': 'ko'})
    return JsonResponse({'status': 'ko'})


    # from django.db.models import Count
    # from images.models import Image
    #
    # image_by_popularity = Image.objects.annotate(total_likes=Count('users_like')).order_by('-total_likes')
