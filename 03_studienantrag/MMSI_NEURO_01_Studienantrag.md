# ==============================================================================
# MMSI v3.5 // STUDIENANTRAG MMSI-NEURO-01
# Titel: Empirische Quantifizierung des kognitiven Phasenraum-Kollapses (d_alpha)
#        und der Nicht-Markovschen Gedächtnis-Viskosität (K) mittels kombinierter
#        High-Density EEG- und Real-Time fMRT-Messung
# Ziel-Institution: Neurozentrum der Albert-Ludwigs-Universität Freiburg
# Prüfarzt: Patrick Frank Buckreus
# Kooperation: Department Radiologie – Medizinische Physik (MRDAC) /
#              Freiburg Brain Imaging (FBI)
# ==============================================================================

## 1. Wissenschaftliche Hintergrundbegründung & Hypothesen

Bisherige neurowissenschaftliche Paradigmen erfassen kognitive Zustände primär über lokal isolierte BOLD-Signal-Veränderungen oder frequenzspezifische Leistungsdichten. Das mathematische Modell der **Metaphysischen Systemtheorie (MMSI v3.5)** erweitert diesen Ansatz um eine topologische Zustandsraum-Geometrie.

### Haupt-Hypothese H1 (Dimensionskollaps)
Der Übergang von zersplitterter kognitiver Verarbeitung (T_V) in fokussierte Gegenwartspräsenz (T_S) korreliert invers mit der effektiven Raumdimension d_α(t) der räumlichen Kovarianzmatrix. Bei Erreichen der P_S-Singularität sinkt d_α(t) unter den Schwellenwert von 1,32.

### Haupt-Hypothese H2 (Nicht-Markovsche Gedächtnis-Dynamik)
Die Verweildauer in traumatisierenden/repetitiven kognitiven Schleifen lässt sich als Abweichung von der Markov-Approximation über den Hurst-Exponenten (H > 0,50) des BOLD- und EEG-Autokorrelations-Kernels K(t−t') quantifizieren.

### Haupt-Hypothese H3 (Null-Last-Entkopplung)
Im Seinsmodus T_S bleibt die neuronale Task-Aktivität A(t) konstant, während das subjektive Belastungssignal W(t) → 0 konvergiert.

## 2. Studiendesign & Methodik

- **Studiendesign:** Prospektive, monozentrische Validierungs- und Beobachtungsstudie
- **Stichprobengröße:** N = 30 Probanden
  - 15 gesunde Kontrollen
  - 15 Patienten mit Posttraumatischer Belastungsstörung (PTBS)
- **Studienort:** Neurozentrum Freiburg, MRDAC / FBI

### Experimentelles Protokoll (3.0 Tesla High-Field MRI)

1. **Mess-Sequenz 1 (rs-fMRT / 10 Min):** BOLD-Sequenz (TR = 1200 ms, Multi-Band Acceleration Factor 4) zur Bestimmung des Basal-Kernels K(t−t') im Default Mode Network (DMN).

2. **Mess-Sequenz 2 (HD-EEG im Scanner / 15 Min):** Simultanes 64-Kanal EEG zur Phasen-Amplituden-Kopplung (θ-Phase vs. γ-Amplitude) unter gezieltem P_S-Triggering (Gegenwartsprojektion).

3. **Mess-Sequenz 3 (rt-fMRT Closed-Loop / 15 Min):** Real-time Rückkopplung der berechneten Dimension d_α(t) an den Probanden über visuelle Feedback-Stimulation.

## 3. Ethische Verträglichkeit & Risikobewertung

- **Risikoklasse:** Nicht-invasives neurophysiologisches Screening
  - Keine Kontrastmittel
  - Keine ionisierende Strahlung
- **Datenschutz:** Pseudonymisierung aller DICOM- und EDF-Datensätze nach DSGVO und BIDS-Standard vor Übergabe an die MMSI-Analyse-Pipeline
- **Probandenschutz:** Abbruchkriterium definiert bei Überschreiten der Cache-Sättigung C(t) > Ω_krit = 0,92 (Erfassung via autonomen GSR/Herzfrequenz-Sensoren)

## 4. Erwarteter Erkenntnisgewinn & Klinische Translation

Die Ergebnisse ermöglichen die Entwicklung objektivierbarer Neuromarker für Burnout, PTBS und Aufmerksamkeitsstörungen. Das entwickelte Real-Time LSL-System kann als biologische Steuerungseinheit für closed-loop Neurofeedback-Systeme am Neurozentrum Freiburg direkt eingesetzt werden.
