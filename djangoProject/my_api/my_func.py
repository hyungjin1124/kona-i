import pandas as pd

def read_data():
    m_keywords_type = pd.read_csv('../data/211124_category_type_keyword.csv')
    cate_type = pd.read_csv('../data/main_menu_type_list.csv')

    return m_keywords_type, cate_type

def ext_info(m_keywords_type, cate_type, menu_list):
    main_cate = cate_type.main.to_list()
    not_main = [cate for cate in m_keywords_type if cate not in main_cate]
    m_keywords_type.drop(columns = not_main, inplace = True)

    total_list = []
    for menu in menu_list:
        res_dict = {}
        cate_list = []
        for col_name, keywords in m_keywords_type.iteritems():
            for key in keywords:
                if pd.isna(key):
                    break
                elif key in menu:
                    if col_name not in cate_list:
                        cate_list.append(col_name)
        res_dict[menu] = cate_list
        total_list.append(res_dict)
    
    return total_list

# def main():
#     m_keywords_type, cate_type = read_data()


# if __name__ == '__main__':
#     main()