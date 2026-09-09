# 
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import ResumeBuilderViewSet


router = DefaultRouter()

router.register(
    r"resumes",
    ResumeBuilderViewSet,
    basename="resume-builder",
)

urlpatterns = [path("",include(router.urls),),]