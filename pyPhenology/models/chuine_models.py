from . import utils
from .base import _base_model

class Uniforc(_base_model):
    """Uniforc model
    
    Single phase forcing model using a sigmoid function for forcing units.
    
    Event happens on :math:`DOY` when the following is met:
        
    .. math::
        \sum_{t=t_{1}}^{DOY}R_{f}(T_{i})\geq F^{*} 
    
    where:
    
    .. math::
        R_{f}(T_{i}) = \\frac{1}{1 + e^{b(T_{i}-c)}}
    
    Parameters:
        t1 : int
            | :math:`t_{1}` - The DOY which forcing accumulating beings
            | default : (-67,298)
        
        F : int, > 0
            | :math:`F^{*}` - The total forcing units required
            | default : (0,200)
            
        b : int, < 0
            | :math:`b` - Sigmoid function parameter
            | default : (-20,0)
        
        c : int
            | :math:`c` - Sigmoid function parameter
            | default (-50,50)
        
        
    Notes:
        Chuine, I. (2000). A Unified Model for Budburst of Trees. 
        Journal of Theoretical Biology, 207(3), 337–347. 
        http://doi.org/10.1006/jtbi.2000.2178
    
    """
    def __init__(self, parameters={} ):
        _base_model.__init__(self)
        self.all_required_parameters = {'t1':(-67,298),'F':(0,200),'b':(-20,0),'c':(-50,50)}
        self._organize_parameters(parameters)
    
    def _apply_model(self, temperature, doy_series, t1, F, b, c):
        temperature = utils.sigmoid2(temperature, b=b, c=c)
    
        #Only accumulate forcing after t1
        temperature[doy_series<t1]=0
    
        accumulateed_forcing=utils.forcing_accumulator(temperature)
    
        return utils.doy_estimator(forcing = accumulateed_forcing,
                                   doy_series=doy_series,
                                   threshold=F)

class Unichill(_base_model):
    """Unichill two-hase model.
    
    Two phase forcing model using a sigmoid function for forcing and
    chilling units. 
    
    TODO: unichill equation
    
    Parameters:
        t0 : int
            | The DOY which chilling accumulating beings
            | default : (-67,298)
        
        C : int, > 0
            | The total chilling units required
            | default : (0,300)

        F : int, > 0
            | The total forcing units required
            | default : (0,200)
            
        b_f : int, < 0
            | Sigmoid function parameter for forcing
            | default : (-20,0)
        
        c_f : int
            | Sigmoid function parameter for forcing
            | default : (-50,50)
            
        a_c : int, > 0
            | Sigmoid funcion parameter for chilling
            | default : (0,20)
            
        b_c : int
            | Sigmoid funcion parameter for chilling
            | default : (-20,20)
            
        c_c : int
            | Sigmoid funcion parameter for chilling
            | default : (-50,50)
            
    Notes:
        Chuine, I. (2000). A Unified Model for Budburst of Trees. 
        Journal of Theoretical Biology, 207(3), 337–347. 
        http://doi.org/10.1006/jtbi.2000.2178
            
    """
    def __init__(self, parameters={}):
        _base_model.__init__(self)
        self.all_required_parameters = {'t0':(-67,298),'C':(0,300),'F':(0,200),
                                        'b_f':(-20,0),'c_f':(-50,50),
                                        'a_c':(0,20),'b_c':(-20,20),'c_c':(-50,50)}
        self._organize_parameters(parameters)
    
    def _apply_model(self, temperature, doy_series, t0, C, F, b_f, c_f, a_c, b_c, c_c):
        if len(temperature.shape)>2:
            raise NotImplementedError('Unichill model currently only supports 2d temperature arrays')

        temp_chilling = temperature.copy()
        temp_forcing  = temperature.copy()
        
        temp_forcing = utils.sigmoid2(temp_forcing, b=b_f, c=c_f)
        temp_chilling =utils.sigmoid3(temp_chilling, a=a_c, b=b_c, c=c_c) 
    
        #Only accumulate chilling after t0
        temp_chilling[doy_series<t0]=0
        accumulated_chill=utils.forcing_accumulator(temp_chilling)
        
        # Heat forcing accumulation starts when the chilling
        # requirement, C, has been met(t1 in the equation). 
        # Enforce this by setting everything prior to that date to 0
        # TODO: optimize this so it doesn't use a for loop
        t1_values = utils.doy_estimator(forcing = accumulated_chill,
                                        doy_series=doy_series,
                                        threshold=C)
        for col, t1 in enumerate(t1_values):
            temp_forcing[doy_series<t1, col]=0
    
        accumulated_forcing = utils.forcing_accumulator(temp_forcing)
        
        return utils.doy_estimator(forcing = accumulated_forcing,
                                   doy_series=doy_series,
                                   threshold=F)
