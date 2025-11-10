### Class for reading CTD data

# imports



class CTDReader():


    def __init__(self, bathy_file, datalakes=False):
        """
        Initialize CTDReader object.

        Parameters
        ----------
        bathy_file : str
            File path to bathymetry data.
        datalakes : bool
            Togle whether to read from Eawag drive or Datalakes.
        """
        self.bathy_file = bathy_file
        self.datalakes = datalakes