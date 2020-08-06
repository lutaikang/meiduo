from django.http import HttpResponse

# Create your views here.
from django.views import View
from django_redis import get_redis_connection

from verifications.captcha.captcha import captcha


class ImageCodeView(View):
    """生成图形验证码"""
    def get(self, request, uuid):
        """
        :param request: 请求对象
        :param uuid: 唯一标识图形验证码属于哪个用户
        :return: image/jpg
        """
        text, image = captcha.generate_captcha()

        redis_conn = get_redis_connection()
        redis_conn.setex('img_%s' % uuid, 300, text)

        return HttpResponse(image, content_type='image/jpg')