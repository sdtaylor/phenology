import numpy as np
import json
import os
from scipy import optimize
import numexpr as ne
from warnings import warn

def mean_temperature(temperature, doy_series, start_doy, end_doy):
    """Mean temperature of a single time period.
    ie. mean spring temperature.
    
    Parameters
    ----------
    temperature : Numpy array
        array of daily temperature values
        
    doy_series : Numpy array
        1D array as produced by format_data(),
        identifying the doy values in forcing[:,b]
    
    start_doy : int
        The beginning of the time period
        
    end_doy : int
        The end of the time period
    """
    if start_doy>end_doy:
        raise RuntimeError('start_doy must be < end_doy')
    
    spring_days = np.logical_and(doy_series>=start_doy,doy_series<=end_doy)
    return temperature[spring_days].mean(axis=0)

def triangle_response(temperature, t_min, t_opt, t_max):
    """Triangle function
    
    Used to simulate and optimal temperature between a low and high temperature.
    """
    outside_triangle = np.logical_or(temperature<=t_min, temperature>=t_max)
    left_side = np.logical_and(temperature > t_min, temperature <= t_opt)
    right_side= np.logical_and(temperature > t_opt, temperature < t_max)
    
    temperature[left_side] -= t_min
    temperature[left_side] /= t_opt - t_min
    
    temperature[right_side] -= t_max
    temperature[right_side] /= t_opt - t_max
    
    temperature[outside_triangle]=0

    return temperature

def sigmoid2(temperature, b, c):
    """The two parameter sigmoid function from Chuine 2000
    
    Parameters
    ----------
    temperature : Numpy array
        array of daily temperature values
    
    b : int
        Sigmoid fitting parameter
    
    c : int
        Sigmoid fitting parameter
    
    Returns
    -------
    temperature : Numpy array
        array of daily forcings derived from function
    """
    return ne.evaluate('1 / (1 + exp(b*(temperature-c)))')

def sigmoid3(temperature, a, b, c):
    """The three parameter sigmoid function from Chuine 2000
    
    Parameters
    ----------
    temperature : Numpy array
        (obs,doy) array of daily temperature values
    
    a : int
        Sigmoid fitting parameter
    
    b : int
        Sigmoid fitting parameter
    
    b : int
        Sigmoid fitting parameter
        
    Returns
    -------
    temperature : Numpy array
        array of daily forcings derived from function
    """
    return ne.evaluate('1 / (1 + exp(a*((temperature - c)**2) + b*(temperature-c)))')

def daylength(doy, latitude):
    """Calculates daylength in hours
    
    From https://github.com/khufkens/phenor
    """
    assert isinstance(doy, np.ndarray), 'doy should be np array'
    assert isinstance(latitude, np.ndarray) , 'latitude should be np array'
    assert doy.shape == latitude.shape, 'latitude and doy should be equal lengths'
    assert len(doy.shape)==1, 'doy should be 1 dimensional'
    doy = doy.copy()
    latitude = latitude.copy()
    
    # negative doy values used in pyPhenology should be converted back to
    # positive for daylength calculation
    doy[doy<1] += 365
    
    # set constants
    latitude = (np.pi / 180) * latitude
    
    # Correct for winter solistice
    doy += 11
    
    # earths ecliptic
    j = np.pi / 182.625
    axis = (np.pi / 180) * 23.439
    
    m = 1 - np.tan(latitude) * np.tan(axis * np.cos(j * doy))
    
    # sun never appears or disappears
    m = np.maximum(m, 0)
    m = np.minimum(m, 2)
    
    # Exposed fraction of the sun's circle
    b = np.arccos(1 - m) / np.pi
    
    # Daylength (lat,day)
    b *= 24
    
    return b

def forcing_accumulator(temperature):
    """ The accumulated forcing for each observation
    and doy in the (obs, doy) array.
    """
    return temperature.cumsum(axis=0)

def doy_estimator(forcing, doy_series, threshold, non_prediction=999):
    """ Find the doy that some forcing threshold is met for a large
    number of sites.
    
    Parameters
    ----------
    forcing : Numpy array
        Either a 2d or 3d array holding timeseries of
        daily mean temperature value of different replicates.
        The 0 axis is always the time axis. Axis 1 in a 2d array
        is the number of replicates. Axis 1 and 2 in a 3d array
        are the spatial replicates (ie lat, lon)
        values are the accumulated forcing for 
        each replicate,doy.
    
    doy_series : Numpy array
        1D array as produced by format_data(),
        identifying the doy values in forcing[0]
        
    threshold : float | int
        Threshold that must be met in forcing
    
    non_prediction : int
        Value to return if the threshold value is not
        met. A large value should be used during fitting
        to ensure unrealistic parameters are not chosen.
    
    Returns
    -------
    doy_final : Numpy array
        1D array of length obs with the doy values which
        first meet the threshold
    """
    #If threshold is not met for a particular row, ensure that a large doy
    #gets returned so it produces a large error
    non_prediction_buffer = np.expand_dims(np.zeros_like(forcing[0]), axis=0)
    non_prediction_buffer[:] = 10e5
    forcing = np.concatenate((forcing, non_prediction_buffer), axis=0)
    doy_series = np.append(doy_series, non_prediction)

    #The index of the doy for each element where F was met
    doy_with_threshold_met = np.argmax(forcing>=threshold, axis=0)
    
    doy_final = np.take(doy_series, doy_with_threshold_met)
    
    return doy_final

def temperature_only_data_prep(observations, predictors, for_prediction=False,
                               verbose=True):
    """Create a numpy array of shape (a,b), where b
    is equal to the sample size in observations, and a is
    equal to the number of days in the yearly time
    series of temperature (ie. Jan 1 - July 30).
    Using a numpy array in this way allows for very 
    efficient processing of phenology mdoels.
    
    Parameters
    ----------
    observations : Pandas Dataframe
        A data frame with columns ['doy','year','site_id'],
        where every row is an observation for an observed
        phenological event.
    
    predictors : Pandas Dataframe
        A Dataframe with columns['temperature','year','site_id']
        which matches to the sites and years in observations.
    
    for_prediction : bool
        Do not return observed_doy, or expect a doy column in observations.
        
    verbose : bool
        Show details of processing

    Returns
    -------
    observed_doy : Numpy array
        a 1D array of the doy of each observation
        
    temperature_array : Numpy array
        a 2D array described above
    
    doy_series : Numpy array
        1D array with length equal to the number of columns
        in temperature_array. Represents the doy values.
        (ie. doy 0 = Jan 1)
    
    """
    predictors = predictors[['doy','site_id','year','temperature']].copy()
    doy_series = predictors.doy.dropna().unique()
    doy_series.sort()
    predictors = predictors.pivot_table(index=['site_id','year'], columns='doy', values='temperature').reset_index()
    
    # This first day of temperature data can causes NA issues because of leap years.
    # If thats the case try dropping it. 
    first_doy_has_na = predictors.iloc[:,2].isna().any() # first day will always be col 2
    if first_doy_has_na:
        first_doy_column = predictors.columns[2]
        predictors.drop(first_doy_column, axis=1, inplace=True)
        doy_series = doy_series[1:]
        warn("""Dropped temperature data for doy {d} due to missing data. Most likely from leap year mismatch""".format(d=first_doy_column))
    
    # Give each observation a temperature time series
    obs_with_temp = observations.merge(predictors, on=['site_id','year'], how='left')
    
    # Deal with any site/years that don't have tempterature data
    original_sample_size = len(obs_with_temp)
    rows_with_missing_data = obs_with_temp.isnull().any(axis=1)
    missing_info = obs_with_temp[['site_id','year']][rows_with_missing_data].drop_duplicates()
    if len(missing_info)>0:
        obs_with_temp.dropna(axis=0, inplace=True)
        n_dropped = original_sample_size - len(obs_with_temp)
        warn('Dropped {n0} of {n1} observations because of missing data'.format(n0=n_dropped, n1=original_sample_size) + \
             '\n Missing data from: \n' + str(missing_info))
    
    observed_doy = obs_with_temp.doy.values
    temperature_array = obs_with_temp[doy_series].values.T
    
    if for_prediction:
        return temperature_array, doy_series
    else:
        return observed_doy, temperature_array, doy_series

def get_loss_function(method):
    if method == 'rmse':
        return lambda obs, pred: np.sqrt(np.mean((obs - pred)**2))
    elif method == 'aic':
        return lambda obs, pred, n_param: len(obs) * np.log(np.mean((obs - pred)**2)) + 2*(n_param + 1)
    else:
        raise ValueError('Unknown loss method: ' + method)

def validate_optimizer_parameters(optimizer_method, optimizer_params):
    sensible_defaults = {'DE': {'testing':{'maxiter':5, 
                                           'popsize':10, 
                                           'mutation':(0.5,1),
                                           'recombination':0.25,
                                           'disp':False},
                              'practical':{'maxiter':1000, 
                                           'popsize':50, 
                                           'mutation':(0.5,1),
                                           'recombination':0.25,
                                           'disp':False},
                              'intensive':{'maxiter':10000, 
                                           'popsize':100, 
                                           'mutation':(0.1,1),
                                           'recombination':0.25,
                                           'disp':False},
                                },
                        'BF': {'testing':  {'Ns':2,
                                            'finish':optimize.fmin_bfgs,
                                            'disp':False},
                               'practical': {'Ns':20,
                                            'finish':optimize.fmin_bfgs,
                                            'disp':False},
                               'intensive': {'Ns':40,
                                            'finish':optimize.fmin_bfgs,
                                            'disp':False}},
                        'BH': {'testing':  {'niter':100,
                                            'T':0.5,
                                            'stepsize':0.5,
                                            'disp':False},
                               'practical': {'niter':50000,
                                            'T':0.5,
                                            'stepsize':0.5,
                                            'disp':False},
                               'intensive': {'niter':500000,
                                            'T':0.5,
                                            'stepsize':0.5,
                                            'disp':False}}
                        }
                        
    if isinstance(optimizer_params, str):
        try:
            optimizer_params = sensible_defaults[optimizer_method][optimizer_params]
        except KeyError:
            raise ValueError('Unknown sensible parameter string: ' + optimizer_params)
    
    elif isinstance(optimizer_params, dict):
        pass
    else:
        raise TypeError('Invalid optimizer parameters. Must be str or dictionary')
    
    return optimizer_params

def fit_parameters(function_to_minimize, bounds, method, results_translator,
                   optimizer_params, verbose=False):
    """Internal functions to estimate model parameters. 
    
    Methods
    -------
    'DE', Differential evolution
        Uses a large number of randomly specified parameters which converge
        on a global optimum. 
    
        https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.differential_evolution.html
    
    'BF', Brute force
        Searches for the best parameter set within a confined space. Can take
        an extremely long time if used beyond 2 or 3 parameters.
        
        https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.brute.html
    
    'SA', Simulated annealing
        The most commonly used method in phenology modelling. Not yet implemented
        here as scipy has discontinued it in favor of basin hopping.
        
        https://docs.scipy.org/doc/scipy-0.14.0/reference/generated/scipy.optimize.anneal.html
        
    'BH, Basin hopping
        Starts off in a search space randomly, "hopping" around until a suitable
        minimum value is found. Note yet implimented.
        
        https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.basinhopping.html
            
    Parameters
    ----------
    funtions_to_minimize : func
        A minimizer function to pass to the optimizer model. Normally
        models._base_model.scipy_error
        
    bounds : list
        List of tuples specifying the upper and lower search space,
        where each tuple represents a model parameter
    
    method : str
        Optimization method to use
    
    results_translator : func
        A function to translate the optimizer output to a dictionary
    
    optimzier_parms : dict
        parameters to pass to the scipy optimizer
        
    Returns
    -------
    fitted_parameters : dict
        Dictionary of fitted parameters
    
    """
    if not isinstance(method, str):
        raise TypeError('method should be string, got ' + type(method))
        
    if method == 'DE':
        optimizer_params = validate_optimizer_parameters(optimizer_method=method,
                                                         optimizer_params=optimizer_params)
        
        optimize_output = optimize.differential_evolution(function_to_minimize,
                                                          bounds=bounds, 
                                                          **optimizer_params)
        fitted_parameters = results_translator(optimize_output['x'])

    elif method == 'BH':
        optimizer_params = validate_optimizer_parameters(optimizer_method=method,
                                                         optimizer_params=optimizer_params)
        # optimize.bashinhopping takes an initial guess value, so here
        # choose one randomly from the (low,high) search ranges given
        initial_guess = [float(np.random.randint(l, h)) for l,h in bounds]

        optimize_output = optimize.basinhopping(function_to_minimize,
                                                x0 = initial_guess,
                                                **optimizer_params,
                                                minimizer_kwargs={'method':'L-BFGS-B',
                                                                  'bounds':bounds})
        fitted_parameters = results_translator(optimize_output['x'])
        
    elif method == 'SE':
        raise NotImplementedError('Simulated Annealing not working yet')
    elif method == 'BF':
        optimizer_params = validate_optimizer_parameters(optimizer_method=method,
                                                         optimizer_params=optimizer_params)
        
        # BF takes a tuple of tuples instead of a list of tuples like DE
        bounds = tuple(bounds)

        optimize_output = optimize.brute(func = function_to_minimize,
                                         ranges = bounds,
                                         **optimizer_params)

        fitted_parameters =  results_translator(optimize_output)
    else:
        raise ValueError('Uknown optimizer method: '+str(method))
    
    if verbose:
        print('Optimizer method: {x}\n'.format(x=method))
        print('Optimizer parameters: \n {x}\n'.format(x=optimizer_params))
        
    return fitted_parameters

def read_saved_model(model_file):
    with open(model_file, 'r') as f:
        m = json.load(f)
    return m
    
def write_saved_model(model_info, model_file, overwrite):
    if os.path.exists(model_file) and not overwrite:
        raise RuntimeWarning('File {f} exists. User overwrite=True to overwite'.format(f=model_file))
    else:
        with open(model_file, 'w') as f:
            json.dump(model_info, f, indent=4)
