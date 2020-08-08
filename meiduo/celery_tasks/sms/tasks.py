from venv import logger

from celery_tasks.main import celery_app


# bind：保证task对象会作为第一个参数自动传入
# name：异步任务别名
# retry_backoff：异常自动重试的时间间隔 第n次(retry_backoff×2^(n-1))s
# max_retries：异常自动重试次数的上限
from celery_tasks.sms import constants
from celery_tasks.sms.yuntongxun.ccp_sms import CCP


@celery_app.task(bind=True, name='ccp_send_sms_code', retry_backoff=3)
def ccp_send_sms_code(self, mobile, sms_code):
    """
    发送短信的异步任务
    :param self:
    :param mobile: 手机号
    :param sms_code: 短信验证码
    :return: 成功0 失败-1
    """

    try:
        send_ret = CCP().send_template_sms(mobile, [sms_code, constants.SMS_CODE_REDIS_EXPIRES // 60],
                                           constants.SEND_SMS_TEMPLATE_ID)
        print(1)
    except Exception as e:
        logger.error(e)
        # 有异常自动重试3次
        raise self.retry(exc=e, max_retries=3)

    if send_ret != 0:
        # 有异常自动重试三次
        raise self.retry(exc=Exception('发送短信失败'), max_retries=3)

    return send_ret
