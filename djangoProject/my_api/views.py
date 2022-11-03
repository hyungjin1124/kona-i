from django.shortcuts import render
from rest_framework import viewsets
from my_api.serializers import MenuSerializer
from my_api.models import Menu
from rest_framework.decorators import action
from rest_framework.response import Response
import pandas as pd
import json

# Create your views here.
class MenuViewset(viewsets.ModelViewSet):
    queryset = Menu.objects.all()
    serializer_class = MenuSerializer

    @action(detail=False, methods=['post'])
    def menu_list(self, request):
        req = json.loads(request.body)
        print(req)

        m_keywords_type, cate_type = read_data()

        result = {}
        id = 0
        for i in req:
            menu = i['menu']
            menuId = i['menuId']
            placeId = i['placeId']
            placeName = i['placeName']
            merchantId = i['merchantId']

            qs = self.queryset.filter(menu = menu, menuId = menuId, placeId = placeId, placeName = placeName, merchantId = merchantId)
            qs_dict = list(qs.values())[0]
            del qs_dict['id']

            type_list = ext_info(m_keywords_type, cate_type, menu)
            qs_dict['category'] = type_list

            result[str(id)] = qs_dict
            id += 1

        return Response(result)

def read_data():
    m_keywords_type = pd.read_csv('C:/Users/Hyungjink/djangoProject/data/211124_category_type_keyword.csv')
    cate_type = pd.read_csv('C:/Users/Hyungjink/djangoProject/data/main_menu_type_list.csv')

    return m_keywords_type, cate_type

def ext_info(m_keywords_type, cate_type, menu):
    main_cate = cate_type.main.to_list()
    not_main = [cate for cate in m_keywords_type if cate not in main_cate]
    m_keywords_type.drop(columns = not_main, inplace = True)

    cate_list = []
    for col_name, keywords in m_keywords_type.iteritems():
        for key in keywords:
            if pd.isna(key):
                break
            elif key in menu:
                if col_name not in cate_list:
                    cate_list.append(col_name)

    return cate_list