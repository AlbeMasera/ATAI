from speakeasypy.src.speakeasy import Speakeasy
from speakeasypy.src.chatroom import Chatroom


speakeasy = Speakeasy(host='https://speakeasy.ifi.uzh.ch', username='ecezeynep.asirim', password='qcje-6hLzZcNkA')
speakeasy.login()

# Only check active chatrooms (i.e., remaining_time > 0) if active=True.
rooms = speakeasy.get_rooms(active=True)
