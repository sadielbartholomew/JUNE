import numpy as np
from june.demography import Person
from june.infection.health_index import HealthIndexGenerator

def test__smaller_than_one():
    index_list=HealthIndexGenerator.from_file()
    increasing_count=0
    for i in range(len(index_list.prob_lists[0])):
        index_m=index_list(Person.from_attributes(age=i,sex='m'))
        index_w=index_list(Person.from_attributes(age=i,sex='f'))
        bool_m=np.sum(np.round(index_m,7)<=1)
        bool_w=np.sum(np.round(index_w,7)<=1)
        if bool_m+bool_w==14:
           increasing_count+=1
        else:
           increasing_count==increasing_count
    assert increasing_count ==121


def test__No_negative_probability():
  probability_object=HealthIndexGenerator.from_file()
  probability_list=probability_object.prob_lists
  negatives=0.0
  for i in range(len(probability_list[0])):
       negatives+=sum(probability_list[0][i]<0)
       negatives+=sum(probability_list[1][i]<0)
  assert negatives==0

def test__growing_index():
    index_list=HealthIndexGenerator.from_file()
    increasing_count=0
    for i in range(len(index_list.prob_lists[0])):
        index_m=index_list(Person.from_attributes(age=i,sex='m'))
        index_w=index_list(Person.from_attributes(age=i,sex='f'))
        
        if sum(np.sort(index_w)==index_w)!=len(index_w):
            increasing_count+=0


        if sum(np.sort(index_m)==index_m)!=len(index_m):
            increasing_count+=0

    assert increasing_count ==0

def test__asymptomatic_ratio():
    health_index=HealthIndexGenerator.from_file(asymptomatic_ratio=0.43)
    baseline_index=health_index(Person.from_attributes(age=80,sex='m'))
    print(baseline_index)
    new_health_index=HealthIndexGenerator.from_file(asymptomatic_ratio=0.2)
    index=new_health_index(Person.from_attributes(age=80,sex='m'))

    assert index[0] == 0.2

    print(index)
    print(np.diff(index))
    print(np.diff(baseline_index)*1.43/1.2)
    assert np.testing.assert_allclose(np.diff(index), np.diff(baseline_index)*1.43/1.2)
    assert 1-index[-1] == 1-baseline_index[-1]*1.43/1.2

