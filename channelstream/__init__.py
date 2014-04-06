from gevent import monkey
monkey.patch_all()

from datetime import datetime
from gevent.lock import RLock
total_messages = 0
total_unique_messages = 0
started_on = datetime.utcnow()

lock = RLock()