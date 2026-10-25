# VOYANTRA: Agent Rules

Read this file and `Voyantra_Full_Specification.md` before every task. These rules override any default behavior.

## 1. Project Constraints (never violate)
- **Cities:** Pondicherry and Chennai, India ONLY. Reject or redirect anything else.
- **Cost:** 100% free-tier and open-source. Never add a paid API, paid service, or a dependency that needs a credit card. If unsure whether something is free, mark it `VERIFY` and ask.
- **Stack:** Python 3.14 + FastAPI, MongoDB `voyantra_db`, Vite/React + Tailwind + Leaflet/OSM, Gemini RAG. Do not introduce a new database, framework, or major library without approval (e.g. no Supabase; Phase 5 uses MongoDB TTL).
- **Architecture:** Keep the Service-Repository pattern. No business logic or DB queries inside routers. Reuse existing utilities (Haversine, crowd engine, festival JSON, itinerary schema) instead of rewriting them.

## 2. Working Process
1. **One phase, one task at a time.** Never work on Phases 4, 5, and 6 together.
2. **Plan first.** For any task larger than a small fix, write a short plan (files to change, approach, risks) and WAIT for my approval before writing code.
3. **Small changes.** One feature per change, with its tests. Keep diffs reviewable (aim for under about 300 changed lines).
4. **Commit after each working step** with a clear message. Never leave the repo in a broken state.
5. **Show me the diff summary** after each task: files changed, what and why, tests added, anything uncertain.
6. Do not refactor, rename, or reformat code unrelated to the task.

## 3. Hard "Never Do" List
- Never commit secrets. API keys live in `.env` (gitignored). Never put keys in frontend code, logs, or API responses.
- Never store plaintext passwords. Never change auth, JWT, or role checks without explicit approval.
- Never delete or overwrite MongoDB collections or user data. Schema changes need a migration plan I approve.
- Never mark a task "verified", "complete", or "passing" unless you actually ran the tests or the app and show the real output.
- Never write tests that only assert what the code already does. Tests must check the spec's expected behavior.
- Never invent data for real-world facts: festival dates, road closures, opening hours, dietary status, coordinates. Use a cited source or flag it as `NEEDS HUMAN VERIFICATION`.
- Never generate synthetic footfall or crowd data and present it as real. Synthetic data must be labeled `simulated` in code, DB, and UI.
- Never silently swallow errors or return stack traces to clients.
- Never claim a library works on Python 3.14 without checking it (`pip install` / import test). Report the result.

## 4. Code Standards
- **Backend:** type hints, Pydantic models for all request/response bodies, async where the existing code is async, meaningful HTTP status codes (401, 403, 404, 422), and input validation on every endpoint.
- **Frontend:** functional components and hooks, Tailwind only, no inline secrets, handle loading, empty, and error states for every data fetch. Must work at 375px and 1440px.
- **Database:** every new collection documents its schema and indexes. Add TTL indexes where data expires. Use parameterized queries and reject operator injection (`$ne`, `$gt`) in user input.
- **AI/Gemini calls:** set timeouts, handle 429 and invalid-key errors with a graceful fallback, validate model output against a schema, and only allow places that exist in the catalog. Treat user prompts as untrusted (prompt-injection safe).
- Keep functions small and named for what they do. Comment the "why", not the "what".

## 5. Testing Requirements (Definition of Done)
A task is done only when ALL are true:
- [ ] Code runs with no errors or new console warnings
- [ ] New unit tests added and passing, existing tests still passing (show output)
- [ ] Edge cases covered: empty input, invalid input, boundary values, service down
- [ ] Spec-defined behavior verified (e.g. crowd rules, 70 km GPS radius, dietary hard filter)
- [ ] API contract matches the spec table; spec updated if the contract changed
- [ ] No hardcoded secrets, no leftover debug code
- [ ] For UI: checked in the browser at mobile and desktop widths, with a screenshot or description of what was seen
- [ ] A short summary written for me: what changed, how it was tested, known limitations

## 6. Phase-Specific Rules

### Phase 4: OSRM Routing
- Self-host OSRM via Docker. Do not depend on the public demo server for core features.
- If OSRM is unreachable, fall back to Haversine x road factor and tell the UI the estimate is approximate.
- Treat ordering as TSP **with time windows**: time-anchored stops (sunset beach, pooja hours, opening hours, meals, crowd quiet windows) are fixed first.
- Label times as "estimated travel time", never "live".
- Do not auto-reorder after drag-and-drop. Only reorder on the explicit "Optimize order" action. Gemini refinement must not undo solver ordering.
- Cache route and matrix results in MongoDB.

### Phase 5: Crowdsourced Reports
- Geofence reports to about 200 m of the place. Rate-limit per user per place. Store only `place_id` and timestamp, never raw user location.
- Use exponential decay weighting. TTL index is for cleanup only.
- Define and implement cold-start behavior (too few reports means show the rule-based estimate and say so).
- Store a feature snapshot (rule prediction, hour, day, festival flag, weather) with every report from day one.
- Include abuse tests: spam, spoofed location, rapid repeats.
- Reports are also the project's only real validation data. Keep them queryable by place, hour and day so predicted vs reported levels can be compared. Do not mix simulated reports with real ones; tag any test data `simulated`.

### Phase 6: Data-Calibrated Seasonality (replaces XGBoost + SHAP)
- Do NOT build or train an XGBoost/ML model in this phase. Real data is only monthly district totals (a few dozen rows), which is too little and too coarse. A model trained on rule-generated data only relearns the rules, so it is forbidden.
- Build a **monthly seasonality index** (`month visitors / average month visitors in that year`, averaged across years) from real government data:
  - Chennai: Tamil Nadu tourism department monthly district data, 2022 onward. Flag or exclude 2020 and 2021 (COVID).
  - Pondicherry: only the Ministry of Tourism 2014 survey month shape plus annual figures. Label it "2014 survey data" and mark it as a rough prior.
- Before using any file, confirm it really contains monthly data and read its methodology notes. Record source URL, year(s) and licence in the data file. If a figure cannot be sourced, mark it `NEEDS HUMAN VERIFICATION`.
- The index must be reproducible: a script plus the raw data file produce the same JSON every run. No hand-typed numbers.
- Compare the measured index against the old "+15% Dec-Jan" assumption and document the difference. Replace the hardcoded value with the index.
- Keep hour-of-day, weekend and festival rules unchanged. No real data supports replacing them.
- The UI must show where the seasonal factor comes from (source and years). Never present district-level data as per-place or hourly data.
- Explain results directly (e.g. "Dec = 1.18x an average month"). Do not add SHAP.
- XGBoost/SHAP may return only if ALL are true and I confirm: (a) Phase 5 has collected at least N real reports per place over at least W weeks (I will set N and W), (b) a time-based held-out test shows the model beats the rules-only baseline on MAE, (c) xgboost and shap install and import on Python 3.14, or a fallback is approved.

## 7. When Unsure
- Stop and ask me. A question is cheaper than a wrong assumption.
- Ask at most 3 questions at a time, each with your default assumption so I can reply "yes".
- If a requirement conflicts with the spec or with these rules, point out the conflict rather than choosing silently.

## 8. Progress Reporting Format
At the end of every task, reply with:
1. **Done:** what was implemented
2. **Tests:** what was run, with pass/fail counts
3. **Not verified:** anything you could not test, and why
4. **Needs human:** decisions, data, keys, or real-world checks only I can do
5. **Next:** suggested next small task
