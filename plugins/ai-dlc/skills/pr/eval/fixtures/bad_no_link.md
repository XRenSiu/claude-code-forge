## Summary

Adds relative-time search with era disambiguation.

## Scope

- do: relative time parsing; disambiguation prompt; era card
- dont: absolute date picker; timeline

## Linked issue

see the issue

## Changes

- `src/search/api/time.ts` — parser + route
- `src/search/ui/EraCard.tsx` — card

## Verification

```bash
npm test   # 128 passed
```

- Red-green: tests/search/time.test.ts failed on abc123, passes here

## Acceptance mapping

| AC | kind | evidence |
|---|---|---|
| AC-001-a | mechanical | tests/search/time.test.ts::disambiguates ✅ |
| AC-001-b | mechanical | tests/search/time.test.ts::rejects_empty ✅ |
| AC-003-a | mechanical | tests/search/time.test.ts::rejects_empty ✅ |
| AC-002-a | human | judge: product · demo (G3) |

## Risk & rollback

- risk: low
- blast radius: search module
- rollback: revert
- feature flag: none

## Reviewer focus

- src/search/api/time.ts:40 — overlap threshold
