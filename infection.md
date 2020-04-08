---
layout: default
title: Simulating an individual infection
parent: Infection Modelling
nav_order: 4
---
Our infection model is encoded in the class "Infection" and assumes that any individual infection is described by two potentially time-dependent characeristics, given as numbers, namely

- the probability to transmit the infection, and

- the severity of its symptoms.

They are realised by two classes, "Transmission" and "Symptoms", and their results are called in the methods "transmission_probability(time)" and "symptom_severity(time)".

We have currently implemented different realisations for both, listed in <html link> and <html link>.

The model characteristics and their parameters are set in the "Infection_Selector" and may vary for each individual -- the logic is that each individual has their individual infection, composed of a transmission probability and symptoms from a pre-selected class and defined by a set of potentially varying parameters.  The variation of parameters can be made person-specific.  There are two modes to vary parameters and produce the actual value (tag "Value") to be given to the infection, namely:

- a (possibly asymmetric) Gaussian distribution ("Mode" = "Gauss")around a mean (tag "Mean") with positive and negative widths ("WidthPlus" and "WidthMinus", the latter be set to "WidthPlus" if it is not given) and lower and upper limits ("Lower" and "Upper"), and

- a gamma-distribution ("Mode" = "Gamma") given by a mean and a shape parameter ("Mean" and "Shape").








