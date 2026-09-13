# Build107 local catalog numerical extraction

Local implementation only, uncommitted and undeployed. The accepted SonicTrace release identity remains unchanged.

`js/catalog-projection-kernel.mjs` is the sole editable numerical source. It exports only `normalize`, `dot`, and `powerComponent`. Their operation order, seed, 42 iterations, orthogonal subtraction, stopping condition and zero behavior are unchanged. Catalog projection policy, normalization of map coordinates, fallbacks, scoring, clustering and semantics remain in `catalog-similarity.js`.

The consumer now imports the local module. The catalog loader marks only the similarity script as a module and advances to UI after its load event, which follows dependency evaluation. The similarity-ready event and public namespace remain unchanged. No remote import or Studio dependency exists.

## Distribution

From this repository:

```text
node scripts/vendor-build107-kernel.mjs ../shinobiwan-studio
node scripts/test-build107-kernel.mjs
node scripts/test-build107-loader.mjs
```

The generator copies canonical bytes and generates declarations and provenance. Never edit the Studio vendor file. LF is enforced for the kernel by `.gitattributes` so checkout conversion cannot invalidate its byte digest.

SHA-256: `f883aa12011d0714049717c6de6a426fbc7c8296a5aa872a978aaeefc47f34d8`.

No new commit was authorized. Therefore the provenance commit is the real pre-extraction commit `7dfe8d341ef1a0573ddda4eb66801d01986780dd`, whose `js/catalog-similarity.js` contains the original functions. `sourceCommitPath` records that committed path; `sourcePath` records the new canonical module; `sourceState` explicitly says `uncommitted-extraction-from-pinned-source`. This does not claim the new path exists at the old commit. `build107-source.mjs` reconstructs the exact extraction from that commit, and tests compare it byte-for-byte to the canonical module and the frozen distribution digest. The workflow fetches history for that verification. A future committed-source pin requires a separately authorized update; this task creates no commits.

## Baseline and validation

Before removing any original function, `node scripts/capture-build107-baseline.mjs` compared both existing implementations exactly and captured 26 numerical cases, 9 SonicTrace whole catalogs and 8 Studio whole catalogs. The capture script is deliberately pre-extraction-only and fails if rerun against extracted consumers; fixtures must not be regenerated to conceal a regression. Fixtures contain outputs, not another solver. Numerical cases include empty/zero vectors and matrices, identical/collinear/rank-deficient matrices, ordinary and 512D deterministic inputs, PC1/orthogonal PC2, unequal dot lengths, extreme magnitudes, repeatability and no mutation.

Phase5 workflow contract Python tests, JavaScript regressions, syntax checks and new numerical/loader tests passed locally. The real Discogs-EffNet smoke failed before model execution because `librosa` is unavailable. No model download or production inference was performed. Full command/results receipt is in Studio `docs/BUILD107-LOCAL-IMPLEMENTATION.md`.

## Rollback

For this initially clean, uncommitted checkout, restore only `.github/workflows/validate-phase5.yml`, `js/catalog-similarity.js` and `js/loader.js` from HEAD, then remove the new Build107 files listed in the companion receipt. Restore the loader and consumer together. This reestablishes the original standalone solver without touching Studio, persisted data, Workers or R2. Review any subsequent local edits before restoration. No rollback was executed.
