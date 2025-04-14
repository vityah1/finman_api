import logging
from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi import Depends, HTTPException, Request
from app.jwt import create_access_token, get_current_user
from fastapi import status, Request
from sqlalchemy import and_
from utils import do_sql_cmd
from mydb import db
from models import User


logger = logging.getLogger()

router = APIRouter(prefix="/api/auth", tags=["auth"])

@router.post("/signin")
async def user_login(request: Request):
    data = await request.json()
    user = db.session().query(User).filter(
        and_(
            User.login == data.get('login'),
            User.password == data.get('password')
        )
    ).one_or_none()
    if not user:
        raise HTTPException(status_code=401, detail="Bad username or password")

    access_token = create_access_token({"sub": str(user.id)})
    result = user.to_dict()
    result['accessToken'] = access_token
    return result

@router.post("/signup")
async def create_user(request: Request):
    data = await request.json()
    user = User(**data)
    try:
        db.session().add(user)
        db.session().commit()
    except Exception as err:
        db.session().rollback()
        logger.error(f'create user failed {err}')        
        raise HTTPException(status_code=500, detail="create user failed")

    access_token = create_access_token({"sub": str(user.id)})
    result = user.to_dict()
    result["accessToken"] = access_token
    return result


@router.get("/users/{user_id}")
def get_user(user_id: int, _: str = Depends(get_current_user)):
    """
    get user
    """
    user = db.session().query(User).get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail='User not found')
    return user.to_dict()


@router.delete("/users/{user_id}")
def delete_user(user_id: int, _: str = Depends(get_current_user)):
    result = {}
    user = db.session().query(User).get(user_id)
    try:
        db.session().delete(user)
        db.session().commit()
    except Exception as err:
        db.session().rollback()
        logger.error(f'user delete failed {err}')
        raise HTTPException(status_code=500, detail="user delete failed")
    result["result"] = "ok"
    return result


@router.get("/users")
def get_users():
    """
    get users
    """
    users = db.session().query(User).all()
    if not users:
        abort(404, 'Not found users')

    return [item.to_dict() for item in users]


from fastapi import Request

@router.patch("/users/{user_id}")
async def edit_user(user_id: int, request: Request, _: str = Depends(get_current_user)):
    data = await request.json()
    data['user_id'] = user_id

    sql = """update `users` 
set login = :login, password = :password, fullname = :fullname, phone = :phone, email = :email 
where id = :user_id """

    res = do_sql_cmd(sql, data)
    return {"result": res}
    if res["rowcount"] < 1:
        return jsonify({"message": "error edit user"}), 401

    access_token = create_access_token(
        identity=data.get('username'), expires_delta=timedelta(days=30)
    )

    return {
        "user_id": data.get('user_id'),
        "accessToken": access_token,
        "username": data.get('username'),
        "fullname": data.get('fullname'),
        "phone": data.get('phone'),
        "email": data.get('email'),
    }
