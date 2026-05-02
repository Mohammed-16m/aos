from rest_framework_simplejwt.tokens import RefreshToken

class CustomRefreshToken(RefreshToken):
    @classmethod
    def for_user(cls, user):
        token = super().for_user(user)
        token['role']    = user.role
        token['user_id'] = user.id
        token['email']   = user.email
        return token