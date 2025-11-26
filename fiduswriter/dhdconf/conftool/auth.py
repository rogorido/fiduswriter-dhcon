from django.contrib.auth.backends import BaseBackend
from django.conf import settings

from dhdconf.conftool.api import (
    ConftoolClient,
    ConftoolLoginFailed,
    ConftoolAccessDenied,
    ConftoolNonceTooSmall,
    ConftoolUnknownUser,
    ConftoolIllegalUsername,
    ConftoolIllegalPassword
)
from dhdconf.conftool.importing import import_user_info
from dhdconf.models import ConftoolUser, ImportLog
from dhdconf.conftool.util import import_log_error


class ConftoolBackend(BaseBackend):

    def __init__(self):
        self.client = ConftoolClient(
            service_url=settings.CONFTOOL_URL,
            secret=settings.CONFTOOL_APIPASS,
        )
        super().__init__()

    def authenticate(self, request, username=None, password=None, retry=0, **kwargs):
        try:
            response = self.client.login(username, password)
        except ConftoolNonceTooSmall as e:
            if retry < 2:
                return self.authenticate(request, username, password, retry=retry + 1, **kwargs)
            else:
                import_log_error(ImportLog.ErrorType.FETCH_LOGIN, e, request)
                return None
        except (
            ConftoolLoginFailed,
            ConftoolAccessDenied,
            ConftoolUnknownUser,
            ConftoolIllegalUsername,
            ConftoolIllegalPassword
        ):
            return None
        except Exception as e:
            import_log_error(ImportLog.ErrorType.FETCH_LOGIN, e, request)
            return None

        if response.result:
            user = ConftoolUser.objects.filter(conftool_id=response.id).first()
            if not user:
                user = ConftoolUser(conftool_id=response.id)
                user.set_unusable_password()
                try:
                    info = self.client.user_info(response.username)
                    try:
                        import_user_info(user, info)
                    except Exception as e:
                        import_log_error(ImportLog.ErrorType.IMPORT_USERINFO, e, request)
                        return None
                except Exception as e:
                    import_log_error(ImportLog.ErrorType.FETCH_USERINFO, e, request)
                    return None
            return user.user_ptr
        else:
            return None

    def get_user(self, user_id):
        user = ConftoolUser.objects.filter(id=user_id).first()
        return user.user_ptr if user else None
