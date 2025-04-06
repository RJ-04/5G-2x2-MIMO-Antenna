import numpy as np
import skfuzzy as fuzz
import skfuzzy.control as ctrl
import cst.interface as cst
from scipy.interpolate import interp1d

de = cst.DesignEnvironment.new()
project = de.open_project(r"D:\My stuff\Antenna Design\antenna_1\antenna_1.cst")
print("CST Opened Successfully!")
model = project.model3d

# opens the specified cst project 

param = ['patch_length',  10.7, 0.1]

#-------------------------------------------------------------------------------------------------------------------------------

frequency_1 = ctrl.Antecedent(np.arange(20, 40, 1), 'Frequency_1')
frequency_2 = ctrl.Antecedent(np.arange(20, 40, 1), 'Frequency_2')

# 20-40 GHz frequency with step width of 1 GHz

s11_1 = ctrl.Antecedent(np.arange(-70, 0, 1), 'S11_1')  
s11_2 = ctrl.Antecedent(np.arange(-70, 0, 1), 'S11_2') 

# S11 values in dB with range -70 to 0 dB with step width of 1 dB

s21_1 = ctrl.Antecedent(np.arange(-60, 0, 1), 'S21_1') 
s21_2 = ctrl.Antecedent(np.arange(-60, 0, 1), 'S21_2')  

# S21 values in dB with range -60 to 0 dB with step width of 1 dB

efficiency_1 = ctrl.Antecedent(np.arange(0.5, 1, 0.05), 'Efficiency_1')  
efficiency_2 = ctrl.Antecedent(np.arange(0.5, 1, 0.05), 'Efficiency_2') 

# Efficiency values in percentage with range 0.5 to 1 with step width of 0.05

gain_1 = ctrl.Antecedent(np.arange(4, 10, 0.1), 'Gain_1')
gain_2 = ctrl.Antecedent(np.arange(4, 10, 0.1), 'Gain_2')

# Gain values in dB with range 4 to 10 with step width of 0.1

optimization_score = ctrl.Consequent(np.arange(0, 1.1, 0.1), 'Optimization_Score')

#-------------------------------------------------------------------------------------------------------------------------------

frequency_1['Targeted'] =  np.fmax(fuzz.gaussmf(frequency_1.universe, 27.5, 1) , fuzz.gaussmf(frequency_1.universe, 38, 0.75))
frequency_2['Targeted'] =  np.fmax(fuzz.gaussmf(frequency_2.universe, 27.5, 1) , fuzz.gaussmf(frequency_2.universe, 38, 0.75))

# Targeted frequency range is 28 & 38 GHz with a peak at 27.5 GHz and 38Ghz distributed symetrically with as Normal distribution

s11_1['Good'] = fuzz.sigmf(s11_1.universe, -18.75, 3)
s11_2['Good'] = fuzz.sigmf(s11_2.universe, -18.75, 3)

# S11 values are good if they are less than -18.75 dB, using a sigmoidal function with a steepness of 3

s21_1['High Isolation'] = fuzz.sigmf(s21_1.universe, -18.75, 3)
s21_2['High Isolation'] = fuzz.sigmf(s21_2.universe, -18.75, 3)

# S21 values are good if they are less than -18.75 dB, using a sigmoidal function with a steepness of 3

efficiency_1['High'] = fuzz.sigmf(efficiency_1.universe, 0.8, 50)
efficiency_2['High'] = fuzz.sigmf(efficiency_2.universe, 0.8, 50)

# Efficiency values are good if they are greater than 0.8, using a sigmoidal function with a steepness of 50

gain_1['High'] = fuzz.sigmf(gain_1.universe, 9, 50)
gain_2['High'] = fuzz.sigmf(gain_2.universe, 9, 50)

# Gain values are good if they are greater than 9 dB, using a sigmoidal function with a steepness of 50

optimization_score['Optimal'] = fuzz.sigmf(optimization_score.universe, 0.8, 25)

#-------------------------------------------------------------------------------------------------------------------------------

rule = ctrl.Rule(frequency_1['Targeted'] & frequency_2['Targeted'] & s11_1['Good'] & s11_2['Good'] & s21_1['High Isolation'] & s21_2['High Isolation'] & efficiency_1['High'] & efficiency_2['High'] & gain_1['High'] & gain_2['High'], optimization_score['Optimal'])

opt_control = ctrl.ControlSystem([rule])
opt_simulation = ctrl.ControlSystemSimulation(opt_control)

#-------------------------------------------------------------------------------------------------------------------------------

def get_s_parameter(model, param_name):
    s_param_data = model.ResultTree.GetResultFromTreeItem(f'1D Results\\S-Parameters\\{param_name}', '3D:RunID:0')

    frequencies = np.array(s_param_data.GetArray('x'))

    s_real = np.array(s_param_data.GetArray('yre'))
    s_imag = np.array(s_param_data.GetArray('yim'))

    s_magnitude = np.sqrt(s_real**2 + s_imag**2)
    s_param_dB = 20 * np.log10(s_magnitude)

    return frequencies, s_param_dB

def get_efficiency(model):
    eff = model.ResultTree.GetResultFromTreeItem('1D Results\Efficiencies\Tot. Efficiency [1]', '3D:RunID:0')

    eff_real = np.array(eff.GetArray('yre'))  
    eff_imag = np.array(eff.GetArray('yim'))  

    eff_magnitude = np.sqrt(eff_real**2 + eff_imag**2)

    return eff_magnitude

def get_gain(model):
    gain = model.ResultTree.GetResultFromTreeItem('Tables\\1D Results\\Max Gain over Frequency', '3D:RunID:0')

    gain_magnitude = np.array(gain.GetArray('y'))

    return gain_magnitude

#-------------------------------------------------------------------------------------------------------------------------------

current_par = param[1] 
best_score = 0
best_params = param[1]

for i in range(5):  
    model.StoreParameter(param[0], current_par)
    model.Rebuild()
    model.Save()
    model.run_solver()
    
    #-------------------------------------------------------------------------------------------------------------------------------

    f, s11_val = get_s_parameter(model, 'S1,1')
    f, s21_val = get_s_parameter(model, 'S2,1')
    efficiency_val = get_efficiency(model)
    gain_val = get_gain(model)
    
    f_efficiency_val = np.linspace(f[0], f[-1], len(efficiency_val)) 
    f_gain_val = np.linspace(f[0], f[-1], len(gain_val))  
    efficiency_interp = interp1d(f_efficiency_val, efficiency_val, kind='linear', fill_value='extrapolate')
    gain_interp = interp1d(f_gain_val, gain_val, kind='linear', fill_value='extrapolate')
    
    #-------------------------------------------------------------------------------------------------------------------------------

    best_freq_1_idx = np.argmin(s11_val) 
    best_freq_1 = f[best_freq_1_idx]
    s11_1_val = s11_val[best_freq_1_idx]
    s21_1_val = s21_val[best_freq_1_idx]
    interpolated_efficiency_1 = float(efficiency_interp(best_freq_1))
    interpolated_gain_1 = float(gain_interp(best_freq_1))

    # frequency 1 is the one with the lowest S11 value
    # all other parameters are sampled at this frequency

    opt_simulation.input['Frequency_1'] = best_freq_1
    opt_simulation.input['S11_1'] = -s11_1_val
    opt_simulation.input['S21_1'] = -s21_1_val
    opt_simulation.input['Efficiency_1'] = interpolated_efficiency_1
    opt_simulation.input['Gain_1'] = interpolated_gain_1

    #-------------------------------------------------------------------------------------------------------------------------------

    mask = (f < (best_freq_1 - 2)) | (f > (best_freq_1 + 2))
    masked_s11 = np.where(mask, s11_val, np.inf)
    masked_s21 = np.where(mask, s21_val, np.inf)
    best_freq_2_idx = np.argmin(masked_s11) 

    # frequency 2 is the one with the lowest S11 value, after frequency 1
    # all other parameters are sampled at this frequency

    best_freq_2 = f[best_freq_2_idx]
    s11_2_val = masked_s11[best_freq_2_idx]
    s21_2_val = s21_val[best_freq_2_idx]
    interpolated_efficiency_2 = float(efficiency_interp(best_freq_2))
    interpolated_gain_2 = float(gain_interp(best_freq_2))

    opt_simulation.input['Frequency_2'] = best_freq_2
    opt_simulation.input['S11_2'] = -s11_2_val
    opt_simulation.input['S21_2'] = -s21_2_val
    opt_simulation.input['Efficiency_2'] =  interpolated_efficiency_2
    opt_simulation.input['Gain_2'] = interpolated_gain_2

    #-------------------------------------------------------------------------------------------------------------------------------
    
    opt_simulation.compute()
    score = opt_simulation.output['Optimization_Score']

    print(f"\nfreq=  {best_freq_1:.2f},  {best_freq_2:.2f}")
    print(f"s1,1= {s11_1_val:.2f}, {s11_2_val:.2f}")
    print(f"s2,1= {s21_1_val:.2f}, {s21_2_val:.2f}")
    print(f"effi=   {interpolated_efficiency_1:.2f},   {interpolated_efficiency_2:.2f}")
    print(f"gain=   {interpolated_gain_1:.2f},   {interpolated_gain_2:.2f}")
    print(f"\nIteration {i+1}: Score = {score:.2%} \n")

    if score > best_score:
        best_score = score
        best_params = current_par

    current_par = current_par + param[2]

print(f"Best Parameters: {param[0]}={best_params}, Best Score={best_score:.2%}")
model.StoreParameter(param[0], best_params)
model.Rebuild()
model.Save()
print("Optimized Design Saved!")