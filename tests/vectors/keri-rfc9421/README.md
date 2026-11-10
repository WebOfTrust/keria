# KERI profile RFC 9421 vectors

These five JSON files are copied verbatim from fiki, `vectors/keri/`, at commit `c6ec3b5c921c16ba8f9d818356de8c12b0be2f8d` (fiki main, the merge of bakobo/fiki#4), `keri_vectors_format` 2, which targets [version 1 of the KERI profile](https://github.com/bakobo/fiki/blob/keri-profile-v1/docs/keri-profile.md). They differ from the earlier copy at fiki `34f37a0` only in header text (the profile citation, and the wording of `policy.body_rule` and `keys_rule`); every case is unchanged. fiki is an RFC 9421 implementation independent of keripy and KERIA and generates them itself (`vectors/keri/generate.py` there). keripy and signify-ts carry identical copies.

Do not edit them here. A case that disagrees with KERIA is resolved against the profile and, if the vector is wrong, fixed at the source and copied again.

- `requests.json`: signed requests a canonical verifier accepts, with the expected signature base.
- `responses.json`: signed responses, each with the request it answers.
- `refusals.json`: messages a canonical verifier refuses, each with its error code. The `request` cases are a server's; the `response` and `sign-request` cases are a client's.
- `legacy.json`: legacy-mode signatures pinned in KERIA's and signify-ts's existing tests.
- `rfc9421.json`: RFC 9421 Appendix B.2.6. KERIA does not run it; it is kept so the set stays whole.

Each key in the `keys` tables carries its `key_state` (current keys and signing threshold) and the `effective_key` that state reduces to under profile R4, or null when it has no single effective signer.

`tests/core/test_authing_canonical.py` runs `requests.json`, the request cases of `refusals.json`, `responses.json` and `legacy.json` through KERIA's `SignedHeaderAuthenticator`, serving each vector key from its `key_state`.
