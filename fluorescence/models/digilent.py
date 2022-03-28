import numpy as np
import time
from multiprocessing import Lock

from experimentor.core.signal import Signal
from experimentor.drivers.digilent import AnalogDiscovery
from experimentor.drivers.digilent.dwfconst import AnalogAcquisitionFilter, AnalogInTriggerMode, InstrumentState, \
    TriggerCondition, \
    TriggerSource
from experimentor.lib.log import get_logger
from experimentor.models.action import Action
from experimentor.models.decorators import make_async_thread
from experimentor.models.devices.base_device import ModelDevice


class DigilentModel(ModelDevice):
    _digilent_lock = Lock()
    new_data = Signal()

    def __init__(self, config):
        super(DigilentModel, self).__init__()
        self.driver = AnalogDiscovery()
        self.config = config
        self.last_daq = np.zeros((100))
        self.logger = get_logger()
        self.continuous_reads_running = False
        self.keep_continuous_reads = False
        self.finalized = True

    def initialize(self):
        """Initializes the communication with the Digilent board
        """

        self.driver.initialize()
        self.finalized = False

    @Action
    def reconfigure_daq(self):
        """Configures the analog channles based on the parameters stored in the configuration dictionary
        """
        self.driver.analog_in_configure(reconfigure=True, start=True)
        self.driver.analog_in_channel_enable(self.config['channel_in'])
        self.logger.info(f'Channel in: {self.config["channel_in"]}')
        self.driver.analog_in_channel_offset_set(self.config['channel_in'], 0)
        self.driver.analog_in_channel_range_set(self.config['channel_in'], 5)
        self.driver.analog_in_buffer_size_set(self.config['buffer'])
        self.logger.info(f'Buffer: {self.config["buffer"]}')
        self.driver.analog_in_frequency_set(self.config['frequency'])
        self.logger.info(f'Frequency: {self.config["frequency"]}')
        self.driver.analog_in_channel_filter_set(self.config['channel_in'], AnalogAcquisitionFilter.filterDecimate)
        if self.config['trigger'] == 'none':
            self.driver.analog_in_trigger_source_set(TriggerSource.none)
        elif self.config['trigger'] == 'analog':
            self.logger.info(f'Trigger analog')
            self.driver.analog_in_trigger_source_set(TriggerSource.DetectorAnalogIn)
            self.driver.analog_in_trigger_channel_set(self.config['channel_trigger'])
            self.logger.info(f'Channel trigger: {self.config["channel_trigger"]}')
            self.driver.analog_in_trigger_type_set(AnalogInTriggerMode.trigtypeEdge)
            self.driver.analog_in_trigger_level_set(self.config['trigger_level'])
            self.driver.analog_in_trigger_condition_set(TriggerCondition.trigcondRisingPositive)
        self.driver.analog_in_configure(reconfigure=False, start=True)
        status = self.driver.analog_in_status(read_data=False)
        self.logger.info(f'Reconfigured driver. Status: {status}')

    def read_analog(self):
        """Reds the data from the analog channel and makes it available as an attribute ```self.last_daq'''
        """
        with self._digilent_lock:
            status = self.driver.analog_in_status(read_data=True)

            if status == InstrumentState.Done:
                data = self.driver.analog_in_status_data(self.config['channel_in'], self.config['buffer'])
                self.last_daq = data
                return data
            else:
                self.logger.debug('Reading from DAQ faster than its acquisition time')

    @make_async_thread
    def continuous_reads(self):
        """ Keeps reading the analog channel and emits a signal with the latest data.
        """
        if self.continuous_reads_running:
            self.logger.warning("Trying to start a second instance of continuous reads")
            return

        self.continuous_reads_running = True
        self.keep_continuous_reads = True
        while self.keep_continuous_reads:
            data = self.read_analog()
            if data is not None:
                self.new_data.emit(data)
            else:
                time.sleep(.001)
            self.continuous_reads_running = False

    def stop_continuous_reads(self):
        if not self.continuous_reads_running:
            self.logger.info("Trying to stop continuous reads, but it is not running")
            return

        self.keep_continuous_reads = False
        while self.continuous_reads_running:
            time.sleep(0.01)

    def close(self):
        self.driver.close()

    def finalize(self):
        if self.finalized:
            return

        self.stop_continuous_reads()
        self.driver.close()
        super(DigilentModel, self).finalize()
        self.finalized = True
