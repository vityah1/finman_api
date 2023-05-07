from os import environ
import dotenv

dotenv.load_dotenv()


cfg = {
    "dict_phones": {
        "+380638457475": "Vik Life",
        "0500326725": "Vik Vodafone",
        "+380638508875": "Tanya Life",
        "0507558679": "Tanya Vodafone",
        "+380637054293": "Yarema Life",
        "+380633859083": "Yana Life",
        "+380634649973": "Ulya Life",
        "0684276934": "Ulya KS",
        "+380935420056": "Tato Life",
        "+380634650087": "Mama Life new",
        "+3809300281494": "Ulya Life 2",
        "0993954299": "Tato Vodafone",
        "+380639920388": "домашня Nokia"
    },
    "not_sub_cat": [
        "AliExpress",
        "PAYPAL",
        "PSP*mall.my.com",
        "PAYPAL *GEEKBUYING",
        "LIQPAY*Hosting Ukrayin",
        "Pandao",
        "Укрпошта",
        "Нова пошта",
        "portmone.com.ua",
        "monobank",
        "DHGATE",
        "DHGATE.COM",
        "wondershare"
    ],
    "not_cat": [],
    "not_cat_": [
        "Грошові перекази"
    ]
}

cfg["SECRET_KEY"] = environ["SECRET_KEY"]
cfg["DATABASE_URI"] = environ["DATABASE_URI"]