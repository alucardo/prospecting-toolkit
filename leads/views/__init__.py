from .call_log import call_log_create, call_log_edit, call_log_delete
from .city import city_index, city_create, city_edit, city_delete, city_detail
from .dashboard import dashboard
from .import_file import import_upload, import_map
from .lead import lead_index, lead_create, lead_detail, lead_edit, lead_delete, lead_bulk_action, lead_scrape_email
from .lead_note import lead_note_create, lead_note_edit, lead_note_delete
from .lead_status_history import lead_status_history_delete
from .lead_contact import lead_contact_create, lead_contact_edit, lead_contact_delete
from .settings import settings