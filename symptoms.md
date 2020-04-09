---
layout: default
title: Symptoms
parent: Simulating an individual infection
mathjax: true
nav_order: 6
---

# Symptoms

1. SymptomsGauss
We have currently only one class of symptoms, a Gaussian distribution with time of symptom severity, given by their maximal severity S_max, "Symptoms:MaximalSeverity", the mean time \bar{t} when the symptoms reach their maximal severity ("Symptoms:MeanTime"), and the width of the distribution ("Symptoms:SigmaTime"), $$\sigma_t$$,

$$ S(t) = Smax * exp[-(t-\bar{t})^2/\sigma^2_t]$$

