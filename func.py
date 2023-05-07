import random
from config import cfg


um_sub_cat = ""
if cfg.get("not_sub_cat"):
    um_sub_cat = f"""
    and sub_cat not in ('{"','".join(cfg.get("not_sub_cat"))}')
    """

um_cat = ""
if cfg.get("not_cat"):
    um_cat = f"""
    and cat not in ('{"','".join(cfg.get("not_cat"))}')
    """

um_not_my_expspense = f"""
{um_sub_cat}
{um_cat}
and `deleted`!=1
and suma>0
"""

cat4zam = """
if(sub_cat='Vdaliy Rik','Авто та АЗС',cat) as cat
"""


rand = random.random() * 10000000
