from  django.conf.urls import url
from django.contrib.auth import views as auth_views
from django.urls import reverse_lazy

from . import views

app_name = 'account'

urlpatterns = [  # previous login view
    url(r'^login1/$', views.user_login, name='login'),
    url(r'^login/$', auth_views.LoginView.as_view(), name='login'),
    url(r'^logout/$', auth_views.LogoutView.as_view(), name='logout'),
    url(r'^logout_then_login/$', auth_views.logout_then_login,
        name='logout_then_login'),  # change password urls
    url(r'^password_change/$', auth_views.PasswordChangeView.as_view(
        success_url=reverse_lazy('account:password_change_done')),
        name='password_change'),
    url(r'^password_change/done/$', auth_views.PasswordChangeDoneView.as_view(),
        name='password_change_done'),
    url(r'^password_reset/$', views.PasswordReset.as_view(),
        name='password_reset'),
    url(r'^password_reset/done/$', auth_views.PasswordResetDoneView.as_view(),
        name='password_reset_done'),
    url(r'^password_reset/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>.+)/$',
        views.PasswordResetConfirm.as_view(), name='password_reset_confirm'),
    url(r'^password_reset/complete/$',
        auth_views.PasswordResetCompleteView.as_view(),
        name='password_reset_complete'),
    url(r'^$', views.dashboard, name='dashboard'),
    url(r'^register/$',views.register,name='register'),
    url(r'^edit/$', views.edit, name='edit'),
    ]
