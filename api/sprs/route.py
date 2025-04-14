# _*_ coding:UTF-8 _*_

from fastapi import APIRouter

from api.sprs.services import (
    get_spr_dictionary,
)


router = APIRouter(prefix="/api/sprs", tags=["sprs"])


@router.get("/{dictionary}")
def get_dict(dictionary: str):
    """
    get dictionaries
    """
    return get_spr_dictionary(dictionary)
