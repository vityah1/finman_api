# _*_ coding:UTF-8 _*_
import logging
import io

from flask import request, abort

from api.revolut.funcs import convert_file_to_pmts, add_payments


logger = logging.getLogger()


def revolut_import_(user_id: int):
    """
    iport data from revolut
    """
    result = None
    if 'file' not in request.files:
        abort('No file part in the request')

    file = request.files['file']

    if file.filename == '':
        abort('No selected file')

    # file.save(f'uploads/{user_id}/revolut/' + file.filename)
    # for test by ThunderClient
    # file_ = request.data
    # file = io.BytesIO(file_)

    try:
        data_ = convert_file_to_pmts(user_id, file)
        if not data_:
            logger.error(f'Not valid data')
            raise Exception("Not valid data")
        if request.form.get('action') == 'import':
            result = add_payments(data_)
        else:
            return data_

        if not result:
            raise Exception('data convert failed')

        result = "ok"
    except Exception as err:
        logger.error(f'{err}')
        result = "failed"
    return {"status": result}
