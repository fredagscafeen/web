from oauth2_provider.oauth2_validators import OAuth2Validator


class CustomOAuth2Validator(OAuth2Validator):
    """Adds the OIDC claims oauth2-proxy needs: `email` (required for it to
    create a session at all) and `permissions` (read as its groups claim, used
    for per-service authorization)."""

    oidc_claim_scope = {**OAuth2Validator.oidc_claim_scope, "permissions": "groups"}

    def get_additional_claims(self, request):
        user = request.user
        return {
            "name": user.get_full_name(),
            "preferred_username": user.get_username(),
            "email": user.email,
            "permissions": sorted(user.get_all_permissions()),
        }

    def get_discovery_claims(self, request):
        # The base implementation can only enumerate claims when
        # get_additional_claims is request-agnostic, so list ours explicitly.
        return ["sub", "name", "preferred_username", "email", "permissions"]
