from pyPhenology import utils
import pytest
import numpy as np

obs, predictors = utils.load_test_data()

core_model_names = ['Uniforc','Unichill','ThermalTime','Alternating','MSB',
                    'Linear','Sequential','M1','Naive','FallCooling']

# Setup a list of (model_name, fitted_model object)
fitted_models = [utils.load_model(model_name)() for model_name in core_model_names]
[model.fit(obs, predictors, optimizer_params='testing') for model in fitted_models]

model_test_cases = list(zip(core_model_names, fitted_models))

#########################################################

@pytest.mark.parametrize('model_name, fitted_model', model_test_cases)
def test_predict_output_length(model_name, fitted_model):
    """Predict output length should equal input length"""
    
    assert len(fitted_model.predict()) == len(obs)

@pytest.mark.parametrize('model_name, fitted_model', model_test_cases)
def test_predict_output_length2(model_name, fitted_model):
    """Predict output length should equal input length
    
    Use a subset because some re-arranging goes on internally
    """
    predicted = fitted_model.predict(to_predict=obs[1:10], predictors=predictors)
    assert len(predicted) == len(obs[1:10])

@pytest.mark.parametrize('model_name, fitted_model', model_test_cases)
def test_predict_output_shape(model_name, fitted_model):
    """Predict output shape should be 1D"""
    assert len(fitted_model.predict().shape) == 1

@pytest.mark.parametrize('model_name, fitted_model', model_test_cases)
def test_score(model_name, fitted_model):
    """Score should return a single number"""
    assert isinstance(fitted_model.score(), float)

@pytest.mark.parametrize('model_name, fitted_model', model_test_cases)
def test_score_with_new_data(model_name, fitted_model):
    """Score should return a single number using a new prediction set"""
    assert isinstance(fitted_model.score(doy_observed = obs.doy.values[1:10],
                                         to_predict = obs[1:10],
                                         predictors = predictors), float)

@pytest.mark.parametrize('model_name, fitted_model', model_test_cases)
def test_do_not_score_with_non_numpy_observed_values(model_name, fitted_model):
    """doy_observed argument should only be a numpy array"""
    with pytest.raises(TypeError):
        fitted_model.score(doy_observed = list(obs.doy.values[1:10]),
                                         to_predict = obs[1:10],
                                         predictors = predictors)

@pytest.mark.parametrize('model_name, fitted_model', model_test_cases)
def test_brute_force(model_name, fitted_model):
    """Test brute force optimization"""
    
    new_model = utils.load_model(model_name)()
    new_model.fit(obs, predictors, method='BF', optimizer_params='testing')
    assert len(new_model.predict()) == len(obs)

@pytest.mark.parametrize('model_name, fitted_model', model_test_cases)
def test_predict_with_new_data_1(model_name, fitted_model):
    """Do not predict new data with only observations"""
    with pytest.raises(TypeError):
        fitted_model.predict(to_predict = obs)

@pytest.mark.parametrize('model_name, fitted_model', model_test_cases)
def test_predict_with_new_data_2(model_name, fitted_model):
    """Do not predict new data with only predictors"""
    with pytest.raises(TypeError):
        fitted_model.predict(predictors=predictors)

@pytest.mark.parametrize('model_name, fitted_model', model_test_cases)
def test_save_and_load_model_universal_loader(model_name, fitted_model):
    """Load a saved model via utils.load_saved_model"""
    
    fitted_model.save_params('model_params.json', overwrite=True)
    loaded_model = utils.load_saved_model('model_params.json')
    assert fitted_model.get_params() == loaded_model.get_params()
    
@pytest.mark.parametrize('model_name, fitted_model', model_test_cases)
def test_save_and_load_model(model_name, fitted_model):
    """Load a saved model by passing file as parameters arg"""

    fitted_model.save_params('model_params.json', overwrite=True)
    loaded_model = utils.load_model(model_name)(parameters='model_params.json')
    assert fitted_model.get_params() == loaded_model.get_params()

@pytest.mark.parametrize('model_name, fitted_model', model_test_cases)
def test_all_parameters_fixed_fit(model_name, fitted_model):
    """Do not attempt to fit a model when all passed parameters are fixed"""
    all_parameters = fitted_model.get_params()
    new_model = utils.load_model(model_name)(parameters=all_parameters)
    with pytest.raises(RuntimeError):
        new_model.fit(obs, predictors, optimizer_params='testing', debug=True)
        
@pytest.mark.parametrize('model_name, fitted_model', model_test_cases)
def test_all_parameters_fixed_predict_no_new_data(model_name, fitted_model):
    """Do not predict, sans new data, when all passed parameters were fixed.
    
    This only works when the model object had fit run, and predictions
    can be from the fitted data.
    """    
    all_parameters = fitted_model.get_params()
    new_model = utils.load_model(model_name)(parameters=all_parameters)
    with pytest.raises(TypeError):
        new_model.predict()
        
@pytest.mark.parametrize('model_name, fitted_model', model_test_cases)
def test_all_parameters_fixed_predict_new_data(model_name, fitted_model):
    """Predict , with new data, when all passed parameters were fixed"""    
    all_parameters = fitted_model.get_params()
    new_model = utils.load_model(model_name)(parameters=all_parameters)
    assert len(new_model.predict(obs, predictors)) == len(obs)

@pytest.mark.parametrize('model_name, fitted_model', model_test_cases)
def test_estimate_all_but_one_parameter(model_name, fitted_model):
    """Estimate only a single parameter.
    
    The end result should be the same as what as passed
    """    
    all_parameters = fitted_model.get_params()
    fixed_param, fixed_value = all_parameters.popitem()
    new_model = utils.load_model(model_name)(parameters={fixed_param:fixed_value})
    new_model.fit(obs, predictors, optimizer_params='testing', debug=True)
    new_value = new_model.get_params()[fixed_param]
    
    assert new_value == fixed_value

@pytest.mark.parametrize('model_name, fitted_model', model_test_cases)
def test_error_on_bad_parameter_names(model_name, fitted_model):
    """Expect error when unknown parameter name is used"""
    with pytest.raises(RuntimeError):
        utils.load_model(model_name)(parameters={'not_a_parameter':0})
        
@pytest.mark.parametrize('model_name, fitted_model', model_test_cases)
def test_do_not_predict_wihout_fit(model_name, fitted_model):
    """Do not predict on unfitted model"""
    model = utils.load_model(model_name)()
    with pytest.raises(RuntimeError):
        model.predict(obs, predictors)

#########################################################
# These tests are for the core methods and do not need to be run 
# for all model types
        
def test_predict_with_nan():
    """model.predict() method should work with nan in obs.doy
    column. see https://github.com/sdtaylor/pyPhenology/issues/105
    """
    single_model = utils.load_model('ThermalTime')()
    single_model.fit(obs, predictors, optimizer_params='testing')

    obs_with_nan = obs.copy(deep=True)
    obs_with_nan['doy'] = np.nan
    p_with_nan = single_model.predict(obs_with_nan, predictors)
    p = single_model.predict(obs, predictors)

    assert np.all(p==p_with_nan)

def test_no_nan_in_observations_fit():
    """the observation data.frame, either in fitting or prediction,
    should not have any NA
    
    """
    single_model = utils.load_model('ThermalTime')()
    single_model.fit(obs, predictors, optimizer_params='testing')

    obs_with_nan = obs.copy(deep=True)
    obs_with_nan['year'][1] = np.nan
    
    with pytest.raises(ValueError):
        single_model.predict(obs_with_nan, predictors)

def test_no_nan_in_observations_predict():
    """the observation data.frame, either in fitting or prediction,
    should not have any NA
    
    """
    single_model = utils.load_model('ThermalTime')()

    obs_with_nan = obs.copy(deep=True)
    obs_with_nan['doy'][1] = np.nan
    
    with pytest.raises(ValueError):
        single_model.fit(obs_with_nan, predictors, optimizer_params='testing')
    
