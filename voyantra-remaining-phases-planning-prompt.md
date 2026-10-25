# VOYANTRA: Planning Prompt for Remaining Phases (v2)

Copy everything below the line into your AI agent. Read `voyantra-agent-rules.md` and `Voyantra_Full_Specification.md` first.

---

You are a senior software architect and technical program manager. Produce a detailed implementation plan for the REMAINING phases (4, 5, 6) of VOYANTRA, a trip-planning platform for Pondicherry and Chennai, India.

## CONTEXT
- Stack: Python 3.14 (FastAPI, Service-Repository pattern), MongoDB `voyantra_db`, Vite/React + Tailwind + Leaflet/OSM, Gemini RAG.
- Constraint: 100% free-tier and open-source. No paid APIs.
- Phases 1, 2, 3 and 3.5 are complete (auth, ranking, Gemini itineraries, rule-based crowd engine, festival calendar, GPS city switching).
- First, read the existing codebase and the spec. Plan around the real structure (folders, services, repositories, collections, components) and reuse existing code: Haversine util, crowd engine, festival JSON files, itinerary schema. Do not invent parts that don't exist.

## PHASES TO PLAN

### Phase 4: OSRM routing and navigation
- Turn-by-turn route polylines on Leaflet (driving + walking) for each day's itinerary.
- Stop-order optimization within a day, treated as TSP WITH TIME WINDOWS: time-anchored stops (sunset beach slots, temple pooja hours, opening hours, meal times, Phase 3 quiet windows) are fixed first, and flexible stops are optimized around them.
- Inter-stop duration (min) and distance (km) used to adjust schedule gaps. Call these "estimated travel times", never "live".

### Phase 5: Crowdsourced real-time crowd reporting
- 1-tap reports: Serene, Moderate, Bustling, Overcrowded.
- Time-decayed aggregation, blended with the Phase 3 rule baseline.
- Anomaly alerts for sudden surges or blockages.
- Reports double as the project's only real validation data for the crowd engine.

### Phase 6 (REVISED): Data-calibrated seasonality
Replaces the original "XGBoost + SHAP" plan. Reason: no free source provides hourly or per-place crowd data for these cities. The only real data found is monthly district-level arrivals (a few dozen rows). XGBoost on that overfits, and a model trained on rule-generated data only relearns the rules.

Scope:
- Build a **monthly seasonality index** (`month visitors / average month visitors in that year`, averaged across years) from real government data and use it in the Phase 3 seasonal rule instead of the hardcoded "+15% Dec-Jan".
- Keep hour-of-day, weekend and festival rules unchanged.
- Show the data source and years in the UI. Explain results directly (e.g. "Dec = 1.18x an average month"). No SHAP.

Known data sources (verify each before relying on it):
- Chennai: Tamil Nadu tourism department district-wise statistics (e.g. a 2024 statistics PDF that appears to hold monthly district tables) and the state statistical handbook (yearly district totals). The monthly PDF must be opened and confirmed. Methodology (how visitors are counted) is unknown and must be checked.
- Pondicherry: Directorate of Economics and Statistics, Puducherry (annual arrivals only) and the Ministry of Tourism 2014 state survey (month-wise estimates, one year, old). No recent monthly source was found. Treat as a rough prior labeled "2014 survey data".
- Exclude or flag 2020 and 2021 (COVID).
- Open-Meteo (free, keyless) may supply weather if a simple regression is tested later.
- Do NOT use scraped Google Popular Times or review-site data.

XGBoost re-entry gate (all must hold, and the human confirms): (a) Phase 5 has N real reports per place over W weeks (human sets N and W), (b) a time-based held-out test beats the rules-only baseline on MAE, (c) xgboost and shap import on Python 3.14, or a fallback is approved.

## DESIGN DECISIONS TO START FROM (challenge any you disagree with, and say why)
Phase 4:
- Self-host OSRM in Docker (Geofabrik South India or Tamil Nadu/Puducherry extract), not the public demo server. Fall back to Haversine x road factor if OSRM is down, and tell the UI the estimate is approximate.
- Use the OSRM /table matrix. Brute force for 8 stops or fewer.
- Time-of-day traffic multiplier for Chennai (OSRM has no traffic data).
- Flag or penalize routes through Phase 3 festival-closure streets.
- "Optimize order" button only. No auto-reorder after drag-and-drop, and Gemini refinements must not undo the solver's order.
- Cache route and matrix results in MongoDB.

Phase 5:
- No Supabase. MongoDB TTL collection plus 30-60s polling or a FastAPI WebSocket.
- Anti-abuse: geofence each report to ~200 m of the place (reuse the GPS code), rate-limit per user per place (1 per 15-30 min), store only place_id plus timestamp, never raw user location.
- Exponential decay weighting (half-life ~30 min). TTL index is for cleanup only.
- Cold start: define behavior with too few reports ("no live reports, showing estimate") and a minimum report count before overriding the rules.
- Anomaly definition, e.g. 3+ reports two levels above the predicted level within 30 min.
- Store each report with a feature snapshot (rule prediction, hour, day, month, festival flag, weather) so predicted vs reported levels can be compared later.
- Tag any test or demo reports `simulated`, and never mix them with real reports.

Phase 6:
- The index is built by a reproducible script from a raw data file. No hand-typed numbers. Store source URL, years used, licence and exclusions in the output JSON.
- Compare the measured index with the old +15% assumption and document the difference.
- Pondicherry: use the 2014 monthly shape as a labeled rough prior. Only blend with Chennai's pattern if the two plausibly match, and mark that as an assumption.
- State plainly in the UI and docs that this is district-level seasonality, not per-place or hourly data.

## DELIVERABLES (produce all, in this order)
1. **Codebase audit summary:** existing modules, collections and components each phase will touch or reuse.
2. **Architecture per phase:** components, data flow (Mermaid), new vs modified files.
3. **Data models:** MongoDB schemas (fields, types, indexes, TTL) for route cache, crowd reports, feature snapshots, and the seasonality data file/collection (schema, provenance fields).
4. **API contract:** every new or changed endpoint with method, path, request and response JSON, auth rules and error cases, in the table format of the spec's Section 5.
5. **Frontend plan:** new React components, state changes, Leaflet layers, UX flows (report button, route overlay, seasonality source note in the crowd popover), with mobile behavior.
6. **Data acquisition plan for Phase 6:** for each source, the exact file or page, what it contains, format, years, licence, extraction steps, and the open check (e.g. "confirm the PDF has monthly tables").
7. **Task breakdown:** epics -> tasks -> subtasks with size estimates (S/M/L), dependencies, and which tasks can run in parallel.
8. **Sequencing roadmap:** recommended order with reasoning. Start Phase 5 data logging early and run Phase 4 in parallel. Phase 6 data collection and index building can start immediately since it needs no new users.
9. **Acceptance criteria per phase:** measurable and testable, e.g.
   - Phase 4: total travel time reduced by X% vs unoptimized order on a set of test itineraries; time-anchored stops never violated; graceful behavior when OSRM is down.
   - Phase 5: spam-resistance test cases, decay math verified, cold-start behavior verified.
   - Phase 6: index reproducible from script and raw data; engine output changes when the index changes (test); UI shows source and years; difference from the old +15% documented; limits note written.
10. **Test plan:** unit, integration, e2e and abuse tests per phase, and how they extend the existing QA suite.
11. **Risk register:** top risks per phase with likelihood, impact and mitigation. Include OSRM hosting and RAM, free-tier limits, sparse crowd data, report bias, Gemini refinement conflicting with the solver, unconfirmed monthly data, unknown visitor-counting methodology, outdated Pondicherry data, and source licensing.
12. **Spec update:** proposed changes to Voyantra_Full_Specification.md as a diff-style draft, including the revised Phase 6 name and roadmap row ("Data-calibrated seasonality") and a note that XGBoost/SHAP is deferred behind the re-entry gate.
13. **Open questions:** at most 5, ranked by how much they block the plan, each with a default assumption so work can proceed.

## RULES
- Plan only. No implementation code (schemas and JSON examples are fine).
- Every recommendation must respect the free-tier, open-source constraint. Mark any claim you are not sure of as "VERIFY".
- Be specific to this codebase. Avoid generic advice.
- Pondicherry and Chennai are the only supported cities.
- Where a decision has tradeoffs, give a short options table and a clear recommendation.
- Never invent real-world data (visitor counts, festival dates, closures). Cite the source or mark `NEEDS HUMAN VERIFICATION`.
- End with a one-page executive summary: phases, order, effort estimate, the 3 biggest risks, and the go/no-go gates.
