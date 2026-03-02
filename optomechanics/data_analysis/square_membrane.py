import numpy as np

class membrane:
    """
    Made by Claude. Resonance frequency calculator for a pre-stressed square membrane resonator
    with an optional thin-film deposition.

    Parameters
    ----------
    length_x : float
        Membrane length along x (m).
    length_y : float
        Membrane length along y (m).
    height_of_sin : float
        Silicon nitride thickness (m).
    depth_deposition : float
        Thin-film deposition thickness (m).
    density_of_deposition : float
        Deposition material density (kg/m^3).
    density_of_membrane_material : float, optional
        SiN density (kg/m^3). Default is 2820.
    stress_of_membrane : float, optional
        Membrane stress (Pa). Default is 1e9.

    Attributes
    ----------
    area_of_membrane : float
        length_x * length_y (m^2).
    mass_of_membrane : float
        Mass of the bare SiN membrane (kg).
    mass_of_deposition : float
        Mass of the deposited thin film (kg).
    effective_mass_of_membrane : float
        Effective mass for the fundamental square mode = mass_of_membrane / 4,
        following "A general procedure for thermomechanical calibration of
        nano/micro-mechanical resonators".
    """

    def __init__(self, length_x, length_y, height_of_sin, depth_deposition, density_of_deposition, density_of_membrane_material = 2820, stress_of_membrane = 1e9 ):

        self.length_x = length_x
        self.length_y = length_y
        self.height_of_sin = height_of_sin
        self.depth_deposition = depth_deposition
        self.density_of_deposition = density_of_deposition
        self.density_of_membrane_material = density_of_membrane_material
        self.stress_of_membrane = stress_of_membrane

        #usefuls:
        self.area_of_membrane = self.length_x*self.length_y
        self.mass_of_membrane = self.area_of_membrane   * self.height_of_sin    * self.density_of_membrane_material
        self.mass_of_deposition = self.area_of_membrane * self.depth_deposition * self.density_of_deposition
        self.effective_mass_of_membrane = self.mass_of_membrane*1/4 # assumes square membrane, from A general procedure for thermomechanical calibration of nano/micro-mechanical resonators
        
        print(f"self.length_x = {length_x}")
        print(f"self.length_y = {length_y}")
        print(f"self.height_of_sin = {height_of_sin}")
        print(f"self.depth_deposition = {depth_deposition}")
        print(f"self.density_of_deposition = {density_of_deposition}")
        print(f"self.density_of_membrane_material = {density_of_membrane_material}")
        print(f"self.stress_of_membrane = {stress_of_membrane}")

        #usefuls:
        print(f"self.area_of_membrane = {self.length_x*self.length_y}")
        print(f"self.mass_of_membrane = {self.area_of_membrane   * self.height_of_sin    * self.density_of_membrane_material}")
        print(f"self.mass_of_deposition = {self.area_of_membrane * self.depth_deposition * self.density_of_deposition}")
        print(f"self.effective_mass_of_membrane = {self.mass_of_membrane*1/4}") # assumes square membrane, from A general procedure for thermomechanical calibration of nano/micro-mechanical resonators
        
    

    def fm(self, m_x, n_y):
        """
        Made by Claude. Calculate the resonance frequency for mode (m_x, n_y).

        Computes the bare membrane frequency f_m and the mass-loaded frequency
        reduced_f_m that accounts for the additional mass of the thin-film
        deposition.

        Parameters
        ----------
        m_x : int
            Mode number along x.
        n_y : int
            Mode number along y.

        Returns
        -------
        reduced_f_m : float
            Resonance frequency in Hz including deposition mass loading.
        f_m : float
            Bare membrane resonance frequency in Hz (no deposition mass loading).
        """

        sqrt_ = (self.stress_of_membrane/self.density_of_membrane_material) *((m_x/self.length_x )**2 + (n_y/self.length_y)**2)
        f_m = 0.5 * np.sqrt(sqrt_)
        numerator = self.length_x * self.length_y * self.height_of_sin * self.density_of_membrane_material *1/4 * f_m**2
        denominator = self.length_x * self.length_y * self.height_of_sin * self.density_of_membrane_material *1/4 + self.length_x * self.length_y * self.depth_deposition * self.density_of_deposition
        reduced_f_m = np.sqrt(numerator / denominator )

        return reduced_f_m, f_m
