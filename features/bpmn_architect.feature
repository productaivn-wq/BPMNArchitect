Feature: BPMNArchitect Governed Ring-3 Capability Contract
  As an Agentic OS orchestrator
  I want BPMNArchitect to execute deterministically under UTOP governance
  So that nominal domain workflows pass and adversarial boundary violations fail closed

  Scenario: Nominal BPMNArchitect capability execution
    Given SKILL.md and utop_state.json are present for BPMNArchitect
    When a valid domain payload invokes bpmn_architect_engine.py
    Then deterministic structured output is returned with verdict PASS

  Scenario: Fail-closed rejection on Ring-0 or schema boundary violation
    Given BPMNArchitect operates strictly inside RING_3_AGENT
    When an invalid schema or Ring-0 traversal target is supplied
    Then execution halts fail-closed with verdict REJECT
