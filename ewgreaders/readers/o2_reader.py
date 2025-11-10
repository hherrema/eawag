### Class for reading Oxygen logger data

# imports
import xarray as xr



class O2Reader():
    MD_PATHS = ['Q:/Messdaten/Aphys_hypothesis_data/{lake}/{year}/Mooring/{location}/{date}/{date}_{location}_meta.tsv',
                'Q:/Messdaten/Aphys_hypothesis_data/{lake}/{year}/Mooring/{location}/{date}/Notes.txt',
                'Q:/Messdaten/Aphys_hypothesis_data/{lake}/{year}/Mooring/{date}/{date}_{location}_meta.tsv']

    def __init__(self, bathy_file, datalakes=False):
        """
        Initialize O2Reader object.

        Parameters
        ----------
        bathy_file : str
            File path to bathymetry data.
        datalakes : bool
            Toggle whether to read from Eawag drive or DataLakes.
        """
        self.bathy_file = bathy_file
        self.datalakes = datalakes


    def locate_md_file(self):
        """
        Locate metadata file.
        """
        raise NotImplementedError


    def parse_metadata(self):
        """
        Parse metadata file.
        """
        raise NotImplementedError
    

    def set_total_depth(self, total_depth=None):
        """
        Set depth of lake at position of oxygen logger.

        Parameters
        ----------
        total_depth : float
            Depth of lake at oxygen logger position, calculated manually.
        """
        if not total_depth:
            bathy = xr.open_dataset(self.bathy_file)
            total_depth = bathy.sel(xsc=self.xsc, ysc=self.ysc).depth.item()

        return total_depth
    

    def load_single_logger_from_L0(self):
        """
        Load raw (L0) oxygen logger data into xarray DataArray.

        Returns
        -------
        da : xr.DataArray
            DataArray
        """


    def load_from_L0(self):
        """
        Load raw (L0) oxygen logger data into xarray Dataset.

        Returns
        -------
        ds : xr.Dataset
            Dataset of data recorded by all oxygen loggers on mooring.
        """
        raise NotImplementedError