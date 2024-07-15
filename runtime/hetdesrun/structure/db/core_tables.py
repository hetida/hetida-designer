from sqlalchemy import DateTime, Float, String
from sqlalchemy.sql.type_api import TypeEngine

from hetdesrun.structure.db.core_service import create_property_table

# just examples:
prop_adresse_columns: list[tuple[str, TypeEngine]] = [
    ("entity", String(100)),
    ("entity_uuid", String(36)),
    ("valid_from", DateTime()),
    ("valid_to", DateTime()),
    ("strasse", String(255)),
    ("plz", String(10)),
    ("ort", String(100)),
]
prop_adresse_table = create_property_table("prop_adresse", prop_adresse_columns)

prop_pumpenparam_columns: list[tuple[str, TypeEngine]] = [
    ("entity", String(100)),
    ("entity_uuid", String(36)),
    ("valid_from", DateTime()),
    ("valid_to", DateTime()),
    ("foerderleistung_max", Float()),
    ("foerderhoehe", Float()),
]
prop_pumpenparam_table = create_property_table("prop_pumpenparam", prop_pumpenparam_columns)
