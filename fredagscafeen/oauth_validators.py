from oauth2_provider.oauth2_validators import OAuth2Validator


class CustomOAuth2Validator(OAuth2Validator):

    oidc_claim_scope = {
        **OAuth2Validator.oidc_claim_scope,
        "name": "profile",
        "preferred_username": "profile",
        "email": "email",
        "permissions": "groups",
    }

    def get_claim_dict(self, request, scopes=None):
        """
        The library calls this internally with just `request`.
        We make `scopes` optional and fall back to `request.scopes` safely.
        """
        user = request.user

        # Guard clause: If there's no logged-in user, return basic baseline
        if not user or user.is_anonymous:
            return {}

        # Fallback to request.scopes if scopes wasn't passed directly
        if scopes is None:
            scopes = getattr(request, "scopes", [])

        claims = {
            "sub": str(user.id),
        }

        if "profile" in scopes:
            claims["name"] = user.get_full_name().strip() or user.get_username()
            claims["preferred_username"] = user.get_username()

        if "email" in scopes:
            claims["email"] = user.email if user.email else ""

        if "groups" in scopes:
            # Safely cast the permissions set to a serializable sorted list
            claims["permissions"] = user.is_superuser and ["admin"] or []

        return claims

    def get_discovery_claims(self, request):
        return ["sub", "name", "preferred_username", "email", "permissions"]
