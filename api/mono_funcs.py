# _*_ coding:UTF-8 _*_
import time
import datetime


"""
url for webhook:
https://script.google.com/macros/s/AKfycbxq8R2y9ugmDmfYDAp9rf5MEUs_5lf2SNT_Cc0u_R3KYTfYMPvc/exec

https://api.monobank.ua/
POST /personal/webhook
{
  "webHookUrl": "string"
}
"""


def _mcc(mcc):
    if (
        mcc
        in (
            4011,
            4111,
            4112,
            4131,
            4304,
            4411,
            4415,
            4418,
            4457,
            4468,
            4511,
            4582,
            4722,
            4784,
            4789,
            5962,
            6513,
            7011,
            7032,
            7033,
            7512,
            7513,
            7519,
        )
        or mcc in range(3000, 4000)
    ):
        return "Подорожі"
    elif (
        mcc
        in (
            4119,
            5047,
            5122,
            5292,
            5295,
            5912,
            5975,
            5976,
            5977,
            7230,
            7297,
            7298,
            8011,
            8021,
            8031,
            8049,
            8050,
            8062,
            8071,
            8099,
        )
        or mcc in range(8041, 8044)
    ):
        return "Краса та медицина"
    elif (
        mcc
        in (
            5733,
            5735,
            5941,
            7221,
            7333,
            7395,
            7929,
            7932,
            7933,
            7941,
            7991,
            7995,
            8664,
        )
        or mcc in range(5970, 5974)
        or mcc in range(5945, 5948)
        or mcc in range(5815, 5819)
        or mcc in range(7911, 7923)
        or mcc in range(7991, 7995)
        or mcc in range(7996, 8000)
    ):
        return "Розваги та спорт"
    elif mcc in range(5811, 5815):
        return "Кафе та ресторани"
    elif mcc in (
        5297,
        5298,
        5300,
        5311,
        5331,
        5399,
        5411,
        5412,
        5422,
        5441,
        5451,
        5462,
        5499,
        5715,
        5921,
    ):
        return "Продукти й супермаркети"
    elif mcc in (7829, 7832, 7841):
        return "Кіно"
    elif (
        mcc
        in (
            5172,
            5511,
            5541,
            5542,
            5983,
            7511,
            7523,
            7531,
            7534,
            7535,
            7538,
            7542,
            7549,
        )
        or mcc in range(5531, 5534)
    ):
        return "Авто та АЗС"
    elif mcc in (
        5131,
        5137,
        5139,
        5611,
        5621,
        5631,
        5641,
        5651,
        5655,
        5661,
        5681,
        5691,
        5697,
        5698,
        5699,
        5931,
        5948,
        5949,
        7251,
        7296,
    ):
        return "Одяг і взуття"
    elif mcc == 4121:
        return "Таксі"
    elif mcc in (742, 5995):
        return "Тварини"
    elif mcc in (2741, 5111, 5192, 5942, 5994):
        return "Книги"
    elif mcc in (5992, 5193):
        return "Квіти"
    elif mcc in (4814, 4812):
        return "Поповнення мобільного"
    elif mcc == 4829:
        return "Грошові перекази"
    elif mcc == 4900:
        return "Комунальні послуги"
    else:
        return "Інше"


def dt(dt):
    # функція повертає юнікс формат часу (як хоче моно) з нормального YYYYMMDD
    #    yy=dt[6:10]
    #    mm=dt[3:5]
    #    dd=dt[0:2]

    yy = dt[0:4]
    mm = dt[5:7]
    dd = dt[8:10]

    if len(dt) > 10:
        hh = dt[11:13]
        mi = dt[14:16]
        ss = dt[17:19]
        #        print(f'''Date with Time: {dt} => [{dd}.{mm}.{yy}, {hh} {mi} {ss}]<br>''')
        d = datetime.datetime(int(yy), int(mm), int(dd), int(hh), int(mi), int(ss))
    else:
        #        print(f'''Only Date: {dt} => [{dd}.{mm}.{yy}]<br>''')
        d = datetime.date(int(yy), int(mm), int(dd))

    return int(time.mktime(d.timetuple()))
