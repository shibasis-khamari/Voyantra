# Voyantra 2.0

## Approved Conversational AI, Voice Assistant and Personalized Travel Intelligence Specification

**Document status:** Final and approved functional direction\
**Product:** Voyantra\
**Primary travel destinations:** Pondicherry and Chennai\
**Supported conversation languages:** English, Hindi and Tamil\
**Primary voice interaction:** Push-to-Talk\
**Secondary voice interaction:** Live Conversation

------------------------------------------------------------------------

## 1. Executive Summary

Voyantra 2.0 is envisioned as a multilingual, voice-enabled,
general-purpose conversational AI with specialized travel intelligence.
It should feel like a natural AI assistant rather than a form-based
itinerary generator or a chatbot restricted to a small set of travel
intents.

Users should be able to ask general questions, learn about destinations,
discover places, explore hotels and restaurants, request travel advice,
generate personalized itineraries, and modify existing plans through
ordinary conversation. They should not have to choose a feature or
workflow before asking a question. The assistant should understand the
request and use the relevant application capabilities when needed.

Voyantra will support text and voice interactions in **English, Hindi
and Tamil**. Push-to-Talk will be the primary voice experience, while
Live Conversation will be available as an optional secondary mode. Both
modes must use the same conversational engine, context and memory
services so that the assistant behaves consistently regardless of how
the user communicates.

The travel experience will prioritize **Pondicherry and Chennai**. The
assistant may provide general knowledge and destination information
about other Indian and international places, but the initial scope for
full local travel discovery and itinerary generation is limited to
Pondicherry and Chennai.

Personalization is a core capability. Itineraries and recommendations
may account for age groups, family composition, group needs, interests,
budget, mobility and accessibility requirements, food preferences,
religious or cultural preferences, travel pace and trip duration. These
preferences must be requested or explicitly supplied by the user; the
system must not infer sensitive characteristics such as religion from a
person's name, location or other indirect signals.

This document defines the approved product behaviour, functional
requirements, architecture, memory model, voice and language experience,
personalization rules, safety and quality requirements, and a phased
implementation approach.

------------------------------------------------------------------------

## 2. Product Vision and Design Principles

### 2.1 Product vision

**Voyantra should understand the traveller before helping plan the
journey.**

It should combine the flexibility of a general conversational assistant
with reliable travel-specific tools. The user should feel that they are
speaking with one assistant that can answer broad questions and, when
appropriate, perform travel-related tasks.

### 2.2 Core design principles

1.  **Conversation first:** Users can start with a natural question.
    They are not required to select "hotel", "place" or "itinerary"
    before chatting.
2.  **Tools when useful:** The AI may use place, hotel, restaurant, map,
    weather or itinerary services when the request requires current or
    structured information.
3.  **No forced itinerary flow:** General questions should receive
    direct answers. The assistant must not turn every conversation into
    an itinerary questionnaire.
4.  **One assistant across modalities:** Text, Push-to-Talk and Live
    Conversation use the same conversation and memory architecture.
5.  **Language continuity:** The assistant should respond in the user's
    selected or detected language and allow language changes without
    losing context.
6.  **Personalization without stereotyping:** User preferences guide
    recommendations, but age, religion, culture or family role must
    never be used to make rigid assumptions.
7.  **Grounded travel information:** Specific hotels, restaurants,
    opening hours, prices, availability and travel conditions must be
    sourced from reliable data or clearly identified as estimates.
8.  **User control:** Users control voice playback, saved preferences,
    memory and microphone access.
9.  **Transparent limitations:** When data is unavailable or uncertain,
    the assistant should say so instead of inventing details.
10. **Incremental delivery:** Build and test the core conversational
    experience before adding advanced live voice behaviour.

------------------------------------------------------------------------

## 3. Geographic Scope and Service Boundaries

Voyantra has a deliberate geographic focus.

  -----------------------------------------------------------------------
  Request type            Initial supported scope Expected behaviour
  ----------------------- ----------------------- -----------------------
  General knowledge       Worldwide               Answer general
                                                  questions where the
                                                  model has reliable
                                                  knowledge.

  Famous destination      India and international Describe history,
  information             destinations            culture, attractions
                                                  and general visitor
                                                  information.

  Full local place        Pondicherry and Chennai Use the application's
  discovery                                       supported place data
                                                  and discovery services.

  Hotel discovery         Pondicherry and Chennai Search available,
                                                  verified hotel
                                                  information where
                                                  integrations permit.

  Restaurant discovery    Pondicherry and Chennai Search relevant
                                                  restaurant information
                                                  where integrations
                                                  permit.

  Itinerary generation    Pondicherry and Chennai Generate structured,
                                                  location-aware
                                                  itineraries.

  Itinerary modification  Existing supported      Add, remove, replace,
                          itineraries             reorder or adjust
                                                  itinerary activities.

  Itinerary generation    Outside initial scope   Explain the current
  elsewhere                                       limitation politely; do
                                                  not pretend to have
                                                  full local planning
                                                  support.
  -----------------------------------------------------------------------

The assistant may answer "Tell me about the Eiffel Tower" or "What is
special about Jaipur?" It should not claim that Voyantra can currently
provide the same end-to-end local planning services for every
destination.

The geographic policy should be centralized in backend configuration or
a destination-support service. It should not be duplicated
inconsistently across prompts, frontend components and individual API
routes.

------------------------------------------------------------------------

## 4. General Conversational AI

### 4.1 Expected behaviour

The assistant must support natural conversation beyond itinerary
generation. Examples include:

-   "Why is Pondicherry famous?"
-   "Explain French colonial architecture."
-   "What is the difference between a beach and a lagoon?"
-   "Tell me about the history of Mahabalipuram."
-   "What should I know before visiting a temple?"
-   "Suggest something interesting to do this weekend."

The AI should answer the question directly, provide useful context and
offer a relevant next step only when it adds value. It should not
repeatedly ask the user to provide dates, budget or group size when
those details are irrelevant to the question.

### 4.2 Intent recognition without restrictive routing

The system may classify a message to help decide whether tools are
needed, but classification must not become a gate that blocks normal
conversation.

A practical decision process is:

1.  Receive the user's message or transcribed speech.
2.  Load the current conversation context and applicable saved
    preferences.
3.  Identify the user's immediate goal and relevant entities.
4.  Decide whether the answer can be produced directly or requires a
    tool.
5.  If a tool is required, call the appropriate service with validated
    parameters.
6.  Generate a natural response using the tool results and conversation
    context.
7.  Save the user and assistant turns and any permitted conversation
    state.

The model should be able to answer general questions even when no travel
tool is called.

------------------------------------------------------------------------

## 5. Travel Discovery Capabilities

### 5.1 Place discovery

Users should be able to ask about a place in ordinary language. For
example:

> "Tell me about Paradise Beach."

A useful response may include:

-   A concise description and what makes the place notable.
-   Its location and how to reach it, when reliable data is available.
-   Main activities and experiences.
-   Typical visit duration, clearly labelled as an estimate.
-   Best time or season to visit, where supported by reliable
    information.
-   Accessibility or practical visitor considerations, where known.
-   Nearby attractions, where supported by location data.
-   Relevant caveats, such as transport or access restrictions that may
    change.

Follow-up questions should retain the place context. If the user asks
"Is it good for children?", the assistant should understand that "it"
refers to the place just discussed.

### 5.2 Hotel discovery

Users may ask broad questions such as "Suggest good hotels in
Pondicherry." The assistant should provide a helpful overview and ask a
focused question only when needed, such as whether the user prefers
budget, mid-range, luxury, beachfront or a particular neighbourhood.

Hotel recommendations must distinguish verified facts from general
descriptions. Do not invent hotel names, addresses, facilities, prices,
ratings or room availability. If live booking availability is not
integrated, state that the user should confirm current rates and
availability with the property or booking provider.

### 5.3 Restaurant discovery

Restaurant discovery should support preferences such as cuisine, budget,
location, dietary requirements and group needs. Dietary preferences must
be treated as user-provided requirements, not inferred from religion or
identity.

Where possible, verify details such as opening hours, location and
current status. If information is uncertain or may have changed, say so.

### 5.4 Travel information

The assistant may answer questions about local transport, practical
visitor guidance, travel seasons, packing, cultural etiquette and
general trip preparation. Time-sensitive claims should be checked
through appropriate data services when available.

------------------------------------------------------------------------

## 6. Intelligent and Personalized Itinerary Generation

### 6.1 When itinerary generation should start

Itinerary generation should begin when the user asks for a plan or
clearly requests an itinerary. It should not be triggered merely because
a user mentions a destination.

For example:

-   "What is special about Pondicherry?" → Answer the question; do not
    automatically generate an itinerary.
-   "Plan a two-day trip to Pondicherry." → Start itinerary planning.
-   "Add Paradise Beach to the plan we discussed." → Modify the active
    itinerary if the context identifies it.

### 6.2 Information that may influence an itinerary

The system should use information supplied by the user, relevant saved
preferences (when enabled), and reliable travel data.

  -----------------------------------------------------------------------
  Factor                              Possible personalization
  ----------------------------------- -----------------------------------
  Trip duration                       Half-day, one-day, weekend or
                                      multi-day schedule.

  Age groups                          Offer activities and pacing
                                      suitable for the travellers,
                                      without stereotyping.

  Group composition                   Individual, couple, family, friends
                                      or mixed-age group.

  Interests                           Beaches, heritage, nature,
                                      spirituality, food, shopping,
                                      photography, adventure or
                                      relaxation.

  Budget                              Budget-conscious, moderate or
                                      premium options.

  Travel pace                         Relaxed, balanced or packed
                                      schedule.

  Mobility and accessibility          Walking distance, steps, accessible
                                      facilities and transport needs.

  Food preferences                    Vegetarian, vegan, Jain, halal or
                                      other explicitly stated dietary
                                      requirements.

  Religious and cultural preferences  User-requested places of worship,
                                      observances, cultural experiences
                                      or practical requirements.

  Accommodation preferences           Preferred area, property type and
                                      budget.

  Transport                           Walking, public transport, taxi,
                                      personal vehicle or other stated
                                      preference.

  Group size                          Practical suitability, capacity and
                                      coordination needs.
  -----------------------------------------------------------------------

Not every request requires every detail. The assistant should ask only
for information that materially affects the result. It should also be
able to create a reasonable first draft using clearly stated assumptions
when the user prefers not to answer more questions.

### 6.3 Age-aware recommendations

The assistant may offer options suitable for children, young adults,
adults and senior travellers. Age should influence practical
considerations such as pacing, rest breaks, activity suitability and
accessibility, but should not determine what a person is capable of
enjoying.

For a mixed-age family, the itinerary should balance group activities
and comfort. It should not assume that every older traveller wants a
slow trip or that every young traveller wants nightlife or adventure.

Where an activity has an actual age, height, health, safety or operator
restriction, the assistant should communicate the verified restriction
rather than making a broad assumption based on age.

### 6.4 Religious and cultural preferences

Users may explicitly request an itinerary that considers a religious or
cultural preference. The assistant can then include relevant places of
worship, heritage sites, prayer or observance considerations, or dietary
requirements where reliable information is available.

Mandatory safeguards:

-   Never infer religion from a name, appearance, language, location or
    family composition.
-   Ask about religious or cultural preferences only when relevant and
    do so neutrally.
-   Do not assume that all members of a group share the same beliefs.
-   Do not equate religion with a food preference. Ask separately about
    dietary requirements.
-   Treat religious preferences as sensitive information. Do not save
    them to long-term memory unless the user explicitly opts in.
-   Allow the user to change or remove such preferences.
-   Present religious and cultural information respectfully and avoid
    unsupported claims about practices or access rules.

### 6.5 Multiple itinerary alternatives

For suitable requests, Voyantra should be able to offer multiple
alternatives, for example:

1.  **Relaxed itinerary:** fewer stops, more time at each place and
    breaks.
2.  **Cultural itinerary:** heritage, architecture, museums and places
    of cultural interest.
3.  **Activity-focused itinerary:** outdoor experiences and activities,
    subject to verified availability and suitability.

The alternatives should be meaningfully different, not merely the same
places in a different order. Users should be able to select one and
request changes conversationally.

### 6.6 Itinerary quality requirements

A generated itinerary should consider:

-   Geographic proximity and realistic travel time.
-   Opening days and hours when reliable data is available.
-   Activity duration and reasonable breaks.
-   Meal periods and user dietary requirements.
-   The user's selected travel pace.
-   Transport mode and practical constraints.
-   Seasonal or access limitations where verified.
-   The needs of all members of a group.

The itinerary should clearly distinguish verified schedules from
estimates. The system must not fabricate opening hours, ticket prices,
travel times or availability.

### 6.7 Conversational itinerary editing

Users should be able to say:

-   "Add the museum on the second day."
-   "Replace the beach with a heritage site."
-   "Make the plan more relaxed."
-   "Remove expensive restaurants."
-   "Can we start later?"
-   "Show me another version for children and grandparents?"

The system should identify the active itinerary, apply the requested
change, preserve unaffected items and return the updated plan. If the
target is ambiguous, ask one concise clarification instead of changing
the wrong item.

------------------------------------------------------------------------

## 7. Memory and Conversation History

Voyantra will support both current-chat context and optional
cross-session memory. These are separate capabilities and should be
implemented separately.

### 7.1 Short-term conversation memory

Short-term memory maintains context within the active conversation. It
should include relevant details such as:

-   Previously discussed destinations and places.
-   The current user request and unresolved questions.
-   Selected hotels or restaurants.
-   The active itinerary and its version.
-   User corrections and choices.
-   Language used in recent turns.
-   References such as "that beach", "the second option" or "the hotel
    you mentioned".

The assistant should resolve references from conversation history and
avoid asking users to repeat information that is already available.

### 7.2 Conversation history

Users should be able to return to previous conversations, open them and
continue where appropriate. Conversation history is not the same as a
compact long-term preference profile. It preserves the actual
conversation records subject to the application's retention and deletion
policies.

### 7.3 Optional long-term memory

With user consent, Voyantra may retain a concise profile of useful
preferences, such as:

-   Preferred language.
-   Preferred travel pace.
-   Typical budget range.
-   Favourite activity types.
-   Preferred accommodation style.
-   Dietary preferences.
-   Accessibility requirements.
-   Other travel preferences the user explicitly asks the assistant to
    remember.

Do not save every message as a permanent preference. A one-time request
should not automatically become a permanent user trait.

Sensitive preferences, including religious beliefs, require explicit
opt-in before being saved. The user should be able to review, edit,
disable and delete saved preferences.

### 7.4 Memory controls

The product should provide clear controls to:

-   Enable or disable long-term memory.
-   View saved preferences.
-   Edit or remove individual preferences.
-   Clear saved preferences.
-   Delete a conversation from history.
-   Understand the difference between deleting a chat and deleting a
    saved preference.

A memory-disabled user should still be able to use the current
conversation context while that conversation is active.

### 7.5 Suggested data separation

Keep conversation records, active session state and long-term
preferences logically separate. A possible data model is:

-   `users`: account and application settings.
-   `conversations`: conversation metadata, title, timestamps and
    status.
-   `messages`: role, content, language, timestamps and optional tool
    metadata.
-   `user_preferences`: explicitly saved, user-controlled preferences
    and consent metadata.
-   `itineraries`: structured itinerary records and versions.
-   `itinerary_items`: places, dates, order, notes and source
    references.

The actual schema should be adapted to the current Voyantra database and
codebase rather than introducing duplicate collections unnecessarily.

------------------------------------------------------------------------

## 8. Multilingual Conversation: English, Hindi and Tamil

### 8.1 Supported languages

Voyantra will support exactly these three user-facing conversation
languages initially:

  Language   Code   Typical script
  ---------- ------ ----------------
  English    `en`   Latin
  Hindi      `hi`   Devanagari
  Tamil      `ta`   Tamil

The supported language list should be centrally configured and
consistently enforced across text, speech recognition, AI response
generation and speech synthesis.

### 8.2 Automatic language detection

Automatic detection should be enabled by default where the language can
be identified confidently. Users should also be able to choose a
preferred language manually in settings or within a conversation.

The assistant should generally respond in the language of the user's
latest message, unless the user has explicitly selected a conversation
language or requested a different response language.

### 8.3 Language switching

Users may switch languages at any point. For example:

1.  User asks about Paradise Beach in English.
2.  User asks a follow-up in Hindi.
3.  User asks for nearby places in Tamil.

The assistant should preserve the topic, place references and itinerary
state throughout the switch. Language changes must not create a new
conversation or reset memory.

### 8.4 Mixed-language messages

Users may naturally mix English, Hindi and Tamil. The system should
handle common code-switching where possible. If the language or meaning
is unclear, it should ask for clarification rather than silently
misinterpret the request.

### 8.5 Translation and place names

Place names, hotel names, restaurant names and official names should
remain recognizable. The assistant may provide a local-script rendering
alongside the official name when helpful. It should not translate proper
names in a way that makes search or navigation difficult.

### 8.6 Quality parity

English, Hindi and Tamil should receive comparable reasoning and feature
support. Itinerary quality, tool access, memory and personalization
should not be reduced for Hindi or Tamil users.

Testing must include native or fluent review of Hindi and Tamil
responses, especially speech recognition, pronunciation, place names and
culturally specific content.

------------------------------------------------------------------------

## 9. Voice Assistant

Voyantra will offer two voice interaction modes. **Push-to-Talk is the
primary and default voice experience. Live Conversation is an optional
secondary mode.**

### 9.1 Push-to-Talk --- Primary mode

Push-to-Talk is designed for simple, deliberate voice messages.

Expected flow:

1.  The user taps the microphone button.
2.  The application requests microphone permission if it has not already
    been granted.
3.  A visible recording indicator shows that audio is being captured.
4.  The user speaks in English, Hindi or Tamil.
5.  The user taps again or uses the stop control to finish recording.
6.  Speech recognition converts the audio into text.
7.  The recognized text is shown to the user for review, where
    practical.
8.  The user can edit the transcript or send it.
9.  The conversational engine processes the message using the same
    context and tools as typed messages.
10. The assistant displays its response and optionally reads it aloud.

Required controls:

-   Start and stop recording.
-   Clear recording/listening status.
-   Transcript preview and edit option.
-   Cancel recording.
-   Send recognized text.
-   Play, pause and replay generated audio.
-   Enable or disable automatic voice responses.
-   Handle microphone denial and speech-recognition failures gracefully.

Push-to-Talk should remain usable even when text-to-speech is disabled.
Users must always be able to read the answer.

### 9.2 Live Conversation --- Secondary mode

Live Conversation provides an optional, more continuous voice
experience.

Expected behaviour:

-   The user explicitly starts a live voice session.
-   The application clearly indicates when it is listening and when the
    AI is speaking.
-   Speech is detected and processed without requiring a button press
    for every turn.
-   The assistant responds with generated speech and, where appropriate,
    visible text.
-   The user can interrupt the assistant while it is speaking.
-   The user can pause, mute or end the session.
-   The session retains the same conversation context as text and
    Push-to-Talk.

Live Conversation should not start automatically. The user must
deliberately activate it and be able to stop it at any time.

### 9.3 Voice privacy and reliability

-   Request microphone permission only when needed.
-   Show an unmistakable recording or listening indicator.
-   Do not record in the background without an explicit, active user
    action.
-   Provide a clear way to stop or exit voice mode.
-   Explain relevant audio processing and retention in the product's
    privacy information.
-   Handle network interruptions, timeouts, unsupported audio and empty
    recordings.
-   Do not send raw audio to unrelated services.
-   Keep text input available as a fallback.

### 9.4 Speech recognition and speech synthesis

The speech-to-text and text-to-speech providers should be selected based
on reliable support for English, Hindi and Tamil, latency, cost,
privacy, API availability and quality in real-world noisy environments.

The existing Gemini integration should be evaluated before adding
another provider. Avoid introducing multiple overlapping speech services
without a clear need. Provider-specific functionality should be hidden
behind backend service interfaces so that providers can be changed
without rewriting the conversational engine.

------------------------------------------------------------------------

## 10. Unified Conversational Architecture

Text, Push-to-Talk and Live Conversation should converge on a common
conversational pipeline.

### 10.1 High-level architecture

``` text
                         USER
                           |
              +------------+------------+
              |            |            |
              v            v            v
          TEXT INPUT   PUSH-TO-TALK  LIVE VOICE
                           |            |
                           v            v
                     SPEECH-TO-TEXT  STREAMING/
                                     SPEECH INPUT
              |            |            |
              +------------+------------+
                           |
                           v
                  LANGUAGE IDENTIFICATION
                    English / Hindi / Tamil
                           |
                           v
                 CONVERSATION ORCHESTRATOR
                           |
               +-----------+-----------+
               |                       |
               v                       v
          CONTEXT SERVICE         MEMORY SERVICE
               |                       |
               +-----------+-----------+
                           |
                           v
                     GEMINI / LLM
                           |
                 TOOL-USE DECISION
                           |
        +------------------+------------------+
        |                  |                  |
        v                  v                  v
   GENERAL ANSWER    TRAVEL DISCOVERY    ITINERARY ENGINE
                          |                  |
                  +-------+-------+          |
                  |       |       |          |
                PLACES  HOTELS RESTAURANTS   |
                  |       |       |          |
                  +-------+-------+----------+
                           |
                           v
                   RESPONSE GENERATOR
                           |
                  LANGUAGE AND FORMAT
                           |
                 +---------+---------+
                 |                   |
                 v                   v
             TEXT RESPONSE       TEXT-TO-SPEECH
                 |                   |
                 +---------+---------+
                           |
                           v
                          USER
```

### 10.2 Main components

**Frontend conversation interface** - Text composer and message
history. - Primary microphone control for Push-to-Talk. - Separate
control to enter Live Conversation. - Language selector and voice
playback controls. - Itinerary cards and structured results. - Visible
tool or loading status where useful.

**Conversation API** - Accepts text or recognized speech. - Validates
user, conversation and request data. - Loads context and permitted
preferences. - Sends a normalized message to the orchestration layer. -
Persists user and assistant messages.

**Conversation orchestrator** - Coordinates the model, context and
tools. - Determines when a tool is useful. - Validates tool parameters
and results. - Handles errors and retries safely. - Produces a final
response in the appropriate language.

**Context and memory service** - Loads recent conversation turns. -
Retrieves relevant earlier information when necessary. - Loads only
preferences permitted by the user's settings and consent. - Keeps
short-term context distinct from long-term memory.

**Travel services** - Place discovery. - Hotel discovery. - Restaurant
discovery. - Destination-support validation. - Itinerary generation and
editing. - Optional integrations for maps, routing, opening hours and
other live data.

**Voice services** - Speech-to-text. - Language identification or
verification. - Text-to-speech. - Live audio session management, if
supported by the selected provider.

### 10.3 Tool-use rules

The model should not invent tool results. Tool calls should be made
through backend-controlled functions with validated inputs. The backend
should enforce the geographic policy even if the model requests an
unsupported destination.

For example, a hotel query should use a hotel discovery service when
available. If the service fails, the assistant may provide general
guidance but must not fabricate current hotel listings.

------------------------------------------------------------------------

## 11. Response Design and User Experience

### 11.1 Natural responses

Responses should be conversational, useful and appropriately detailed.
The assistant should avoid:

-   Repeating the user's question unnecessarily.
-   Asking several questions at once.
-   Forcing itinerary generation.
-   Giving generic filler before answering.
-   Presenting guesses as verified facts.
-   Recommending the same places repeatedly without reason.

### 11.2 Structured travel responses

When useful, the frontend may render structured content such as:

-   Place information cards.
-   Hotel and restaurant result cards.
-   Itinerary day sections.
-   Map or navigation actions.
-   Alternative itinerary comparisons.
-   Estimated budget breakdowns.

The conversational answer should still make sense without the rich UI
component.

### 11.3 Clarifying questions

Ask a clarifying question only when the missing information materially
affects the result. Prefer one focused question at a time. If the user
asks for a broad first draft, use reasonable assumptions and label them
so the user can correct them.

### 11.4 Accessibility and usability

The interface should support keyboard navigation, readable contrast,
clear status indicators and accessible labels for microphone and
playback controls. Voice must be an additional way to interact, not a
requirement for using the product.

------------------------------------------------------------------------

## 12. Data Accuracy, Safety and Privacy

### 12.1 Factual accuracy

The assistant should distinguish:

-   Verified data returned by an integrated service.
-   General model knowledge.
-   Approximate estimates.
-   Information that is unknown or unavailable.

Time-sensitive information such as opening hours, ticket prices, hotel
rates, restaurant status, traffic and activity availability should be
verified through current sources when possible.

### 12.2 Personalization safeguards

-   Do not infer religion, dietary needs, disability or other sensitive
    preferences.
-   Ask only relevant questions and allow users to skip them.
-   Do not treat age as a proxy for ability or interests.
-   Support different preferences within one travelling group.
-   Explain when an itinerary uses assumptions.
-   Allow users to correct any preference or recommendation.

### 12.3 Privacy safeguards

-   Obtain consent for persistent memory.
-   Provide controls to view, edit and delete saved preferences.
-   Require explicit opt-in before retaining sensitive religious
    preferences.
-   Protect conversation records and account data with appropriate
    access controls.
-   Avoid storing raw voice recordings unless there is a documented need
    and clear user consent.
-   Follow applicable privacy and data-protection requirements.

### 12.4 Security

-   Keep API keys and provider credentials on the backend.
-   Validate user input and tool parameters.
-   Enforce user ownership checks for conversations, memory and
    itineraries.
-   Rate-limit expensive AI and voice endpoints.
-   Avoid exposing internal prompts, credentials or private tool output.
-   Log operational metadata without unnecessarily logging sensitive
    user content.

------------------------------------------------------------------------

## 13. Suggested API and Service Boundaries

The exact endpoint names should be aligned with the current Voyantra
backend. The following are conceptual service boundaries, not a claim
that these routes already exist.

  -----------------------------------------------------------------------
  Service                             Example responsibility
  ----------------------------------- -----------------------------------
  Conversation endpoint               Accept a text message and return an
                                      assistant response.

  Conversation history endpoint       List and retrieve the user's
                                      conversations.

  Memory preferences endpoint         Read, update or delete consented
                                      saved preferences.

  Speech transcription endpoint       Accept a short audio recording and
                                      return recognized text and
                                      language.

  Speech synthesis endpoint           Convert an assistant response into
                                      audio.

  Live voice session endpoint         Create, manage and end an
                                      authorized live session.

  Place discovery endpoint            Search supported destinations and
                                      places.

  Hotel discovery endpoint            Search accommodation information.

  Restaurant discovery endpoint       Search restaurants using relevant
                                      preferences.

  Itinerary endpoint                  Generate a new structured
                                      itinerary.

  Itinerary update endpoint           Modify an existing itinerary while
                                      preserving unaffected items.
  -----------------------------------------------------------------------

Every user-specific endpoint must verify authentication and ownership.
Voice and AI endpoints should have size, duration, rate and timeout
limits.

------------------------------------------------------------------------

## 14. Implementation Roadmap

Implement the redesign in stages. This reduces risk and makes it
possible to validate the conversational foundation before adding more
complex capabilities.

### Phase 1 --- Audit and conversational foundation

-   Inspect the existing chatbot frontend, backend routes, prompts and
    Gemini integration.
-   Document current message flow and data structures.
-   Identify existing place, hotel, restaurant and itinerary services.
-   Remove restrictive routing behaviour that prevents general
    conversation.
-   Establish a unified conversation API and normalized message format.
-   Add baseline conversation tests.

**Completion criteria:** Users can ask general questions and travel
questions naturally without being forced into itinerary generation.

### Phase 2 --- Context and conversation history

-   Persist messages and conversation metadata.
-   Load recent context for follow-up questions.
-   Support conversation listing and reopening.
-   Preserve references to places, hotels and active itineraries.
-   Handle context limits through summarization or retrieval without
    losing important decisions.

**Completion criteria:** Follow-up questions work reliably, and users
can reopen previous conversations.

### Phase 3 --- Optional long-term memory

-   Add explicit memory consent and settings.
-   Store a concise preference profile separately from conversation
    messages.
-   Add review, edit and deletion controls.
-   Apply stricter consent for sensitive preferences.
-   Test behaviour when memory is disabled.

**Completion criteria:** The assistant uses only permitted saved
preferences and users retain control over them.

### Phase 4 --- Travel discovery and tool orchestration

-   Connect place, hotel and restaurant discovery to verified services.
-   Centralize supported-destination rules.
-   Validate tool inputs and outputs.
-   Improve response handling when services fail or return incomplete
    data.
-   Preserve discovery context for follow-up questions.

**Completion criteria:** The assistant can answer general questions and
invoke real travel services when appropriate, without inventing results.

### Phase 5 --- Personalized itinerary engine

-   Define a structured itinerary data model.
-   Add preference-aware planning.
-   Support mixed-age and multi-person groups.
-   Add optional religious, cultural and dietary requirements with
    appropriate consent.
-   Generate multiple meaningfully different alternatives.
-   Support conversational itinerary editing and versioning.
-   Validate route feasibility, timing and data provenance.

**Completion criteria:** Users can generate, compare and modify
itineraries for Pondicherry and Chennai through conversation.

### Phase 6 --- Multilingual text conversations

-   Add English, Hindi and Tamil language settings.
-   Implement automatic language detection with a manual override.
-   Preserve context when the user switches languages.
-   Test mixed-language input and proper-name handling.
-   Review Hindi and Tamil output quality with fluent speakers.

**Completion criteria:** Core conversation, discovery and itinerary
functions work in all three languages.

### Phase 7 --- Push-to-Talk voice

-   Add microphone permission handling and recording controls.
-   Integrate speech-to-text for all three languages.
-   Show and allow editing of the recognized transcript.
-   Add text-to-speech playback.
-   Add playback and automatic-voice-response settings.
-   Test noise, accents, interruptions to recording, network failures
    and unsupported audio.

**Completion criteria:** Push-to-Talk is reliable and remains the
primary voice interaction.

### Phase 8 --- Live Conversation

-   Evaluate provider support for low-latency audio sessions.
-   Add explicit session start and stop.
-   Add listening and speaking indicators.
-   Support interruption and recovery from connection loss.
-   Reuse the same conversation context and preferences.
-   Test session authorization, cost controls and privacy behaviour.

**Completion criteria:** Users can optionally hold a continuous voice
conversation without creating a separate assistant identity or losing
context.

### Phase 9 --- Quality, security and release

-   Run functional, integration, regression and usability tests.
-   Measure response latency and tool reliability.
-   Test English, Hindi and Tamil across text and voice.
-   Review privacy, consent and deletion behaviour.
-   Test unsupported destinations and unavailable travel data.
-   Monitor errors, cost and user feedback after release.

**Completion criteria:** The application meets the acceptance criteria
below and has operational monitoring in place.

------------------------------------------------------------------------

## 15. Acceptance Criteria

The redesign should not be considered complete until the following
behaviours have been tested.

### Conversation

-   A user can ask general knowledge questions without triggering
    itinerary generation.
-   A user can ask travel questions in natural language.
-   Follow-up references such as "that place" resolve correctly when
    context is clear.
-   The assistant asks only necessary clarifying questions.

### Geographic scope

-   Full travel discovery and itinerary generation work for Pondicherry
    and Chennai.
-   General destination questions about other locations can be answered.
-   Unsupported itinerary requests receive a clear explanation of the
    current scope.
-   Backend services enforce the same geographic policy as the user
    interface.

### Personalization

-   Users can request age-aware recommendations without being
    stereotyped.
-   Mixed-age groups receive balanced suggestions.
-   Religious or cultural preferences are used only when explicitly
    supplied.
-   Sensitive preferences are not retained without explicit opt-in.
-   Dietary and accessibility requirements can be handled independently.
-   Users can request multiple alternatives and modify the selected
    itinerary.

### Memory

-   Current conversation context is retained during the conversation.
-   Previous conversations can be reopened.
-   Long-term memory is optional and user-controlled.
-   Disabling long-term memory does not disable current-chat context.
-   Users can review, edit and delete saved preferences.

### Language

-   English, Hindi and Tamil are supported.
-   The assistant responds in the selected or appropriately detected
    language.
-   Language switching does not reset conversation context.
-   Core travel features work in all three languages.

### Voice

-   Push-to-Talk is the primary voice mode.
-   Users can start, stop, cancel and review a recording.
-   Recognized text can be edited before sending.
-   Voice responses can be replayed or disabled.
-   Live Conversation is optional and has clear listening, speaking and
    stop controls.
-   Both voice modes use the same conversation history and context.
-   Microphone permissions and recording status are clear to the user.

### Accuracy and reliability

-   The assistant does not invent hotels, restaurants, prices, opening
    hours or availability.
-   Estimates are labelled as estimates.
-   Tool failures produce honest fallback responses.
-   API credentials are not exposed to the client.
-   User data is protected by authentication and ownership checks.

------------------------------------------------------------------------

## 16. Evaluation and Testing Strategy

A repeatable evaluation set should be maintained as the chatbot changes.
It should include:

1.  General knowledge questions unrelated to travel.
2.  Questions about Pondicherry and Chennai attractions.
3.  Place discovery and contextual follow-ups.
4.  Hotel and restaurant searches with unavailable or incomplete data.
5.  Itinerary generation for different trip durations and budgets.
6.  Mixed-age family planning.
7.  Explicit religious, cultural and dietary preferences.
8.  Itinerary modification and ambiguous references.
9.  English-to-Hindi-to-Tamil language switching.
10. English, Hindi and Tamil speech recognition in quiet and noisy
    settings.
11. Memory enabled, disabled and deleted scenarios.
12. Unsupported destination itinerary requests.
13. Tool timeout, network failure and invalid-result scenarios.

Suggested quality metrics:

  -----------------------------------------------------------------------
  Metric                              What it measures
  ----------------------------------- -----------------------------------
  Intent understanding                Whether the assistant understands
                                      the user's actual request.

  Context resolution                  Whether follow-up references are
                                      interpreted correctly.

  Tool correctness                    Whether the right service is used
                                      with valid parameters.

  Groundedness                        Whether factual travel claims are
                                      supported by available data.

  Itinerary feasibility               Whether timing, travel distance and
                                      opening hours are realistic.

  Personalization relevance           Whether stated preferences
                                      meaningfully affect
                                      recommendations.

  Language quality                    Naturalness and correctness in
                                      English, Hindi and Tamil.

  Speech recognition quality          Accuracy of transcripts across
                                      supported languages and conditions.

  Voice latency                       Time from the end of user speech to
                                      a usable response.

  Reliability                         Error rate, timeout rate and
                                      successful recovery.

  Privacy compliance                  Whether consent and user memory
                                      controls are respected.
  -----------------------------------------------------------------------

Metrics should be measured separately by language and interaction mode.
A good overall score must not hide poor Tamil speech recognition or weak
Hindi itinerary quality.

------------------------------------------------------------------------

## 17. Key Technical Decisions to Preserve

The following decisions are part of the approved product direction:

1.  Voyantra is a general-purpose conversational assistant with
    specialized travel intelligence, not an itinerary-only chatbot.
2.  The user does not need to select an intent or feature before
    starting a conversation.
3.  Pondicherry and Chennai are the initial destinations for full travel
    discovery and itinerary functionality.
4.  General information about other Indian and international
    destinations remains allowed.
5.  English, Hindi and Tamil are the only initially supported
    conversation languages.
6.  Automatic language detection is enabled by default, with manual
    language selection.
7.  Language switching must preserve context.
8.  Push-to-Talk is the primary voice mode.
9.  Live Conversation is a secondary, opt-in voice mode.
10. Text, Push-to-Talk and Live Conversation share one conversational
    engine and memory system.
11. Short-term context and optional long-term memory are separate.
12. Long-term memory is user-controlled; sensitive preferences require
    explicit opt-in.
13. Itinerary planning considers user-stated preferences, including age
    groups, group composition, interests, budget, mobility, food and
    religious or cultural requirements.
14. Multiple itinerary alternatives and conversational itinerary editing
    are supported.
15. Travel facts must be grounded in actual data where available, and
    uncertainty must be communicated honestly.

------------------------------------------------------------------------

## 18. Final Product Statement

**Voyantra 2.0 is a multilingual, voice-enabled conversational AI that
combines natural general-purpose assistance with personalized travel
intelligence.**

It allows people to communicate in English, Hindi or Tamil through text,
primary Push-to-Talk voice interaction or optional Live Conversation. It
remembers the current conversation, can retain user-approved preferences
across sessions, discovers travel information for Pondicherry and
Chennai, and generates adaptable itineraries based on the needs of
individuals, families and groups.

Its defining principle is simple:

**Understand the person, understand the journey, and then recommend the
right experience.**

This specification records the approved functional direction.
Implementation details, provider choices, endpoint names and database
changes must be verified against the existing Voyantra repository before
code changes are made.
