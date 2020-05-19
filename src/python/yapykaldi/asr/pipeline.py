"""Pipeline manager class"""
from __future__ import print_function, division, absolute_import, unicode_literals
from builtins import *
from threading import Event
from ..logger import logger


class AsrPipeline(object):
    """Class AsrPipeline"""
    # pylint: disable=useless-object-inheritance

    def __init__(self):
        self._source = None
        self._sink = None
        self._elements = []
        self._open_state = Event()
        self._start_state = Event()

    def add(self, element):
        """
        Add element to the pipeline

        :param element: Element to be added
        :type element: AsrPipelineElementBase
        """
        self._elements.append(element)

    def _check(self):
        """Internal method to check if the pipeline is continuous"""

        logger.info("Checking the continuity of the pipeline")
        for element in self._elements:
            if not (element._source and element._sink):
                raise BrokenPipeError("Element with no source or sink")

            if (not element._source) and element._sink:
                self._source = element

            if element._source and (not element._sink):
                self._sink = element

        # TODO: Check the continuity of the pipeline from source to sink
        logger.info("Pipeline validated")

    def open(self):
        """Open the streams of the pipeline elements"""
        if self._open_state.is_set():
            raise Exception("Pipeline already open")

        self._check()

        logger.info("Trying to open the pipeline stream")
        element = self._source
        while element:
            element.open()
            element = element._sink

        self._open_state.set()
        logger.info("Successfully opened the pipeline stream")

    def start(self):
        """Start the flow of data across the pipeline.

        This method calls the start() and next_chunk() methods of the each of the pipeline elements with additional
        consistency checks in the pipeline.
        """
        if not self._open_state.is_set():
            raise Exception("Cannot start pipeline before opening it")

        if self._start_state.is_set():
            raise Exception("Pipeline already started")

        logger.info("Trying to start the pipeline")
        element = self._source
        while element:
            element.start()
            element = element._sink

        self._start_state.set()
        logger.info("Successfully started pipeline")

    def stop(self):
        """Stop the flow of data across the pipeline.

        This method calls the stop() method of each of the pipeline elements with additional consistency checks in the
        pipeline.
        """

    def close(self):
        """Close the streams of the pipeline elements"""
        if not self._open_state.is_set():
            raise Exception("Pipeline not opened. First open pipeline before closing it.")

        logger.info("Trying to close the pipeline")
        element = self._source
        while element:
            element.close()
            element = element._sink

        self._open_state.clear()
        logger.info("Successfully closed the pipeline")

    def register_callback(self, handle):
        """Register a callback"""
