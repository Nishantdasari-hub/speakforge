from slowapi import Limiter
from slowapi.util import get_remote_address

# The supported deployment runs one API worker; configure shared storage before scaling it.
limiter = Limiter(key_func=get_remote_address)
