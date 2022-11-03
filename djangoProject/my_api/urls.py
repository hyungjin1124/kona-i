from django.urls import include, path
from rest_framework import routers
from my_api.views import MenuViewset

router = routers.DefaultRouter()
router.register(r'menu', MenuViewset)
# router.register(r'menu-kimchi', MenuViewset.menu_list)

urlpatterns = [
    path("", include(router.urls)),
]