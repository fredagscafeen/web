from oauth2_provider.oauth2_validators import OAuth2Validator


class CustomOAuth2Validator(OAuth2Validator):
    """Adds the OIDC claims oauth2-proxy needs: `email` (required for it to
    create a session at all) and `groups` (read as its groups claim, used
    for per-service authorization)."""

    oidc_claim_scope = {
        **OAuth2Validator.oidc_claim_scope,
        "name": "profile",
        "preferred_username": "profile",
        "email": "email",
        "groups": "groups",  # maps the 'groups' claim to 'groups' scope
    }

    def get_claim_dict(self, request, scopes):
        """
        This is where DOT extracts claims for the ID Token and UserInfo endpoint.
        It evaluates the granted scopes and yields the correct dictionary payload.
        """
        user = request.user
        claims = {
            "sub": str(user.id),
        }

        # Dynamically inject claims if their mapped scopes were requested and granted
        if "profile" in scopes:
            claims["name"] = user.get_full_name() or user.get_username()
            claims["preferred_username"] = user.get_username()

        if "email" in scopes:
            claims["email"] = user.email

        if "groups" in scopes:
            claims["groups"] = sorted(list(user.get_all_permissions()))

        return claims

    def get_discovery_claims(self, request):
        return ["sub", "name", "preferred_username", "email", "groups"]
