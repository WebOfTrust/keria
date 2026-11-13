# KERI profile RFC 9421 vectors

These five JSON files are copied verbatim from fiki, `vectors/keri/`, at commit `63821f7ac4fd6e4062b3932e77e325a7227b4f6d` (fiki main, the merge of bakobo/fiki#32, tagged `keri-profile-v1.2`), `keri_vectors_format` 8, which targets [version 1.2 of the KERI profile](https://github.com/bakobo/fiki/blob/keri-profile-v1.2/docs/keri-profile.md). fiki is an RFC 9421 implementation independent of keripy and KERIA and generates them itself (`vectors/keri/generate.py` there). keripy and signify-ts carry identical copies.

Do not edit them here. A case that disagrees with KERIA is resolved against the profile and, if the vector is wrong, fixed at the source and copied again.

- `requests.json`: signed requests a canonical verifier accepts, with the expected signature base.
- `responses.json`: signed responses, each with the request it answers.
- `refusals.json`: messages a canonical verifier refuses, each with its error code. The `request` cases are a server's; the `response` and `sign-request` cases are a client's.
- `legacy.json`: legacy-mode signatures pinned in KERIA's and signify-ts's existing tests, and legacy requests fiki generated from controllers with more than one current key. Each generated case carries `key_state`, the key state KERIA holds for its `Signify-Resource` (null when it serves no agent for it), its `sufficient_keys`, every current key that alone satisfies the signing threshold (profile section 8), and its refusal `error` when it has one.
- `rfc9421.json`: RFC 9421 Appendix B.2.6. KERIA does not run it; it is kept so the set stays whole.

Each transferable key in the `keys` tables carries its `key_state` (current keys and signing threshold) and the `effective_key` that state reduces to under profile R4, or null when it has no single effective signer. A `B` keyid's key is its prefix, so KERIA verifies it without key state. Two request cases, a `Signature` and a `Content-Digest` without `=` padding, are marked `verified_by_fiki` false; KERIA verifies them like the rest.

`tests/core/test_authing_canonical.py` runs `requests.json`, the request cases of `refusals.json`, `responses.json` and `legacy.json` through KERIA's `SignedHeaderAuthenticator`, serving each vector key from its `key_state`. The generated legacy cases go through the same authenticator's legacy path against their `key_state` (`test_vector_legacy_sufficient_keys`).
