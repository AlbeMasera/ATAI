from speakeasypy.src.speakeasy import Speakeasy
from speakeasypy.src.chatroom import Chatroom


speakeasy = Speakeasy(host='https://speakeasy.ifi.uzh.ch', username='kindle-pizzicato-wheat_bot', password='zJD7llj0A010Zg')
speakeasy.login()

# Only check active chatrooms (i.e., remaining_time > 0) if active=True.
rooms = speakeasy.get_rooms(active=True)
