# KERI profile RFC 9421 vectors

These five JSON files are copied verbatim from fiki, `vectors/keri/`, at commit `530cd8c269675bb8fc311d8896034cfd2a46fafc`, `keri_vectors_format` 1. fiki is an RFC 9421 implementation independent of keripy and KERIA and generates them itself (`vectors/keri/generate.py` there). keripy and signify-ts carry identical copies.

Do not edit them here. A case that disagrees with KERIA is resolved against the profile and, if the vector is wrong, fixed at the source and copied again.

- `requests.json`: signed requests a canonical verifier accepts, with the expected signature base.
- `responses.json`: signed responses, each with the request it answers.
- `refusals.json`: messages a canonical verifier refuses, each with its error code.
- `legacy.json`: legacy-mode signatures pinned in KERIA's and signify-ts's existing tests.
- `rfc9421.json`: RFC 9421 Appendix B.2.6. KERIA does not run it; it is kept so the set stays whole.

`tests/core/test_authing_canonical.py` runs `requests.json`, `refusals.json` (the request cases), `responses.json` and `legacy.json` through KERIA's `SignedHeaderAuthenticator`.
