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
        self._stop_state = Event()
        self._finalize = Event()
        self._callbacks = []
        self._iterations = 0

        self._stop_state.set()

    def add(self, element, *elements):
        """
        Add element(s) to the pipeline

        :param element: Element to be added. Multiple elements can be passed as comma separated args
        :type element: AsrPipelineElementBase
        """
        self._elements.append(element)

        if elements:
            self._elements += elements

    def _check(self):
        """Internal method to check if the pipeline is continuous"""

        logger.info("Checking the continuity of the pipeline")
        for element in self._elements:
            if (not element._source) and (not element._sink):
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

        if not self._stop_state.is_set():
            raise Exception("Pipeline already started")

        logger.info("Trying to start the pipeline")
        element = self._source
        while element:
            element.start()
            element = element._sink

        self._stop_state.clear()
        logger.info("Successfully started pipeline")

        self._finalize.clear()

        while not self._finalize.is_set():
            if self._stop_state.is_set():
                self._set_finalize()

            element = self._source
            chunk = None
            while element:
                chunk = element.next_chunk(chunk)
                element = element._sink

            self._iterations += 1

            for callback in self._callbacks:
                callback()

        self._stop()

    def stop(self):
        """Stop the flow of data across the pipeline.

        This method calls the stop() method of each of the pipeline elements with additional consistency checks in the
        pipeline.
        """
        if self._stop_state.is_set():
            raise Exception("Cannot stop a pipeline that has not started")

        self._stop_state.set()

    def _stop(self):
        """Internal method actually stopping the pipeline"""
        self._stop_state.wait()

        logger.info("Trying to stop the pipeline")
        element = self._source
        while element:
            element.stop()
            element = element._sink

        logger.info("Successfully stopped the pipeline")

    def _set_finalize(self):
        """Finalize processing of chunks in the pipeline elements"""
        self._finalize.wait()

        element = self._source
        while element:
            element.finalize()
            element = element._sink

        self._finalize.set()

    def close(self):
        """Close the streams of the pipeline elements"""
        if not self._open_state.is_set():
            raise Exception("Pipeline not opened. First open the pipeline before closing it.")

        if not self._stop_state.is_set():
            raise Exception("Pipeline running. First stop the pipeline before closing it.")

        logger.info("Trying to close the pipeline")
        element = self._source
        while element:
            element.close()
            element = element._sink

        self._open_state.clear()
        logger.info("Successfully closed the pipeline")

    def register_callback(self, callback):
        """Register a callback

        :param callback: A function taking no args as input
        """
        self._callbacks.append(callback)
