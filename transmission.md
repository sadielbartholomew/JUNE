---
layout: default
title: Transmission Probability
parent: Simulating an individual infection
nav_order: 5
---
1. TransmissionSI
This model reproduces the assumptions of the SI model, namely that upon infection people will continue to infect others with a probability given by "Transmission:Probability".  There is no intrinsic cut-off or modulation to that model.

2. TransmissionSIR
This model reproduces the assumptions of the SIR model - upon infection people will continue to infect othe people until they recover, again with a probability given by "Transmission:Probability".  Recovery is encoded probabilistically in this model. In every time-step after infection every infected person has a chance to recover given by "Transmission:Recovery".  We have also included a variant where recovery happens after a fixed given time, "Transmission:RecoverCutoff".

3. TransmissionConstantInterval
In this model the transmission probability is fixed to a constant value ("Transmission:Probability") for a fixed time interval after infection ("Transmission:EndTime") - the person however will not necessarily be recovered after this interval is over.  This is different to the fixed-time implementation of the SIR model.

4. TransmissionXNExp
In this model the transmission probability varies with time according to a function given by
$P(t) = P_0 * t^n * exp(-t/alpha)$ with P_0 given by "Transmission:Probability", n given by "Transmission:Exponent", and alpha given by "Transmission:Norm".  Again, recovery is not encoded in this model.
