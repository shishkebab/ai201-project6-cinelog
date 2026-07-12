# PR Response Doc — CineLog Watchlist Feature

## AI Usage
I used Codex and Claude to orient myself in the codebase and compare the watchlist implementation with established project patterns. In particular, I asked it to locate every reference to `save_to_watchlist()`, examine how `add_to_collection()` handles duplicate entries, and compare the missing-film test with the equivalent collection test. I reviewed the proposed changes and verified them independently with project-wide searches, focused pytest runs, the complete test suite, and `git diff --check`. I also used AI to inspect the rebase history and reflog, diagnose the UUID integration issue that Git did not report as a textual conflict, and audit the commit subjects against Conventional Commits.

For Comments 4 and 5, I asked Claude to stress-test both sides of the design choices rather than simply defend the existing implementation. For visibility, the AI identified the tension between social discovery and privacy; my final position keeps `public=True` only with the additional requirement that the default be clearly disclosed and that users have an accessible private option. For ordering, the AI compared alphabetical scanning with recent-intent behavior; my final argument adopts newest-first because a watchlist functions primarily as a personal queue, while reserving alphabetical order for a future explicit sort or search option. The final positions and tradeoffs are my decisions, refined using that analysis.

## Comment 1 — Rename
**What I changed:** Renamed `save_to_watchlist()` to `add_to_watchlist()` in `services/watchlist_service.py`. I also updated the corresponding import and invocation in `routes/watchlist/watchlist.py` so the route uses the new service API consistently.

**Design decisions:**

1. I chose `add_to_watchlist()` to match the existing `add_film` route handler and `/add` endpoint. Using the same verb across the route and service layers makes the request flow easier to follow and communicates that this is a create operation.
2. I made a direct rename instead of retaining `save_to_watchlist()` as a compatibility alias. The function is internal, had only one call site, and a temporary alias would leave two names for the same operation without providing a compatibility benefit.

**How I verified:** I used a project-wide search to confirm there are no remaining references to `save_to_watchlist()` and that the definition, import, and call all use `add_to_watchlist()`. I also ran the test suite; all four tests passed.

## Comment 2 — Deduplication
**What I did:** Added an `AlreadyInWatchlistError` and updated `add_to_watchlist()` to query for an existing entry with the same `user_id` and `film_id` before creating one. If a match exists, the function raises the new error instead of inserting a duplicate. This follows the same validation pattern used by `add_to_collection()`.

**How I verified:** Added a film to a user's watchlist, attempted to add the same film for the same user again, and confirmed that `AlreadyInWatchlistError` was raised and only one matching `WatchlistEntry` remained in the database. I also ran the full test suite to check for regressions.

## Comment 3 — Missing test
**What I did:** Created `tests/test_watchlist.py` and added `test_add_to_watchlist_nonexistent_film_raises`. The test uses the same isolated in-memory database and user fixture pattern as `tests/test_collection.py`, calls `add_to_watchlist()` with the nonexistent UUID `00000000-0000-0000-0000-000000000000`, and asserts that the service raises `FilmNotFoundError` rather than allowing a database integrity error.

**How I verified:** Ran `pytest tests/test_watchlist.py -v`; all three watchlist tests passed. This confirmed that UUID-backed entries can be created, an unknown UUID is rejected before insertion, and retrieved watchlists are ordered newest first.

## Comment 4 — Default visibility
**My position:** I support keeping `public=True` as the default, provided that visibility is communicated clearly and users have an easy way to make watchlist entries private. This should be an intentional product default, not merely an inherited model value.

**Reasoning:** I am optimizing for users who treat CineLog as a social discovery tool: they save films they want to watch, share those interests, and help other users discover films through visible watchlists. Defaulting entries to public makes that behavior immediate and avoids requiring an extra visibility decision every time a film is added. It also ensures that the sharing value of the feature works for users who accept the product's social model but would not actively configure each entry.

**Tradeoff acknowledged:** A `public=False` default would better protect users who consider their viewing interests personal and would reduce the risk of accidental disclosure. That is a meaningful privacy advantage, and a public default creates a responsibility to make visibility obvious and private controls accessible. I am choosing public-by-default here because I prioritize low-friction sharing and discovery for this feature, but if CineLog cannot clearly communicate the default or offer a straightforward opt-out, private-by-default would be the safer choice.

## Comment 5 — Sort order
**My position:** I agree that the default should be date added, newest first. I changed `get_watchlist()` to order by `WatchlistEntry.date_added.desc()` instead of `Film.title.asc()`.

**Reasoning:** A watchlist behaves more like a personal queue than a catalog. Recent additions reflect the user's current interests and are the items they are most likely to look for when returning to the list. Newest-first ordering also gives immediate feedback after an add operation because the newly saved film appears at the top. Alphabetical order is useful for locating a known title in a long list, but that need would be better served by search or an explicit sort control rather than determining the default for every user.

**Engagement with reviewer's point:** The reviewer's observation that users generally want to see what they added recently matches the primary behavior I want to optimize for: resuming the intent that brought a user back to their watchlist. I therefore adopted the suggested ordering rather than retaining alphabetical order. This also aligns watchlist behavior with the collection service's existing newest-first convention, making ordering more predictable across CineLog.

## Comment 6 — Rebase
**What conflicted:** Git reported an add/add conflict in `.gitignore` because both branches introduced the file, with `main` also ignoring `.pytest_cache/`. The UUID migration created a separate semantic conflict that Git did not flag: `main` removed the integer-based `WatchlistEntry`, while the replayed feature commits still imported it and documented integer film IDs.

**How I resolved it:** Removed the committed conflict markers from `.gitignore` and retained the complete set of Python, database, test-cache, and virtual-environment exclusions. Restored `WatchlistEntry` with a UUID `film_id`, added the user and film relationships required by the service, changed the service and route documentation to UUIDs, and updated the missing-film test to use a nonexistent UUID.

**How I verified no conflict remains:** Searched the project for Git conflict markers and remaining watchlist integer-ID references; no unresolved markers or active integer assumptions remain. `pytest tests/test_watchlist.py -v` passed all three focused tests, and the complete suite passed all seven tests. The focused tests exercise UUID persistence, nonexistent UUID handling, the `entry.film` relationship, and newest-first ordering.

**Git log image:** [Git log image](./git_log.png)

## PR Description
### Summary

This PR adds a watchlist for films a user wants to watch later. A client can add a film by UUID with `POST /watchlist/<user_id>/add` and retrieve the user's watchlist with `GET /watchlist/<user_id>`. Each returned film includes its watchlist `date_added` and `public` metadata. The service rejects unknown film UUIDs and prevents the same user from adding the same film more than once.

The implementation is compatible with `main`'s UUID-based film model and includes focused service tests for successful UUID persistence, missing films, model relationships, and result ordering.

### Design decisions

1. **Visibility defaults to public.** New `WatchlistEntry` records use `public=True`. I chose this default to optimize for CineLog's social discovery use case: users can share what they plan to watch without configuring every entry individually. The tradeoff is that private-by-default would offer stronger protection for users who consider viewing interests personal, so visibility must be communicated clearly and an accessible private option should be added as the product evolves.
2. **Watchlists default to newest-first order.** `get_watchlist()` sorts by `date_added` descending. This treats the watchlist as a personal queue and puts the user's most recent interests at the top, while also making a newly added film immediately visible. Alphabetical ordering can still be offered later as an explicit sort option or through search.

### Manual testing

1. Install the dependencies:

   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

2. Seed one user and two films from the Flask shell:

   ```bash
   flask --app app shell
   ```

   Then run:

   ```python
   from app import db
   from models import Film, User

   user = User(username="watchlist-manual", email="watchlist-manual@example.com")
   older_film = Film(title="Manual Older Film", year=2024)
   newer_film = Film(title="Manual Newer Film", year=2025)
   db.session.add_all([user, older_film, newer_film])
   db.session.commit()

   print("USER_ID=", user.id)
   print("OLDER_FILM_ID=", older_film.id)
   print("NEWER_FILM_ID=", newer_film.id)
   exit()
   ```

3. Start the API in one terminal:

   ```bash
   source .venv/bin/activate
   python app.py
   ```

4. In another terminal, replace the placeholders with the UUIDs printed during seeding:

   ```bash
   USER_ID="<user-uuid>"
   OLDER_FILM_ID="<older-film-uuid>"
   NEWER_FILM_ID="<newer-film-uuid>"
   ```

5. Add the first film and confirm the response is `201 Created` with `"public": true`:

   ```bash
   curl -i -X POST "http://localhost:5000/watchlist/$USER_ID/add" \
     -H "Content-Type: application/json" \
     -d "{\"film_id\": \"$OLDER_FILM_ID\"}"
   ```

6. Wait one second, then add the second film:

   ```bash
   sleep 1
   curl -i -X POST "http://localhost:5000/watchlist/$USER_ID/add" \
     -H "Content-Type: application/json" \
     -d "{\"film_id\": \"$NEWER_FILM_ID\"}"
   ```

7. Retrieve the watchlist:

   ```bash
   curl -s "http://localhost:5000/watchlist/$USER_ID" | python -m json.tool
   ```

   Confirm that both entries include `date_added` and `public`, that `public` is `true`, and that **Manual Newer Film** appears before **Manual Older Film**.

8. Confirm request validation by omitting `film_id`:

   ```bash
   curl -i -X POST "http://localhost:5000/watchlist/$USER_ID/add" \
     -H "Content-Type: application/json" \
     -d '{}'
   ```

   Confirm the API returns `400 Bad Request` with `{"error":"film_id is required"}`.

9. Run the automated checks:

   ```bash
   pytest tests/test_watchlist.py -v
   pytest -q
   ```

   The focused watchlist suite should report three passing tests, and the complete suite should report seven passing tests.

### Rebase and conflict resolution

I rebased `feature/watchlist` onto `origin/main` to incorporate the UUID migration. I removed accidentally committed `.gitignore` conflict markers and retained the combined ignore rules. Git did not flag the semantic conflict caused by `main` removing the old integer-based `WatchlistEntry`, so I restored that model with a UUID `film_id`, added the `entry.film` and `entry.user` relationships, and updated the remaining integer references in the service, route documentation, and tests.

I verified the resolution with a repository-wide conflict-marker and integer-reference search, three passing focused watchlist tests, seven passing tests in the complete suite, successful Python compilation, and `git diff --check`.
