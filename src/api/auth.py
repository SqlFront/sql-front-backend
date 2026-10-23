from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from src.api.dependencies import get_user_repository
from src.models.user import User
from src.repositories.user import UserRepository
from src.schemas.token import Token
from src.schemas.user import PasswordResetRequest, UserCreate, UserLogin, UserPublic
from src.utils.analytics import log_user_event
from src.utils.auth import create_access_token, get_current_user

router = APIRouter(prefix="/api/auth", tags=["Auth"])


@router.post("/register", response_model=UserPublic)
async def register(
    user_data: UserCreate,
    user_repo: UserRepository = Depends(get_user_repository),
):
    if await user_repo.get_user_by_login(user_data.login):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Пользователь с таким логином уже существует",
        )

    try:
        user = await user_repo.create_user(
            user_data={
                "login": user_data.login,
                "email": user_data.email,
                "fullname": user_data.fullname,
                "group": user_data.group,
            },
            password=user_data.password,
        )
        return user
    except KeyError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Отсутствует обязательное поле: {e.args[0]}",
        )
    except AttributeError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Переданы некорректные данные пользователя",
        )
    except TypeError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Некорректный тип данных: {str(e)}",
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Ошибка валидации: {str(e)}",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Внутренняя ошибка сервера",
        )


@router.post("/login", response_model=Token)
async def login(
    user_data: UserLogin,
    user_repo: UserRepository = Depends(get_user_repository),
):
    user = await user_repo.get_user_by_login(user_data.login)
    if not user or not await user_repo.verify_password(
        user_data.login, user_data.password
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Некорректный логин или пароль",
        )
    access_token = create_access_token(
        data={"sub": user.login},
        expires_delta=timedelta(hours=24),
    )
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/reset-password")
async def reset_password(
    data: PasswordResetRequest,
    user_repo: UserRepository = Depends(get_user_repository),
    db: AsyncSession = Depends(get_db),
):
    user = await user_repo.reset_password(
        login=data.login,
        email=data.email,
        new_password=data.new_password,
    )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Пользователь с указанным логином и почтой не найден",
        )

    try:
        await log_user_event(
            session=db,
            user_id=user.user_id,
            event_type="password_reset",
        )
    except Exception:
        pass

    return {"message": "Пароль успешно обновлен"}


@router.post("/logout")
async def logout(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        await log_user_event(
            session=db,
            user_id=current_user.user_id,
            event_type="user_inactive",
        )
    except Exception:
        pass
    return {"message": "Successfully logged out"}
