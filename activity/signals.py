from __future__ import annotations

from typing import Optional

from django.contrib.auth import get_user_model
from django.contrib.auth.signals import (
    user_logged_in,
    user_logged_out,
    user_login_failed,
)
from django.dispatch import receiver

from .models import LoginEvent

UserModel = get_user_model()


def _get_ip(request) -> Optional[str]:
    if request is None:
        return None
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        # X-Forwarded-For: client, proxy1, proxy2
        return x_forwarded_for.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")


def _get_user_agent(request) -> str:
    if request is None:
        return ""
    return request.META.get("HTTP_USER_AGENT", "")


def _get_path(request) -> str:
    if request is None:
        return ""
    return request.get_full_path()


@receiver(user_logged_in)
def log_user_login(sender, request, user, **kwargs):
    LoginEvent.objects.create(
        user=user,
        username=user.get_username(),
        action=LoginEvent.Action.LOGIN,
        ip_address=_get_ip(request),
        user_agent=_get_user_agent(request),
        path=_get_path(request),
    )


@receiver(user_logged_out)
def log_user_logout(sender, request, user, **kwargs):
    LoginEvent.objects.create(
        user=user if isinstance(user, UserModel) else None,
        username=getattr(user, "get_username", lambda: "")(),
        action=LoginEvent.Action.LOGOUT,
        ip_address=_get_ip(request),
        user_agent=_get_user_agent(request),
        path=_get_path(request),
    )


@receiver(user_login_failed)
def log_user_login_failed(sender, credentials, request, **kwargs):
    username = credentials.get("username", "") if isinstance(credentials, dict) else ""
    LoginEvent.objects.create(
        user=None,
        username=username,
        action=LoginEvent.Action.FAILURE,
        ip_address=_get_ip(request),
        user_agent=_get_user_agent(request),
        path=_get_path(request),
    )
