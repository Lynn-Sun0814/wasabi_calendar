"""webapps URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from wasabicalendar import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.profile_action, name='home'),
    path('oauth/', include('social_django.urls', namespace='social')),
    path('profile', views.profile_action, name='profile'),
    path('create_calendar', views.create_calendar, name='create_calendar'),
    path('get_calendar/<int:id>', views.get_calendar, name='get_calendar'),
    path('add_member/<int:id>', views.add_member, name='member'),
    path('add_tag/<int:id>', views.add_tag, name='tag'),
    path('new_task/<int:id>', views.new_task, name='new_task'),
    path('create_task/<int:id>', views.create_task, name='create_task'),
    path('back/<int:id>', views.back, name='back'),
    path('modify_task/<int:id>', views.modify_task, name='modify_task'),
    path('modify_helper/<int:id>', views.modify_helper, name='modify_helper'),
    path('delete_helper/<int:id>', views.delete_helper, name='delete_helper'),
    path('logout', auth_views.logout_then_login, name='logout'),
    path('wasabicalendar/get-task', views.get_task, name= 'get_task'),
    path('get_calendar/wasabicalendar/modify_helper/<int:id>', views.modify_helper, name='modify_helper'),
    path('wasabicalendar/get-cal-list', views.get_cal_list_wrapper, name='cal_list'),
    path('get_calendar/wasabicalendar/get-cal-list', views.get_cal_list_wrapper, name='get_cal_list'),
    path('add_member/wasabicalendar/get-cal-list', views.get_cal_list_wrapper, name='get_cal_list_member'),
    path('add_tag/wasabicalendar/get-cal-list', views.get_cal_list_wrapper, name='get_cal_list_tag'),
    path('back/wasabicalendar/get-cal-list', views.get_cal_list_wrapper, name='get_cal_list_back'),
    path('create_task/wasabicalendar/get-cal-list', views.get_cal_list_wrapper, name='get_cal_list_create_task'),
    path('wasabicalendar/flip-block', views.flip_block, name='flip-block'),
    path('get_calendar/wasabicalendar/flip-block', views.flip_block, name='get_flip_block'),
    path('wasabicalendar/prev-week', views.prev_week, name = 'prev_week'),
    path('wasabicalendar/next-week', views.next_week, name = 'next_week'),
    path('get_calendar/wasabicalendar/prev-week', views.prev_week, name = 'prev_week'),
    path('get_calendar/wasabicalendar/next-week', views.next_week, name = 'next_week'),
    path('get_calendar/wasabicalendar/get-task', views.get_task, name= 'get_task')
]
