import logging
from sqlalchemy import and_
from fastapi import HTTPException, status

from models.models import Group, UserGroupAssociation
from fastapi_sqlalchemy import db

logger = logging.getLogger()

def check_user_in_group(target_user_id: int, admin_user_id: int) -> bool:
    """
    Перевіряє, чи є admin_user_id адміністратором у групі, в якій знаходиться target_user_id.
    
    Args:
        target_user_id: ID користувача, для платежу якого потрібна перевірка
        admin_user_id: ID користувача, який намагається змінити платіж
        
    Returns:
        bool: True, якщо admin_user_id є адміністратором групи, в якій є target_user_id
    """
    # Знаходимо групи, в яких знаходиться цільовий користувач
    target_user_groups = db.session.query(UserGroupAssociation).filter(
        UserGroupAssociation.user_id == target_user_id
    ).all()
    
    if not target_user_groups:
        logger.info(f"Користувач {target_user_id} не належить до жодної групи")
        return False
    
    # Для кожної групи перевіряємо, чи є admin_user_id адміністратором
    for association in target_user_groups:
        # Перевіряємо, чи є admin_user_id у цій групі та чи є він адміном
        admin_association = db.session.query(UserGroupAssociation).filter(
            and_(
                UserGroupAssociation.group_id == association.group_id,
                UserGroupAssociation.user_id == admin_user_id,
                UserGroupAssociation.is_admin == True
            )
        ).first()
        
        if admin_association:
            logger.info(f"Користувач {admin_user_id} є адміністратором групи {association.group_id}")
            return True
    
    logger.info(f"Користувач {admin_user_id} не є адміністратором жодної групи користувача {target_user_id}")
    return False
