### Class for reading ADCP data

# imports
import dolfyn as dlfn
import xarray as xr
import numpy as np


class ADCPReader():
    MD_PATHS = ['Q:/Messdaten/Aphys_hypothesis_data/{lake}/{year}/Mooring/{location}/{date}/{date}_{location}_meta.tsv',
                'Q:/Messdaten/Aphys_hypothesis_data/{lake}/{year}/Mooring/{location}/{date}/Notes.txt',
                'Q:/Messdaten/Aphys_hypothesis_data/{lake}/{year}/Mooring/{date}/{date}_{location}_meta.tsv']

    def __init__(self, lake, location, year, date, bathy_file, datalakes=False):
        """
        Initialize ADCPReader object.

        Parameters
        ----------
        lake : str
            Lake where ADCP is deployed.
        location : str
            Location code witin lake of ADCP deployment.
        year : str
            Year of ADCP retrieval.
        date : str
            Date (YYYYMMDD) of ADCP retrieval.
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



    def parse_metadata(self):
        """
        Parse metadata file.
        """
        raise NotImplementedError
    

    def set_total_depth(self, total_depth=None):
        """
        Set depth of lake at position of ADCP.

        Parameters
        ----------
        total_depth : float
            Depth of lake at ADCP position, calculated manually.
        """
        if not total_depth:
            bathy = xr.open_dataset(self.bathy_file)
            total_depth = bathy.sel(xsc=self.xsc, ysc=self.ysc).depth.item()

        return total_depth


    def load_from_L0(self):
        """
        Load raw (L0) ADCP data into xarray Dataset.

        Returns
        -------
        ds : xr.Dataset
            Dataset of all data recorded by ADCP.
        """
        return dlfn.read(self.fpath)
    

    def set_depth(self, depth=None):
        """
        Set depth of ADCP.  Use ADCP's depth if ADCP measures pressure.

        Parameters
        ----------
        depth : float
            Depth below water surface of ADCP, calculated manually.
        
        Returns
        -------
        depth : float
            Depth below water surface of ADCP.
        """
        if 'pressure' in self.ds.data_vars:
            depth = self.ds.depth.where(self.ds.depth != 0, drop=True).mean().item()
        elif not depth:
            raise ValueError('ADCP does not measure pressure, must provide manual depth argument.')
        
        return depth
    

    def range_to_depth(self, orientation=None):
        """
        Convert ADCP range values to depths.

        Parameters
        ----------
        orientation : str
            'up' for upwards looking ADCP, 'down' for downwards looking ADCP.
        """
        if orientation and orientation not in ['up', 'down']:
            raise ValueError('If specifying orient, must be "up" or "down".')
        
        if not orientation:
            orientation = self.ds.attrs['orientation']

        if orientation == 'up':
            self.ds['range'] = self.depth - self.ds.range.values
        elif orientation == 'down':
            self.ds['range'] = self.depth + self.ds.range.values


    def qa_interface_surface(self):
        """
        Filter data impacted by lake surface.
        """
        dist_sidelobe = self.depth * (1 - np.cos(self.ds.attrs['beam_angle'] * np.pi / 180))

        return self.ds.where(self.ds.range >= dist_sidelobe, drop=True)
    
    def qa_interface_bottom(self):
        """
        Filter data impacted by lake bottom.
        """
        dist_sidelobe = (self.total_depth - self.depth) * (1 - np.cos(self.ds.attrs['beam_angle'] * np.pi / 180))
        
        return self.ds.where(self.ds.range <= self.total_depth - dist_sidelobe, drop=True)
    

    def qa_min_corr(self, corr_thresh=64):
        """
        Filter data with at least one beam correlation < 64.

        Parameters
        ----------
        corr_thresh : int
            Threshold for beam correlations.
        """
        corr1 = self.ds.corr.sel(beam=1) >= corr_thresh
        corr2 = self.ds.corr.sel(beam=2) >= corr_thresh
        corr3 = self.ds.corr.sel(beam=3) >= corr_thresh
        corr4 = self.ds.corr.sel(beam=4) >= corr_thresh

        return self.ds.where(corr1 & corr2 & corr3 & corr4)
    
    
    def qa_pg14(self, pg14_thresh=25):
        """
        Filter data with PG1 + PG4 < 25%.

        Parameters
        ----------
        pg14_thresh : int
            Threshold for minimum good data percentage.
        """
        pg14 = self.ds.prcnt_gd.sel(beam=1) + self.ds.prcnt_gd.sel(beam=4)

        return self.ds.where(pg14 >= pg14_thresh)
    

    def qa_pg3(self, pg3_thresh=25):
        """
        Filter data with PG3 > 25 %.

        Parameters
        ----------
        pg3_thresh : int
            Threshold for maximum bad data percentage.
        """
        pg3 = self.ds.prcnt_gd.sel(beam=3)

        return self.ds.where(pg3 <= pg3_thresh)
    

    def qa_vel_error(self, velerr_thresh=0.05):
        """
        Filter data with velocity error > 0.05 m/s.

        Parameters
        ----------
        velerr_thresh : float
            Threshold for maximum velocity error.
        """
        velerr = abs(self.ds.vel.sel(dir='err'))

        return self.ds.where(velerr <= velerr_thresh)
    

    def qa_tilt(self, tilt_thresh=15):
        """
        Filter data with pitch or roll angle > 15°.

        Parameters
        ----------
        tilt_thresh : int
            Threshold for maximum tilt.
        """
        pitch = abs(self.ds['pitch']) <= tilt_thresh
        roll = abs(self.ds['roll']) <= tilt_thresh

        return self.ds.where(pitch & roll)
        
    
    def qa_corr_stdev(self, stdev_thresh=0.01):  # threshold may be too harsh (test not from manual)
        """
        Filter data with standard deviation of 4 beams' correlations > 0.01.
        
        Parameters
        ----------
        stdev_thresh : float
            Threshold for maximum standard deviation.
        """
        corr1 = self.ds.corr.sel(beam=1) / 100        # scale correlations to [0, 1]
        corr2 = self.ds.corr.sel(beam=2) / 100
        corr3 = self.ds.corr.sel(beam=3) / 100
        corr4 = self.ds.corr.sel(beam=4) / 100
        corr = xr.concat([corr1, corr2, corr3, corr4], dim='beam')
        corr_stdev = corr.std(dim='beam')

        return self.ds.where(corr_stdev <= stdev_thresh)
    

    def qa_echo_amp_diff(self, surfbot_toggle=True, ead_thresh=30):
        """
        Filter data with at least one beam with vertical echo difference between 
        consecutive bins > 30.

        Only required if beam reaches surface or bottom.

        Parameters
        ----------
        surfbot_toggle : bool
            Toggle whether ADCP range reaches lake surface or bottom.
        ead_thresh : int
            Threshold for minimum vertical echo difference
        """
        if not surfbot_toggle:
            return self.ds
        
        echo_amp_diff = self.ds.amp.diff(dim='range')
        ead1 = echo_amp_diff.sel(beam=1) <= ead_thresh
        ead2 = echo_amp_diff.sel(beam=2) <= ead_thresh
        ead3 = echo_amp_diff.sel(beam=3) <= ead_thresh
        ead4 = echo_amp_diff.sel(beam=4) <= ead_thresh

        return self.ds.where(ead1 & ead2 & ead3 & ead4)


