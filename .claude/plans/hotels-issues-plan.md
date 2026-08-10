# Hotels Repo — Issue Resolution Plan

Created: 2026-08-10
Status: To-do (deferred)

---

## Issue #3: RuntimeError "No hotels found" (Bug Report)

**Opened:** 2025-10-22 | **Labels:** none | **Comments:** 0

### What happened
A user called `get_hotels()` with `fetch_mode="common"` and hit a `RuntimeError` in `parse_response()` at `core.py:223`. Google Hotels returned a page, but the HTML parser found zero hotel cards matching `div.uaTTDe`, and the fallback parser also produced no results. The response body contained language-selection content (EN, català, Deutsch, Español…), suggesting Google returned a locale/redirect page instead of actual hotel results.

### Root cause analysis
1. **Likely: Google Hotels changed their HTML structure or serving behavior** — the `div.uaTTDe` selector may be stale, or Google now serves a different page shape depending on region/headers.
2. **Possible: The user's location parameter was not a valid hotel-search city** — this could trigger a redirect or empty results page from Google.
3. **Possible: Rate limiting or bot detection** — Google may be blocking the request and serving a minimal/redirect page instead.

### What to do
1. [ ] **Reproduce the error** — use the same `hotel_data` and `guests` the user reported (need to ask the user for their exact input, or try common failing cases).
2. [ ] **Add better error messages** — when `parse_response` finds zero hotels, inspect the response text for known failure patterns (language selectors, CAPTCHAs, redirects) and raise descriptive errors like:
   - `"Google Hotels returned a locale selection page — location may be invalid"`
   - `"Google Hotels returned an empty result — possible rate limiting"`
3. [ ] **Add retry with backoff** — if the first fetch returns a suspicious page, retry once with a delay and/or different user-agent.
4. [ ] **Add a test for the error case** — mock a response with no hotel cards and verify a helpful error is raised.
5. [ ] **Add input validation** — validate that the `location` field is a real city or IATA code before sending the request.

### Files to touch
- `fast_hotels/core.py` — `parse_response()` and `fetch()`
- `fast_hotels/utils.py` — if adding location validation helpers
- `tests/test_fast_hotels.py` — new error-case tests

---

## Issue #4: Fix hotel price extraction for non-$ currencies and discounted rates (PR — needs review/merge)

**Opened:** 2026-07-08 | **Labels:** none | **PR #4**

### What's in this PR
The price extraction regex in `parse_response()` at line ~160 only matches `$`:
```python
price_matches = re.findall(r'\$([0-9,.]+)', card_text)
```
This breaks for:
- **Non-USD currencies** — e.g., `₹` (INR), `€`, `£` return zero matches, causing a silent fallback to the broken whole-page parser that misattributes star ratings as prices.
- **Discounted listings** — cards showing both crossed-out original price and current price; the code takes the first match (often the higher original).

The fix:
1. Expands the currency regex to match `₹`, `€`, `£`, `¥`, and other common symbols alongside `$`.
2. Takes the **minimum** of matched amounts per card instead of the first match, so discounted prices win.

### What to do
1. [ ] **Review the PR diff** — https://github.com/jongan69/hotels/pull/4 — check the regex changes and min() logic.
2. [ ] **Run tests** — `pytest tests/test_fast_hotels.py` (already passing per PR description, but re-verify).
3. [ ] **Manual verification with edge cases** — test with:
   - INR hotel search (Goa, Mumbai)
   - EUR hotel search (Paris, Berlin)
   - A search with many discounted listings (e.g., off-season dates)
   - A search with no discounts (to confirm min() behavior when only one price exists)
4. [ ] **Merge the PR** — squash and merge into `main`.
5. [ ] **Bump version & release** — update `pyproject.toml`, tag a new release, let the deploy workflow publish to PyPI.

### Files to touch
- `fast_hotels/core.py` — the price extraction block (~lines 155-165)
- `pyproject.toml` — version bump
- `tests/test_fast_hotels.py` — consider adding a price-specific unit test

---

## Priority & Order

| Priority | Issue | Why |
|----------|-------|-----|
| **1. Merge PR #4** | Price fix | Already written and tested — low effort, immediate value. Also makes the currency-agnostic parsing more robust, which helps #3's error path. |
| **2. Fix Issue #3** | RuntimeError | Needs investigation + code changes. The improved parsing from #4 helps, but the core problem (selectors/locale pages) needs its own fix. |
