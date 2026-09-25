from django.contrib import admin
from django.urls import include, path


urlpatterns = [
    path("admin/",admin.site.urls,),
    path("api/auth/",include("accounts.urls"),),
path("api/dashboard/",include("dashboard.urls"),),
path("api/resume-builder/",include("resume_builder.urls"),),
      path("api/interview-prep/",include("interview_prep.urls"),),
        path("api/settings/",include("settings_app.urls"),),
   ]