import os
import glob
import subprocess
import configparser

from .settings import config
from .helpers import get_bash_path

# An ExtractCubes object is tasked with reducing a single case of
# raw CHARIS data from SMOKA into datacubes pyKLIP can use. Each 
# of its methods represent a step in the extraction process.
class ExtractCubes:
    # initialize directory variables and create new directories if needed
    def __init__(self, case_dir):
        self.case_dir = case_dir
        self.raw_data_dir = os.path.join(case_dir,'raw/data')
        self.calib_dir = os.path.join(case_dir, 'raw/calib')
        self.cubes_dir = os.path.join(case_dir, 'extracted/cubes')
        self.ramps_dir = os.path.join(case_dir, 'extracted/ramps')
        self.config_file_path = os.path.join(case_dir, 'modified.ini')

        if not os.path.exists(self.case_dir):
            raise Exception('Case directory does not exist!')
        if not os.path.exists(self.raw_data_dir):
            raise Exception('Raw data directory does not exist!')
        if not os.path.exists(self.calib_dir):
            raise Exception('Calibration directory does not exist!')
        if not os.path.exists(self.cubes_dir):
            os.makedirs(self.cubes_dir)
        if not os.path.exists(self.ramps_dir):
            os.makedirs(self.ramps_dir)
    
    # First step in extracting a datacube, generates a wavelength
    # calibration from a calibration file located in the case/raw/calib
    # directory.
    def generate_wavecal(self, overwrite=False):
        calib_file = glob.glob(os.path.join(self.calib_dir, '*.fits'))
        if overwrite or len(calib_file) == 1:
            bash_command = 'cd {} && printf \'{}\n{}\n{}\' | buildcal {}'.format(get_bash_path(self.calib_dir), 
                                                                                    config['Wavecal']['oversample'],
                                                                                    config['Wavecal']['threads'],
                                                                                    config['Wavecal']['continue'],
                                                                                    os.path.basename(calib_file[0]))
            output = os.system(bash_command)
            print("output: ", output)

    # Second step in extracting a datacube, generates a .ini file that 
    # the CHARISDRP needs to perform step 3.
    def generate_extract_config(self, overwrite=False):
        if overwrite or not os.path.exists(os.path.join(self.case_dir, "modified.ini")):
            caldir = os.path.relpath(self.calib_dir, self.cubes_dir)
            config['Calib']['calibdir'] = caldir
            sections = ['Ramp', 'Calib', 'Extract'] # sections that need to be copied over to new .ini file
            modified = self._create_config_sections(sections)
            with open(os.path.join(self.case_dir,'modified.ini'), 'w') as config_file:
                modified.write(config_file)

    # Third step in extracting a datacube. Extract the cubes using bash
    # commands for CHARISDRP.
    def generate_reduced_cubes(self, overwrite=False):
        files = glob.glob(os.path.join(self.cubes_dir, '*.fits')) + glob.glob(os.path.join(self.ramps_dir, '*.fits'))
        if overwrite or len(files) == 0:
            bash_command = 'cd {} && extractcube {} {}'.format(get_bash_path(self.cubes_dir),
                                                                os.path.join(get_bash_path(self.raw_data_dir), '*.fits'),
                                                                get_bash_path(self.config_file_path)) 
            output = os.system(bash_command)
            print("output: ", output)

        displaced_ramps = glob.glob(os.path.join(self.cubes_dir, '*?ramp.fits'))
        for ramp in displaced_ramps:
            os.rename(ramp, os.path.join(self.ramps_dir, os.path.basename(ramp)))

    # Helper function for self.generate_extract_config(). Given a list
    # of sections, creates a new config file with only the sections in 
    # that list.
    def _create_config_sections(self, sections):
        new_config = configparser.ConfigParser()
        for section in sections:
            if not config.has_section(section):
                raise Exception("{} is not in config file!".format(section))
            new_config.add_section(section)
            for item in config.items(section):
                new_config[section][item[0]] = item[1]
        return new_config





            


