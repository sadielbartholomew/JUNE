---
layout: default
title: Populating output with realistic household characteristics
has_children: true
nav_order: 4
---

Populating output areas with realistic household characteristics
========
We have populated postcode sectors with households that have realistic age compositions, using the following datasets extracted from Nomis,
- [KS101EW](https://www.nomisweb.co.uk/census/2011/ks101ew), classifies the usual resident population by sex. We use it to extract the number of residents by postcode sector, and the sex composition.
- [KS102EW](https://www.nomisweb.co.uk/census/2011/ks102ew), classifies the usual resident population by age. The age intervals given are:

    + Age 0 to 4

    - Age 5 to 7
    - Age 8 to 9
    - Age 10 to 14
    - Age 15
    - Age 16 to 17
    - Age 18 to 19
    - Age 20 to 24
    - Age 25 to 29
    - Age 30 to 44
    - Age 45 to 59
    - Age 60 to 64
    - Age 65 to 74
    - Age 75 to 84
    - Age 85 to 89
    - Age 90 and over

- [LC1402EW](https://www.nomisweb.co.uk/census/2011/lc1402ew), classifies households by household composition and by number of bedrooms. We use this information to generate realistic households by postcode sector assuming that, i) Families in which all members are over 65's, are composed of couples, ii) Lone parents with one or two bedrooms only have one child, iii) Lone parents with three or more bedrooms only have two children, iv) Families classified as others count as young adults with no children.

Given these datasets we populate all postcode sectors with Person instances by matching the output area observations in terms of sex, age and household composition. See figures below to check results.

<img src="images/overall_ages.png" alt="Kitten"
	title="Total number of residents in given age range" width="400" height="400" align="middle" />

<img src="images/ages_postcodes.png" alt="Kitten"
	title="Distribution of residents per postcode sector per age category" width="400" height="400" align="middle" />

<img src="images/age_dist.png" alt="Kitten"
	title="England and Wales age distribution per postcode. Comparison between census data and distribution after people allocation." width="700" height="700" align="middle" />

## Household distribution model

Given a household configuration, we use the encoding

```python
"n_kids n_students n_adult n_old"
```

where ``n_kids`` is the number of people under 18 years old, ``n_students`` is the number of people between the age of 18 and 24 (without caring if they are really a student or not), ``n_adult`` is the number of people from 18 to 65 years old, and finally ``n_old`` corresponds to +65 years of age. The possible 19 household configurations currently considered are:

- ``"0 0 0 1"`` : One old person

- ``"0 0 0 2"`` : Two old people

- ``"0 0 0 3"`` : Three old people

- ``"0 0 1 0"`` : One adult

- ``"0 0 2 0"`` : Two adults

- ``"1 0 1 0"`` : One adult and one kid

- ``"2 0 1 0"`` : One adult and two kids

- ``"3 0 1 0"`` : One adult and three kids

- ``"1 1 1 0"`` : One adult, one kid, and one student

- ``"2 1 1 0"`` : One adult, two kids, and one student

- ``"1 0 2 0"`` : Two adults and one kid

- ``"2 0 2 0"`` :  Two adults and two kids

- ``"3 0 2 0"`` :  Two adults and three kids

- ``"1 1 2 0"`` : Two adults, one kid, and one student

- ``"2 1 2 0"`` : Two adults, two kids, and one student

- ``"0 3 0 0"`` : Three students

- ``"0 4 0 0"`` : Four students

- ``"0 1 2 0"`` : Two adults and one student

- ``"0 2 2 0"`` : Two adults and two students

  

The algorithm that it is used to allocate pople in houses is found in the ``distributor.py`` module. Given the local population of the output area, the algorithm then initializes a household randomly following the distribution of household configurations from the nomis data, then it tries to fill the given configuration with the pool of people. If the full configuration cannot be achieved (for instance, household configuration is two old people, but we only have one left) then the house is left half empty, and the household configuration is updated to reflect the actual one. That means that new configurations can appear, for instance if there is only one student left, and we create a student household, then the configuration would be ``"0 1 0 0 "`` which was not in the original input.