---
layout: default
title: Quick summary of Imperial transmission model
nav_order: 9
mathjax: true
has_children: false
---

# Quick summary of Imperial transmission model

The model is a stochastic individual based simulation with spatial structure. Individuals belong to a household and a place (school or work). Individuals are assigned to places to reflect the census data. The model itself is described in some detail in reference [1] and has been adapted to the current pandemic in [2].

Each susceptible individual $$i$$ has a probability $$P_{i} = 1 - \exp{(-\lambda_{i}\Delta T)}$$ of being infected at each timestep $$\Delta T = 0.25$$ days, where $$\lambda_{i}$$ is the instantaneous infection risk [1]. $$\lambda_{i}$$ contains the information about the interactions occurring in different groups and is split up into three terms. [2] claims that approximately one third of transmissions occurs in  the household, one third in schools and workplaces, and one third in the community.

\begin{align}
\lambda_{i} &= \lambda_{i, \text{home}} + \lambda_{i, \text{place}} + \lambda_{i, \text{community}} \\\\ \lambda_{i, \text{home}} &= \sum_{k} \dfrac{I_{k}\beta_{h}\kappa{(t-\tau_{k})}\rho_{k}\left[1+C_{k}(\omega - 1)\right]}{n_{i}^{\alpha}} \\\\ \lambda_{i, \text{place}} &= \sum_{k} \dfrac{I_{k}\beta_{p}\kappa{(t-\tau_{k})}\rho_{k}\left[1+C_{k}(\omega \psi_{p}(t-\tau_{k})-1)\right]}{m_{i, \text{place}}} \\\\ \lambda_{i, \text{community}} &= \sum_{k} \dfrac{I_{k}\xi{(a_{i})}\beta_{c}\kappa{(t-\tau_{k})}\rho_{k}f(d_{i,k})\left[1+C_{k}(\omega - 1)\right]}{\sum_{k}f(d_{i,k})}
\end{align}

Brief descriptions of each term:
* $$I_{k} = 1$$ if individual $$k$$ is infectious, 0 otherwise
* $$\beta_{h, p, c}$$ are the transmission coefficients for household, place, and community respectively
* $$\tau_{k}$$ is the time that individual $$k$$ became infectious
* $$\kappa(t-\tau_{k})$$ is a lognormal time profile of the infectiousness
* $$\rho_{k}$$ is the relative infectiousness of individual $$k$$, sampled from gamma distribution
* $$C_{i} = 1$$ if individual $$i$$ is severely infected, 0 otherwise (50% of infections are assumed to be severe [1])
* $$n_{i}^{\alpha}$$ and $$m_{i, j}$$ are the number of people in households and number of people in places (j indexes schools or work), $$\alpha$$ scales transmission rates depending on housesize ($$\alpha = 0.8$$ in [1])
* $$\omega$$ is the infectiousness of a severe infection relative to a mild one (assumed to be $$\omega=2$$ in [1])
* $$\psi_{p}(t)$$ accounts for the time they take away from work if they are severely infected (hard coded in [1])
* $$f(d_{i,k}) \sim 1/\left[1+(d/a)^{b}\right]$$ (a=4km and b=3.8 in [1]) is like a "gravity model" modelling the strength of random interactions out in the community, where $$d_{i,k}$$ is the distance between individuals $$i$$ and $$k$$.
* $$\xi{(a_{i})}$$ is the relative travel related contact rate of an individual of age $$a_{i}$$ ([1] says this makes little difference if set constant to 1)

## In English...

In words, for each individual $$i$$ loop over infectious individuals $$k$$ and sum up all the probabilities which depend on the described factors above. If $$k$$ is severely infected then the transmission probability roughly doubles. An individual $$k$$ has an individual infectiousness sampled from a gamma distribution with mean 1 and shape 0.25 [2] (this is quite ambiguous but I think it means a gamma distribution peaked at 1 c.f. Fig SI8b in [3]), this individual's infectiousness profile (not related to relative infectiousness) evolves over time according to a log-normal distribution.

They assume an incubation period of 5.1 days and infectiousness occurs 12 hours before the onset of symptoms. The infectiousness profile ($$\kappa$$) is tuned to give a mean generation time (time to pass on the infection) of 6.48 days with a standard deviation of 3.83 days [4].

My speculation as to how they arrive at different transmission coefficients $$\beta$$ is that given an $$R_{0}$$ value obtained from data, they divide $$R_{0}$$ by 3 (since roughly 1/3 chance to transmit in each of their defined groups) and then fit the $$\beta_{\text{house}}$$ using Bayesian methods with household data to try and recover this $$R_{0}/3$$ (section 3 in [1]). The other two $$\beta_{p, c}$$ are then tuned to match $$R_{0}/3$$ as well.

Symptomatic individuals are assumed to be 50% more infectious than asymptomatic individuals, but they don't seem to mention the proportions.


## References

[1. Strategies for containing an emerging influenza pandemic in
SE Asia.](https://static-content.springer.com/esm/art%3A10.1038%2Fnature04017/MediaObjects/41586_2005_BFnature04017_MOESM1_ESM.pdf)

[2. Impact of non-pharmaceutical interventions (NPIs) to reduce COVID19 mortality and healthcare demand](https://www.imperial.ac.uk/media/imperial-college/medicine/sph/ide/gida-fellowships/Imperial-College-COVID19-NPI-modelling-16-03-2020.pdf)

[3. Strategies for mitigating an influenza pandemic.](https://static-content.springer.com/esm/art%3A10.1038%2Fnature04795/MediaObjects/41586_2006_BFnature04795_MOESM28_ESM.pdf)

[4. The Global Impact of COVID-19 and Strategies for Mitigation and
Suppression](https://www.imperial.ac.uk/media/imperial-college/medicine/mrc-gida/2020-03-24-COVID19-Report-11.pdf)

