import sys

sys.path.append("..")

from utils.files import update_resources_data, get_resource_list_data

update_resources_data()

data = get_resource_list_data()
print(type(data))
