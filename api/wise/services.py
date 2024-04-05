# _*_ coding:UTF-8 _*_
import logging
# import io

from flask import request, abort

from api.wise.funcs import convert_file_to_pmts, add_wise_bulk_payments
from api.mono.funcs import add_new_payment


logger = logging.getLogger()


def wise_import_(user_id: int):
    """
    iport data from wise
    """

    if 'file' not in request.files:
        abort('No file part in the request')

    file = request.files['file']

    if file.filename == '':
        abort('No selected file')

    # file.save(f'uploads/{user_id}/wise/' + file.filename)
    # for test by ThunderClient
    # file_ = request.data
    # file = io.BytesIO(file_)

    try:
        data_ = convert_file_to_pmts(user_id, file)
        if not data_:
            logger.error(f'Not valid data')
            raise Exception("Not valid data")
        if request.form['action'] == 'show':
            return data_
        if request.form['action'] == 'import':
            result = add_wise_bulk_payments(data_)
            if result:
                for pmt_row in data_:
                    pmt_row['sql'] = True
            else:
                for pmt_row in data_:
                    result = add_new_payment(pmt_row)
                    if result:
                        pmt_row['sql'] = True
                    else:
                        pmt_row['sql'] = False
        return data_
    except Exception as err:
        logger.error(f'{err}')
        return {"status": "failed"}
