"""(Pydantic) Models for ingoing / outgoing data"""
import re

from pydantic import ConstrainedStr

RESERVED_FILTER_KEY = ["from", "to", "id"]


class FilterKey(ConstrainedStr):
    min_length = 1
    regex = re.compile(r"^[a-zA-Z]\w+$", flags=re.ASCII)
