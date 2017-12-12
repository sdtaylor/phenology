from pyPhenology import utils, models
import pytest

doy, temp = utils.load_test_data(name='vaccinium')

model_list={'Uniforc': models.Uniforc,
            'Unichill': models.Unichill,
            'Thermal_Time':models.Thermal_Time}

for model_name, Model in model_list.items():
    #Test with no fixed parameters
    print(model_name + ' - Estimate all parameters')
    model=Model()
    model.fit(DOY=doy, temperature=temp, verbose=True)
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
    model.fit(DOY=doy, temperature=temp, verbose=True)
    model.predict(doy, temp)
    assert model.get_params()[param]==value, 'Fixed parameter does not equal final one: '+str(param)

    # Estimate only a single parameter
    print(model_name + ' - Estimate a single parameter')
    # all_parameters is now minus one due to popitem()
    model = Model(parameters=all_parameters)
    model.fit(DOY=doy, temperature=temp, verbose=True)
    model.predict(doy, temp)
    for param, value in all_parameters.items():
        assert model.get_params()[param] == value, 'Fixed parameter does not equal final one: '+str(param)
    
    # Expect error when a bogus parameter gets passed
    print(model_name + ' - Should not accept unknown parameters')
    with pytest.raises(AssertionError) as a:
        model = Model(parameters={'not_a_parameter':0})

# Make sure some known parameters are estimated correctly
#fixed_gdd_model = models.Thermal_Time(parameters={'t1':0, 'T':0})
#fixed_gdd_model.fit(DOY=doy, temperature=temp, verbose=True)
