from utils import get_reservable_sites
from db_utils import connect_to_firebase_db_and_authenticate

sites = get_reservable_sites()
all_sites = []
for v in sites.values():
    all_sites += list(v)

db = connect_to_firebase_db_and_authenticate()
reservation = {}

for site in all_sites:
    doc_ref = db.collection("sites").document(site)
    doc_ref.set(reservation)
