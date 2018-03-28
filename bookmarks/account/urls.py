from  django.conf.urls import url
from django.contrib.auth.views import LoginView, LogoutView, logout_then_login
from django.contrib.auth.views import PasswordChangeDoneView
from django.contrib.auth.views import PasswordResetCompleteView
from django.contrib.auth.views import PasswordResetDoneView

from . import views

urlpatterns = [  # previous login view
    # url(r'^login/$', views.user_login, name='login'),
    # login / logout urls
    url(r'^login/$', LoginView.as_view(), name='login'),
    url(r'^logout/$', LogoutView.as_view(), name='logout'),
    url(r'^logout_then_login/$', logout_then_login, name='logout_then_login'),
    url(r'^$', views.dashboard, name='dashboard'),
    url(r'^password_change/$', views.PasswordChange.as_view(),
        name='password_change'),
    url(r'^password_change/done/$', PasswordChangeDoneView.as_view(),
        name='password_change_done'),
    url(r'^password_reset/$', views.PasswordReset.as_view(),
        name='password_reset'),
    url(r'^password_reset/done/$', PasswordResetDoneView.as_view(),
        name='password_reset_done'),
    url(r'^password_reset/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>.+)/$',
        views.PasswordResetConfirm.as_view(), name='password_reset_confirm'),
    url(r'^password_reset/complete/$', PasswordResetCompleteView.as_view(),
        name='password_reset_complete'),
    url(r'^register/$', views.register, name='register'),
    url(r'^edit/$', views.edit, name='edit'),
    url(r'^users/$', views.user_list, name='user_list'),
    url(r'^users/follow/$', views.user_follow, name='user_follow'),
    url(r'^users/(?P<username>[-\w]+)/$', views.user_detail,
        name='user_detail'),]
