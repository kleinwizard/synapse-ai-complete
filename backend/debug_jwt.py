from jose import jwt
import os
from datetime import datetime

JWT_SECRET_KEY = 'dev_jwt_secret_key_12345_this_should_be_changed_in_production'
token = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOjEsImV4cCI6MTc1NDY0NDg1OX0.IE7clbS2oEg52q7HXncjH4SHLK4F6s2yEYU3kaAbens'

try:
    payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=['HS256'])
    print('Token decoded successfully:', payload)
    print('Current timestamp:', int(datetime.utcnow().timestamp()))
    print('Token expiry:', payload.get('exp'))
    exp = payload.get('exp')
    if exp:
        print('Token valid:', exp > int(datetime.utcnow().timestamp()))
    else:
        print('No expiry found in token')
except Exception as e:
    print('Token decode error:', e)
