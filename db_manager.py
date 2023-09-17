import datetime as dt
import json
import os

import streamlit as st
from google.cloud import firestore
from google.oauth2 import service_account


def refresh_db(fn, threshold=60):
    def wrapper(*args, **kwargs):
        # Executed before function call
        self = args[0]
        now = dt.datetime.utcnow()
        delta = (self.db_timestamp - now).total_seconds() / 60
        if delta > threshold:
            self.connect_to_db_and_authenticate()
        args = (self, *args[1:])
        # Function call
        output = fn(*args, **kwargs)

        # After function call
        return output

    return wrapper


class DBManager:
    def __init__(self):
        self.connect_to_db_and_authenticate()

    def connect_to_db_and_authenticate(self, *args, **kwargs):
        self.db = connect_to_firebase_db_and_authenticate(*args, **kwargs)
        self.db_timestamp = dt.datetime.utcnow()

    def get_all_reservations(self) -> dict:
        return self._get_all_objects_in_collection("sites")

    def get_all_daily_prices(self) -> dict:
        all_prices = self._get_all_objects_in_collection("prices")
        return all_prices['daily_prices']
    
    def get_all_monthly_prices(self) -> dict:
        all_prices = self._get_all_objects_in_collection("prices")
        return all_prices['monthly_prices']

    def get_sites_list(self) -> list:
        return self._get_all_object_ids_in_collection("sites")

    def get_reservations_for_site(self, site_name: str) -> dict:
        return self._get_object_in_collection("sites", site_name)

    def update_sites_daily_prices(self, prices_dict:dict):
        return self._update_object_in_collection(
            collection_name="prices",
            object_name="daily_prices",
            new_data=prices_dict
        )
    def update_sites_monthly_prices(self, prices_dict:dict):
        return self._update_object_in_collection(
            collection_name="prices",
            object_name="monthly_prices",
            new_data=prices_dict
        )

    def add_reservation_to_site(self, site_name: str, reservation_data: dict):
        return self._update_object_in_collection(
            collection_name="sites",
            object_name=site_name,
            new_data=reservation_data,
        )

    def delete_reservation(self, site_name: str, reservation_key: str) -> dict:
        try:
            doc_ref = self.db.collection("sites").document(site_name)
            doc = doc_ref.get() 
            site_dict = doc.to_dict()
            del site_dict[reservation_key]
            doc_ref.set(site_dict)
            return True
        except:
            return False
    
    def validate_reservation_is_possible(self, site_name: str, reservation: dict) -> bool:
        """Verifies if a given reservation is possible and not overlapping with existing ones.

        Args:
            db: Firebase database instance.
            site (str): String of the site to add the reservation to.
            reservation (dict): Dictionary containing the reservation information.

        Returns:
            success: Boolean wether the addition is possible (True), or not (False).
        """
        reservations = self.get_reservations_for_site(site_name)
        start = list(reservation.keys())[0]
        end = list(reservation.values())[0]["end"]
        for iter_start, vals in reservations.items():
            iter_end = vals["end"]
            cond1 = start >= iter_start and start <= iter_end
            cond2 = end >= iter_start and end <= iter_end
            if cond1 or cond2:
                return False
        return True

    @refresh_db
    def _get_all_objects_in_collection(self, collection_name: str) -> dict:
        ref = self.db.collection(collection_name)
        all_objects_dict = {}
        for obj in ref.stream():
            all_objects_dict[obj.id] = obj.to_dict()
        return all_objects_dict

    @refresh_db
    def _create_new_object_in_collection(
        self, collection_name: str, object_name: str, data: dict
    ) -> dict:
        ref = self.db.collection(collection_name).document(object_name)
        ref.set(data)  # Get data for document

    @refresh_db
    def _get_all_object_ids_in_collection(self, collection_name: str) -> list:
        ref = self.db.collection(collection_name)
        object_names_list = []
        for obj in ref.stream():
            object_names_list.append(obj.id)
        return object_names_list

    @refresh_db
    def _get_object_in_collection(self, collection_name: str, object_name: str) -> dict:
        ref = self.db.collection(collection_name).document(object_name)
        obj = ref.get()  # Get data for document
        return obj.to_dict()

    @refresh_db
    def _update_object_in_collection(
        self, collection_name: str, object_name: str, new_data: dict
    ) -> dict:
        data = self._get_object_in_collection(
            collection_name=collection_name, object_name=object_name
        )
        data.update(new_data)
        self._create_new_object_in_collection(
            collection_name=collection_name, object_name=object_name, data=data
        )

    @refresh_db
    def _delete_object_in_collection(self, collection_name: str, object_name: str):
        ref = self.db.collection(collection_name).document(object_name)
        ref.set({})
        ref.delete()

    @refresh_db
    def _delete_all_objects_in_collection(self, collection_name: str):
        objects_list = self._get_all_object_ids_in_collection(collection_name)
        for obj in objects_list:
            self._delete_object_in_collection(
                collection_name=collection_name, object_name=obj
            )


def connect_to_firebase_db_and_authenticate(
    local_auth_file: str = "firestore-key.json",
) -> object:
    """Connects to a firebase project using a local authentication file,
    or using a streamlit toml secrets file.

    Args:
        local_auth_file (str, optional): Local authentication file. Defaults to "firestore-key.json".

    Returns:
        db: Firebase database object.
    """

    # Authenticate to Firestore with the JSON account key.
    if os.path.exists(local_auth_file):
        db = firestore.Client.from_service_account_json("firestore-key.json")

    # Authenticate with streamlit secrets
    elif "textkey" in st.secrets.keys():
        key_dict = json.loads(st.secrets["textkey"])
        with open("firestore-key.json", "w+") as f:
            json.dump(key_dict, f)

        # Old way apparently not working anymore - replaced by live json creation
        # creds = service_account.Credentials.from_service_account_info(key_dict)
        # db = firestore.Client(credentials=creds, project=project_name)
        db = firestore.Client.from_service_account_json("firestore-key.json")

    # Other cases
    else:
        raise ValueError("Impossible to access credentials for firebase database.")

    return db
