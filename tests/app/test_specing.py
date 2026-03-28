from keria.app import agenting, aiding, delegating, notifying, indirecting, specing
from keria.end import ending

"""
OpenAPI Spec test validates:
- basic openapi document shape (version, paths, components, schemas)
- operation shape and HTTP method
- that referenced schemas from each operation actually exist in the document schemas

This is much more reliable than a big, copy-pasted string value in a gigantic test assertion.
"""


def _iter_refs(node):
    """Yield all $ref values from a nested OpenAPI document."""
    if isinstance(node, dict):
        for key, value in node.items():
            if key == "$ref" and isinstance(value, str):
                yield value
            else:
                yield from _iter_refs(value)
    elif isinstance(node, list):
        for value in node:
            yield from _iter_refs(value)


def _validate_openapi_semantics(spec):
    """Perform lightweight semantic validation without brittle full-string snapshots."""
    assert spec.get("openapi", "").startswith("3.")
    assert isinstance(spec.get("paths"), dict)
    assert isinstance(spec.get("components"), dict)
    assert isinstance(spec["components"].get("schemas"), dict)

    schemas = spec["components"]["schemas"]
    http_methods = {"get", "post", "put", "patch", "delete", "options", "head", "trace"}

    for route, operations in spec["paths"].items():
        assert route.startswith("/")
        assert isinstance(operations, dict)
        assert operations, f"Path {route} must include at least one operation"

        for method, operation in operations.items():
            assert method in http_methods or method.startswith("x-")
            if not isinstance(operation, dict) or not operation:
                # Some routes may intentionally define placeholder operations.
                continue
            assert "responses" in operation, (
                f"Missing responses for {method.upper()} {route}"
            )
            assert isinstance(operation["responses"], dict)

    # Ensure all local schema references resolve.
    for ref in set(_iter_refs(spec)):
        if ref.startswith("#/components/schemas/"):
            schema_name = ref.split("/")[-1]
            assert schema_name in schemas, f"Unresolved schema reference: {ref}"


def test_spec_resource(helpers):
    with helpers.openKeria() as (agency, agent, app, client):
        # Add all the endpoints similar to the agenting.setup function.
        agenting.loadEnds(app)
        aiding.loadEnds(app, agency, authn=None)
        delegating.loadEnds(app=app, identifierResource=aiding.IdentifierResourceEnd())
        ending.loadEnds(agency=agency, app=app)
        indirecting.loadEnds(agency=agency, app=app)
        notifying.loadEnds(app)

        specRes = specing.AgentSpecResource(
            app, title="KERIA Interactive Web Interface API"
        )
        sd = specRes.spec.to_dict()

        # Contract checks for critical API routes and basic document shape.
        paths = sd["paths"]
        assert "/" in paths
        assert "/agent/{caid}" in paths
        assert "/challenges" in paths
        assert "/challenges/{name}" in paths
        assert "/contacts/{prefix}" in paths
        assert "/contacts/{prefix}/img" in paths
        assert delegating.DELEGATION_ROUTE in paths
        assert "/events" in paths
        assert "/identifiers" in paths
        assert "/identifiers/{name}" in paths
        assert "/identifiers/{name}/endroles" in paths
        assert "/identifiers/{name}/locschemes" in paths
        assert "/identifiers/{name}/submit" in paths
        assert "/identifiers/{name}/oobis" in paths
        assert "/notifications" in paths
        assert "/notifications/{said}" in paths
        assert "/oobi" in paths
        assert "/oobi/{aid}" in paths
        assert "/oobi/{aid}/{role}" in paths
        assert "/oobi/{aid}/{role}/{eid}" in paths
        assert "/oobis" in paths
        assert "/oobis/{alias}" in paths
        assert "/operations" in paths
        assert "/operations/{name}" in paths
        assert "/queries" in paths
        assert "/states" in paths
        assert "/config" in paths

        _validate_openapi_semantics(sd)
