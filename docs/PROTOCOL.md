# Voice Trainer — Deterministic Session Protocol

## Status

This document defines the target deterministic training protocol. As of v0.1.0, the full controller/state machine described here is **not yet implemented**.

When code and this document disagree, treat the mismatch as implementation work rather than silently redefining the protocol in prompt text.

## Design principle

The language model may propose what should happen next, but the controller owns whether that action is valid and whether the session changes phase.

Prompt instructions are not sufficient enforcement for session invariants.

## Canonical phases

The intended phase model is:

```text
prepare
  ↓
scene
  ↓
wait_user
  ↘ reflect ↘
   ↖ replay  ↙
      ↓
    debrief
      ↓
      end
```

A concrete implementation may use enums or sub-states, but must preserve the semantic ownership below.

### `prepare`

Purpose: establish the session goal, scenario/context references, requirements and initial conditions.

The controller validates that required setup exists before entering the active scene.

### `scene`

Purpose: produce or continue the simulated interaction.

The model can generate partner/scene content, but cannot unilaterally mark training requirements complete or end the session.

### `wait_user`

Purpose: wait for the user's real response.

Silence, interruption and delayed response should be represented deliberately rather than treated as an implicit model turn.

### `reflect`

Purpose: brief structured reflection on the user's response or internal reaction.

Reflection is bounded by controller-owned limits. The model cannot extend reflection indefinitely by repeatedly asking another reflective question.

### `replay`

Purpose: retry or replay a specific moment using approved/stored source material.

Exact replay requires an explicit stored source/text reference. The model must not claim an exact replay when it is reconstructing from memory or inventing content.

### `debrief`

Purpose: summarize the completed session, observations and next useful training focus.

Entry is blocked while mandatory session requirements remain incomplete unless the user explicitly ends the session.

### `end`

Terminal phase for the session.

The user must always be able to end manually. The model must not directly transition the controller to `end` merely by generating language such as “we are done”.

## Proposed-action contract

The controller should eventually consume structured proposed actions rather than infer state transitions from free-form assistant text.

Conceptually:

```text
ProposedAction
- kind
- payload
- source
- optional reason
```

Examples of `kind`:
- `continue_scene`
- `wait_for_user`
- `request_reflection`
- `request_replay`
- `complete_requirement`
- `request_debrief`
- `request_end`

The exact schema belongs in code once implemented. Validation rules belong in the controller/domain layer, not only in prompts.

## Core invariants

The implementation must preserve at least these invariants:

1. **Model cannot end directly.** A model proposal may request an end/debrief, but the controller decides.
2. **Manual user end always works.** User cancellation/end bypasses normal requirement completion gates.
3. **Incomplete required stages block normal debrief.** The controller, not the model, owns requirement completion.
4. **Reflection limits are controller-owned.** Repeated model requests cannot exceed the configured/session limit.
5. **Exact replay requires stored source/text.** Otherwise replay must be labeled as reconstruction/rephrasing, not exact replay.
6. **Transitions are explicit.** Free-form text must not mutate phase by implication.
7. **State changes are auditable.** The controller should make it possible to inspect why a transition was accepted or rejected.
8. **Personal memory is not silently expanded.** Protocol execution must not create unrestricted transcript/history persistence as a side effect.

## Requirements and counters

A session may define controller-owned requirements such as:
- number of active attempts;
- whether a reflection occurred;
- whether replay is required/optional;
- whether a specific skill was practiced;
- maximum reflection count;
- session duration or phase limits.

The model may report evidence, but only validated controller logic updates authoritative counters/requirements.

## Silence and interruption

Voice of Luna owns generic barge-in and transport behavior. Voice Trainer owns the training meaning of waiting and silence.

The protocol should support patient waiting without automatically filling silence with extra model speech. Interruption should cancel or suspend output through the host's generic mechanisms while preserving a coherent trainer state.

No training-specific audio transport logic should be implemented here if the generic host capability already exists.

## Debrief boundary

Debrief is a product artifact, not merely the final assistant paragraph.

A future implementation should distinguish:
- deterministic session facts/counters;
- user-approved or explicit observations;
- model interpretation/synthesis;
- any proposed durable observation to be stored externally.

This prevents model-generated interpretation from being mistaken for controller-verified fact.

## Error handling

Invalid proposed actions should be rejected deterministically and leave the session in a valid state. The adapter may return corrective prompt context to the model, but must not repair invariants by silently mutating unrelated state.

## Testing expectations

At minimum, controller tests should cover:
- valid happy-path phase flow;
- invalid phase transitions;
- direct model end rejection;
- manual user end acceptance from every active phase;
- unfinished requirement debrief blocking;
- reflection-limit enforcement;
- replay-without-source rejection;
- exact replay with valid stored source;
- deterministic behavior for identical state + action;
- persistence/serialization round trips once state serialization exists.

## Change rule

Changes to phase semantics or core invariants are architectural changes. Update this document, tests and `CHANGELOG.md` together; do not change them only through prompts or UI labels.
