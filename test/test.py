from pyPhenology import utils, models
from pyPhenology.models import validation
import pytest

doy, temp = utils.load_test_data()

model_list={'Uniforc': models.Uniforc,
            'Unichill': models.Unichill,
            'Thermal_Time':models.Thermal_Time,
            'Alternating':models.Alternating}

# Allow for quick fitting in testing. 
testing_optim_params = {'maxiter':5, 'popsize':10, 'disp':True}

for model_name, Model in model_list.items():
    print(model_name + ' - Initial validaiton')
    validation.validate_model(Model())
        
    #Test with no fixed parameters
    print(model_name + ' - Estimate all parameters')
    model=Model()
    model.fit(DOY=doy, temperature=temp, verbose=True, optimizer_params=testing_optim_params)
    model.predict(doy, temp)

    # Use estimated parameter values in other tests
    all_parameters = model.get_params()
    
    # Test with all parameters set to a fixed value
    print(model_name + ' - Fix all parameters')
    model = Model(parameters=all_parameters)
    model.predict(doy, temp)
    
    # Only a single parameter set to fixed
    print(model_name + ' - Fix a single parameter')
    param, value = all_parameters.popitem()
    single_param = {param:value}
    model = Model(parameters=single_param)
    model.fit(DOY=doy, temperature=temp, verbose=True, optimizer_params=testing_optim_params)
    model.predict(doy, temp)
    assert model.get_params()[param]==value, 'Fixed parameter does not equal final one: '+str(param)

    # Estimate only a single parameter
    print(model_name + ' - Estimate a single parameter')
    # all_parameters is now minus one due to popitem()
    model = Model(parameters=all_parameters)
    model.fit(DOY=doy, temperature=temp, verbose=True, optimizer_params=testing_optim_params)
    model.predict(doy, temp)
    for param, value in all_parameters.items():
        assert model.get_params()[param] == value, 'Fixed parameter does not equal final one: '+str(param)
    
    # Expect error when predicting but not all parameters were
    # passed, and no fitting has been done.
    print(model_name + ' - Should not predict without fit')
    with pytest.raises(AssertionError) as a:
        model = Model(parameters=single_param)
        model.predict(doy, temp)
    
    # Expect error when a bogus parameter gets passed
    print(model_name + ' - Should not accept unknown parameters')
    with pytest.raises(AssertionError) as a:
        model = Model(parameters={'not_a_parameter':0})

############################################################
# Make sure some known parameters are estimated correctly
# Using the Brute Force method in this way should produce
# the same result every time.
# The number match the estimates from the original model
# codebase in github.com/sdtaylor/phenology_dataset_study
###########################################################
vaccinium_doy, vaccinium_temp = utils.load_test_data(name='vaccinium')

leaves_doy = vaccinium_doy[vaccinium_doy.Phenophase_ID==371]
flowers_doy = vaccinium_doy[vaccinium_doy.Phenophase_ID==501]

fixed_gdd_model = models.Thermal_Time(parameters={'t1':0, 'T':0, 'F':(0,1000)})
fixed_gdd_model.fit(DOY=leaves_doy, temperature=vaccinium_temp, verbose=True,
                    optimizer_params={'Ns':1000, 'disp':True}, method='BF')
assert int(fixed_gdd_model.get_params()['F']) == 273, 'Vaccinium leaves not estimated correctly'

fixed_gdd_model = models.Thermal_Time(parameters={'t1':0, 'T':0, 'F':(0,500)})
fixed_gdd_model.fit(DOY=flowers_doy, temperature=vaccinium_temp, verbose=True,
                    optimizer_params={'Ns':1000, 'disp':True}, method='BF')
assert int(fixed_gdd_model.get_params()['F']) == 447, 'Vaccinium flowers not estimated correctly'
