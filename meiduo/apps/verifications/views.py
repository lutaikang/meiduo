from random import random
from venv import logger

from django.http import HttpResponse, JsonResponse

# Create your views here.
from django.views import View
from django_redis import get_redis_connection

from meiduo.meiduo.utils.response_code import RETCODE
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

        redis_conn = get_redis_connection('verify_code')
        redis_conn.setex('img_%s' % uuid, 300, text)

        return HttpResponse(image, content_type='image/jpg')


class SMSCodeView(View):
    """短信验证码"""

    def get(self, request, mobile):
        image_code_client = request.GET.get('image_code')
        uuid = request.GET.get('uuid')

        if not all([image_code_client, uuid]):
            return JsonResponse({'code': RETCODE.IMAGECODEERR, 'errmsg': '图形验证码失效'})

        redis_conn = get_redis_connection('verify_code')
        image_code_server = redis_conn.pop('sms_%s' % uuid)

        if image_code_server is None:
            return JsonResponse({'code': RETCODE.IMAGECODEERR, 'errmsg': '图形验证码失效货已过期'})

        if image_code_client.lower() != image_code_server.decode().lower():
            return JsonResponse({'code': RETCODE.IMAGECODEERR, 'errmsg': '验证码错误'})

        sms_code = '%06d' % random.randint(0, 999999)
        logger.info(sms_code)

        redis_conn.setex('sms_%s' % sms_code, 300, sms_code)

        # 发送短信验证码
        CCP().send_template_sms(mobile, [sms_code, constants.SMS_CODE_REDIS_EXPIRES // 60],
                                constants.SEND_SMS_TEMPLATE_ID)

        return JsonResponse({'code': RETCODE.ok, 'errmsg': '发送短信成功'})

