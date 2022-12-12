from google.cloud import firestore
import json
import os

def get_all_reservations(db) -> dict:
    """Returns the reservations for all sites in the database.

    Args:
        db: Firebase database instance.

    Returns:
        dict: Nested dictionary of all reservation instances
    """

    # Let's make a reference to ALL of the posts
    posts_ref = db.collection("sites")

    # For a reference to a collection, we use .stream() instead of .get()
    all_reservations = {}
    for doc in posts_ref.stream():
        all_reservations[doc.id] = doc.to_dict()

    return all_reservations


def get_reservations_for_site(db, site: str) -> dict:
    """Fetches all reservations in the database for a specific site.

    Args:
        db: Firebase database instance.
        site (str): String of the site to remove the reservation from.

    Returns:
        reservation: Site reservations, as a dictionary. 
    """
    doc_ref = db.collection("sites").document(site)
    doc = doc_ref.get()  # Get data for document

    return doc.to_dict()

def cancel_reservation(db, site: str, reservation_key: str) -> bool:
    """Deletes a specific reservation.

    Args:
        db: Firebase database instance.
        site (str): String of the site to remove the reservation from.
        reservation_key (str): Reservation key, the starting date as a string.

    Returns:
        success: Boolean wether the deletion was a success (True), or not (False).
    """
    try:
        doc_ref = db.collection("sites").document(site)
        doc = doc_ref.get()  # Get data for document
        site_dict = doc.to_dict()
        del site_dict[reservation_key]
        doc_ref.set(site_dict)
        return True
    except:
        return False

def add_reservation_to_site(db, site: str, reservation: dict) -> bool:
    """Adds a reservation to a specific site's database.

    Args:
        db: Firebase database instance.
        site (str): String of the site to add the reservation to.
        reservation (dict): Dictionary containing the reservation information.

    Returns:
        success: Boolean wether the addition was a success (True), or not (False).
    """
    try:
        doc_ref = db.collection("sites").document(site)
        doc_ref.update(reservation)
        return True
    except:
        return False

def validate_reservation_is_possible(db, site: str, reservation: dict) -> bool:
    """Verifies if a given reservation is possible and not overlapping with existing ones.

    Args:
        db: Firebase database instance.
        site (str): String of the site to add the reservation to.
        reservation (dict): Dictionary containing the reservation information.

    Returns:
        success: Boolean wether the addition is possible (True), or not (False).
    """
    reservations = get_reservations_for_site(db, site)
    start = list(reservation.keys())[0]
    end = list(reservation.values())[0]["end"]
    for iter_start, vals in reservations.items():
        iter_end = vals["end"]
        cond1 = iter_end <= end and iter_end >= start
        cond2 = iter_start <= end and iter_start >= start
        if cond1 or cond2:
            return False
    return True


def connect_to_firebase_db_and_authenticate(project_name: str = None, local_auth_file: str = "firestore-key.json"):
    """Connects to a firebase project using a local authentication file, or using a streamlit toml secrets file.

    Args:
        project_name (str, optional): Firebase project name. Defaults to None.
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
        creds = service_account.Credentials.from_service_account_info(key_dict)
        db = firestore.Client(credentials=creds, project=project_name)

    # Other cases
    else:
        raise ConnectionError("Impossible to connect to firebase database.")
    return db
