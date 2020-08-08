import random
from venv import logger

from django.http import HttpResponse, JsonResponse

# Create your views here.
from django.views import View
from django_redis import get_redis_connection

from meiduo.utils.response_code import RETCODE
from verifications.captcha.captcha import captcha
from meiduo.utils import constants
from celery_tasks.sms.tasks import ccp_send_sms_code


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
        # 校验参数
        if not all([image_code_client, uuid]):
            return JsonResponse({'code': RETCODE.IMAGECODEERR, 'errmsg': '图形验证码失效'})
        # 获取图片验证码
        redis_conn = get_redis_connection('verify_code')
        image_code_server = redis_conn.get('img_%s' % uuid)
        # 删除图片验证码
        try:
            redis_conn.delete('img_%s' % uuid)
        except Exception as e:
            logger.error(e)
        # 对比图片验证码
        if image_code_server is None:
            return JsonResponse({'code': RETCODE.IMAGECODEERR, 'errmsg': '图形验证码失效或已过期'})
        if image_code_client.lower() != image_code_server.decode().lower():
            return JsonResponse({'code': RETCODE.IMAGECODEERR, 'errmsg': '验证码错误'})

        # 后端60秒倒计时  避免频繁请求
        send_flag = redis_conn.get('send_flag_%s' % mobile)
        if send_flag:
            return JsonResponse({'code': RETCODE.THROTTLINGERR, 'errmsg': '发送短信过于频繁'})

        # 生成短信验证码
        sms_code = '%06d' % random.randint(0, 999999)
        logger.info(sms_code)
        print(sms_code)

        pl = redis_conn.pipeline()

        pl.setex('sms_%s' % mobile, 300, sms_code)
        # 重新写入send_flag
        pl.setex('send_flag_%s' % mobile, constants.SEND_SMS_CODE_INTERVAL, 1)
        # 执行请求
        pl.execute()

        # 发送短信验证码
        # CCP().send_template_sms(mobile, [sms_code, constants.SMS_CODE_REDIS_EXPIRES // 60],
        #                         constants.SEND_SMS_TEMPLATE_ID)
        ccp_send_sms_code.delay(mobile, sms_code)

        return JsonResponse({'code': RETCODE.OK, 'errmsg': '发送短信成功'})
