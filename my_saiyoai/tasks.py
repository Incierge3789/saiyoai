# tasks.py
from __future__ import absolute_import, unicode_literals
from celery import shared_task
from celery.utils.log import get_task_logger
logger = get_task_logger(__name__)

@shared_task
def add(x, y):
    try:
        # ここにタスクのロジックを書く
        return x + y
    except Exception as e:
        logger.error('Error occurred: %s', e)
        raise


@shared_task
def process_result(result):
    # ここで結果を処理します。例えば、結果をデータベースに保存するなど。
    pass

