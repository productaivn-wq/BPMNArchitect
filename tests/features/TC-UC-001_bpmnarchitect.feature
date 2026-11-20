# Auto-generated Gherkin feature for BPMNArchitect — UC-001: 1. Overview & Generic Design Principles
# UC Reference: UC-001
# Generated: 2026-08-27

@skill @bpmnarchitect @uc-001
Feature: BPMNArchitect — 1. Overview & Generic Design Principles
  As a user of the Antigravity platform
  I want to use the BPMNArchitect skill for '1. Overview & Generic Design Principles'
  So that I can generic bpmn 2.0 business process modeling, auditing, and visualization skill. models, validates, and renders formal bpmn 2.0 activity diagrams (plantuml .puml) and interactive mermaid.js viewers (.ht

  Background:
    Given the Antigravity platform is running
    And the "BPMNArchitect" skill is registered and available


  @TC-UC-001-S01 @happy-path
  Scenario: Happy Path - 1. Overview & Generic Design Principles
    Given the "BPMNArchitect" skill is initialized
    And the system has valid configuration
    When Generic & Reusable: BPMNArchitect contains instructions for process modeling in general. Systemspecific process specifications (such as the Universal Working Harness 37step model) live in project context directories (docs/diagrams/UNIVERSAL_WORKING_HARNESS_BPMN_SPEC.md).
    And PlantUML & Mermaid Native: OMG BPMN XML and bpmnjs are deprecated. All process models MUST be rendered using PlantUML Activity Diagrams (.puml) and Interactive Mermaid.js HTML Viewers (.html).
    And Start Event Flexibility: A valid process MUST have at least one Start Event ($\ge 1$). Multiple Start Events with distinct triggers (Message, Timer, Signal, None) are explicitly allowed.
    Then the system completes '1. Overview & Generic Design Principles' successfully

  @TC-UC-001-S02 @error-handling
  Scenario: Alternate Flow - Invalid Input — System validates inputs and returns a structured error with field-level guidance. Gherkin: `@TC-UC-001-S02`
    Given the "BPMNArchitect" skill is initialized
    When the user triggers alternate flow "Invalid Input — System validates inputs and returns a structured error with field-level guidance. Gherkin: `@TC-UC-001-S02`"
    Then the system handles the scenario correctly

  @TC-UC-001-S03 @error-handling
  Scenario: Alternate Flow - Dependency Unavailable — System retries up to 3 times with exponential backoff, then falls back. Gherkin: `@TC-UC-001-S03`
    Given the "BPMNArchitect" skill is initialized
    When the user triggers alternate flow "Dependency Unavailable — System retries up to 3 times with exponential backoff, then falls back. Gherkin: `@TC-UC-001-S03`"
    Then the system handles the scenario correctly

  @TC-UC-001-S04 @error-handling
  Scenario: Alternate Flow - Timeout — System terminates execution after configured timeout and reports partial results. Gherkin: `@TC-UC-001-S04`
    Given the "BPMNArchitect" skill is initialized
    When the user triggers alternate flow "Timeout — System terminates execution after configured timeout and reports partial results. Gherkin: `@TC-UC-001-S04`"
    Then the system handles the scenario correctly

  @TC-UC-001-ERR01
  Scenario: Graceful degradation on dependency failure during 1. Overview & Generic Design Principles
    Given the "BPMNArchitect" skill is initialized
    And a required dependency is unavailable
    When the user invokes the skill for '1. Overview & Generic Design Principles'
    Then the system attempts a fallback mechanism
    And reports the degradation to the caller
