from itsdangerous import TimedJSONWebSignatureSerializer as Serializer, BadData
from django.conf import settings


def check_access_token(token):
    """解密"""
    serializer = Serializer(settings.SECRET_KEY, 300)
    try:
        date = serializer.loads(token)
    except BadData:
        return None
    return date['openid']


def generate_eccess_token(openid):
    """加密"""
    serializer = Serializer(settings.STATIC_KEY, 300)
    date = {'openid': openid}
    token = serializer.dumps(date)
    return token.decode()
