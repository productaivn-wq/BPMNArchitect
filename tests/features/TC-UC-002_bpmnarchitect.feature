# Auto-generated Gherkin feature for BPMNArchitect — UC-002: 2. Standard Taxonomy & Rules
# UC Reference: UC-002
# Generated: 2026-08-27

@skill @bpmnarchitect @uc-002
Feature: BPMNArchitect — 2. Standard Taxonomy & Rules
  As a user of the Antigravity platform
  I want to use the BPMNArchitect skill for '2. Standard Taxonomy & Rules'
  So that I can generic bpmn 2.0 business process modeling, auditing, and visualization skill. models, validates, and renders formal bpmn 2.0 activity diagrams (plantuml .puml) and interactive mermaid.js viewers (.ht

  Background:
    Given the Antigravity platform is running
    And the "BPMNArchitect" skill is registered and available


  @TC-UC-002-S01 @happy-path
  Scenario: Happy Path - 2. Standard Taxonomy & Rules
    Given the "BPMNArchitect" skill is initialized
    And the system has valid configuration
    When STxxx (Happy Path Steps): ST001, ST002, ... ST037 (Sequential 3digit zeropadded IDs).
    And EXxxx (Unhappy Exception Branches): EX001 to EX007 (Autoheal recovery loops & escalations).
    And GWxxx (Decision Gateways): GW001 to GW004 (Conditional decision gateways).
    And RFxxx (Reflection Circles): RF001 (30s micro), RF002 (1m meso), RF003 (3m macro).
    And 🔵 [CORE] Universal Path (#0f172a container / #38bdf8 border): Baseline path followed by all work types (General Vibe Working, Research, Documents, Ops, Strategy, and Harness Nodes).
    And 🟣 [CODE] Technical Vibe Coding (#3b0764 container / #c084fc border): Deep engineering subtask hops for Vibe Coding (AST 3Way Merges, DB Schema Migrations, SAST Scans, FastForward Git PR Merges, Infrastructure Deploy).
    And 🔴 [EX] Exception AutoHeal (#450a0a container / #ef4444 border): Unhappy exception recovery loops (EX001 to EX007).
    And 🟠 [GW] Decision & Quality Gateways (#fb923c border): Gateways and 4tier Quality Gates (GW001 to GW004).
    And Subtask Quality Gate (ST018 / RF001): Microtimebox sandbox quality validation (2m subtask level).
    And Task Quality Gate (GW003 / ST025 / RF002): Mesotimebox staging quality validation ($\text{EAI} \ge 0.98$).
    Then the system completes '2. Standard Taxonomy & Rules' successfully

  @TC-UC-002-S02 @error-handling
  Scenario: Alternate Flow - Invalid Input — System validates inputs and returns a structured error with field-level guidance. Gherkin: `@TC-UC-002-S02`
    Given the "BPMNArchitect" skill is initialized
    When the user triggers alternate flow "Invalid Input — System validates inputs and returns a structured error with field-level guidance. Gherkin: `@TC-UC-002-S02`"
    Then the system handles the scenario correctly

  @TC-UC-002-S03 @error-handling
  Scenario: Alternate Flow - Dependency Unavailable — System retries up to 3 times with exponential backoff, then falls back. Gherkin: `@TC-UC-002-S03`
    Given the "BPMNArchitect" skill is initialized
    When the user triggers alternate flow "Dependency Unavailable — System retries up to 3 times with exponential backoff, then falls back. Gherkin: `@TC-UC-002-S03`"
    Then the system handles the scenario correctly

  @TC-UC-002-S04 @error-handling
  Scenario: Alternate Flow - Timeout — System terminates execution after configured timeout and reports partial results. Gherkin: `@TC-UC-002-S04`
    Given the "BPMNArchitect" skill is initialized
    When the user triggers alternate flow "Timeout — System terminates execution after configured timeout and reports partial results. Gherkin: `@TC-UC-002-S04`"
    Then the system handles the scenario correctly

  @TC-UC-002-ERR01
  Scenario: Graceful degradation on dependency failure during 2. Standard Taxonomy & Rules
    Given the "BPMNArchitect" skill is initialized
    And a required dependency is unavailable
    When the user invokes the skill for '2. Standard Taxonomy & Rules'
    Then the system attempts a fallback mechanism
    And reports the degradation to the caller
