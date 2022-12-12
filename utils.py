import json


def get_reservable_sites():
    with open("sites.json", "r") as f:
        sites_dict = json.load(f)

    return sites_dict['reservable_sites']
