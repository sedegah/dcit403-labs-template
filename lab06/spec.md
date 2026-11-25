# Prometheus System Specification: Asempa Community Clinic Assistant

## 1. System goal
Provide patients with accurate information about the Asempa Community Clinic and
route urgent cases to the right place, without diagnosing or prescribing.

## 2. Goal hierarchy
- G0 Provide clinic information and safe routing
  - G1 Provide opening hours
    - G1.1 Provide OPD hours
    - G1.2 Provide laboratory hours
    - G1.3 Provide pharmacy hours
  - G2 Provide service information
    - G2.1 List services offered
    - G2.2 List services not offered
  - G3 Provide test preparation instructions
  - G4 Provide payment and NHIS information
  - G5 Handle appointment requests
  - G6 Handle emergencies (redirect)

## 3. Scenarios
- S1 Patient asks "What are the opening hours?" -> G1, answer with OPD/lab/pharmacy hours.
- S2 Patient asks "Are you open on Sunday?" -> G1, answer Sunday hours (OPD and lab closed, pharmacy 10-2).
- S3 Patient asks about a fasting blood sugar test -> G3, give fasting instructions.
- S4 Patient asks if card payment is accepted -> G4, answer no, cash and mobile money only.
- S5 Patient mentions chest pain, difficulty breathing or severe bleeding -> G6, redirect to nearest hospital emergency unit or call 112.
- S6 Patient asks for a service the clinic does not provide (surgery, X-ray) -> G2.2, state not provided and refer.

## 4. Percepts mapped to tools
| Percept (user input) | Tool |
|---|---|
| Question about opening hours | get_opening_hours(service, day) |
| Question about a service | get_service_info(service) |
| Question about test preparation | get_test_prep(test_name) |
| Question about payment / NHIS | get_payment_info() |
| Mention of emergency symptoms | detect_emergency(text) |

## 5. Actions mapped to tool calls
| Action | Tool call |
|---|---|
| Answer with hours | get_opening_hours(...) |
| Answer with service info | get_service_info(...) |
| Answer with test prep | get_test_prep(...) |
| Answer with payment info | get_payment_info() |
| Redirect to emergency | detect_emergency(...) then respond with redirect text |

## 6. Agent descriptors
- ClinicInfoAgent: goals G1-G4, percepts hours/service/prep/payment, actions answer_*.
- TriageAgent: goal G6, percept emergency symptoms, action redirect.

## 7. Data
Clinic information lives in lab05/docs/*.md (opening_hours, services, nhis, lab_test_preparation, appointments_and_visits).
