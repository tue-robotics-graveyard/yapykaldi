#include <stdexcept>
#include <pybind11/pybind11.h>
#include <string>
#include "gmm_wrappers.h"
#include "nnet3_wrappers.h"

namespace py = pybind11;

PYBIND11_MODULE(_Extensions, m)
{
  /*
   * gmm_wrappers
   */
  // GMM Online Model Wrapper
  py::class_<kaldi::GmmOnlineModelWrapper>(m, "GmmOnlineModelWrapper")
      .def(py::init<float, int, int, float, std::string &, std::string &, std::string &,
                    std::string &>());

  // GMM Online Decoder Wrapper
  py::class_<kaldi::GmmOnlineDecoderWrapper>(m, "GmmOnlineDecoderWrapper")
      .def(py::init<kaldi::GmmOnlineModelWrapper *>())
      .def("decode",
           [](kaldi::GmmOnlineDecoderWrapper &m, float samp_freq, py::buffer frames_buffer, bool finalize) {
             py::buffer_info info = frames_buffer.request();
             if (info.ndim != 1)
             {
               throw std::runtime_error("Incompatible buffer dimensions");
             }

             return m.decode(samp_freq, info.shape[0], static_cast<float *>(info.ptr), finalize);
           })
      .def("get_decoded_string",
           [](kaldi::GmmOnlineDecoderWrapper &m, double likelihood) {
             std::string decoded_string = "";
             m.get_decoded_string(decoded_string, likelihood);
             return std::tuple<std::string, double>(decoded_string, likelihood);
           })
      .def("get_word_alignment", &kaldi::GmmOnlineDecoderWrapper::get_word_alignment);

  /*
   * nnet3_wrappers
   */
  // NNet3 Online Model Wrapper
  py::class_<kaldi::NNet3OnlineModelWrapper>(m, "NNet3OnlineModelWrapper")
      .def(py::init<float, int, int, float, float, int, std::string &, std::string &, std::string &,
                    std::string &, std::string &, std::string &>());

  // NNet3 Online Decoder Wrapper
  py::class_<kaldi::NNet3OnlineDecoderWrapper>(m, "NNet3OnlineDecoderWrapper")
      .def(py::init<kaldi::NNet3OnlineModelWrapper *>())
      .def("decode",
           [](kaldi::NNet3OnlineDecoderWrapper &m, float samp_freq, py::buffer frames_buffer, bool finalize) {
             py::buffer_info info = frames_buffer.request();
             if (info.ndim != 1)
             {
               throw std::runtime_error("Incompatible buffer dimensions");
             }

             return m.decode(samp_freq, info.shape[0], static_cast<float *>(info.ptr), finalize);
           })
      .def("get_decoded_string",
           [](kaldi::NNet3OnlineDecoderWrapper &m, double likelihood) {
             std::string decoded_string = "";
             m.get_decoded_string(decoded_string, likelihood);
             return std::tuple<std::string, double>(decoded_string, likelihood);
           })
      .def("get_word_alignment", &kaldi::NNet3OnlineDecoderWrapper::get_word_alignment);
}
