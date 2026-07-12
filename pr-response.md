# PR Response Doc — CineLog Watchlist Feature

## AI Usage
<!-- Fill in at the end — how you used AI tools during this project -->

## Comment 1 — Rename
**What I changed:** Renamed `save_to_watchlist()` to `add_to_watchlist()` in `services/watchlist_service.py`. I also updated the corresponding import and invocation in `routes/watchlist/watchlist.py` so the route uses the new service API consistently.

**Why:** `add_to_watchlist()` describes the domain action more precisely. The function creates a new relationship between a user and a film; `save` is broader and could imply either persistence or an update to an existing entry.

**Design decisions:**

1. I chose `add_to_watchlist()` to match the existing `add_film` route handler and `/add` endpoint. Using the same verb across the route and service layers makes the request flow easier to follow and communicates that this is a create operation.
2. I made a direct rename instead of retaining `save_to_watchlist()` as a compatibility alias. The function is internal, had only one call site, and a temporary alias would leave two names for the same operation without providing a compatibility benefit.

**How I verified:** I used a project-wide search to confirm there are no remaining references to `save_to_watchlist()` and that the definition, import, and call all use `add_to_watchlist()`. I also ran the test suite; all four tests passed.

## Comment 2 — Deduplication
**What I did:**
**How I verified:**

## Comment 3 — Missing test
**What I did:**
**How I verified:**

## Comment 4 — Default visibility
**My position:**
**Reasoning:**
**Tradeoff acknowledged:**

## Comment 5 — Sort order
**My position:**
**Reasoning:**
**Engagement with reviewer's point:**

## Comment 6 — Rebase
**What conflicted:**
**How I resolved it:**
**How I verified no conflict remains:**

## PR Description
<!-- Written at the end — feature overview, design decisions, manual testing steps -->
