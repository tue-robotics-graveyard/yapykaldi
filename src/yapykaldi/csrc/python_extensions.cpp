#include <pybind11/pybind11.h>
#include <string>
#include "gmm_wrappers.h"
#include "nnet3_wrappers.h"

namespace py = pybind11;

PYBIND11_MODULE(yapykaldi, m)
{
  // gmm_wrappers
  py::class_<kaldi::GmmOnlineModelWrapper>(m, "GmmOnlineModelWrapper")
      .def(py::init<float, int, int, float, std::string &, std::string &, std::string &,
                    std::string &>());

  py::class_<kaldi::GmmOnlineDecoderWrapper>(m, "GmmOnlineDecoderWrapper")
      .def(py::init<kaldi::GmmOnlineModelWrapper *>())
      .def("decode", &kaldi::GmmOnlineDecoderWrapper::decode)
      .def("get_decoded_string", &kaldi::GmmOnlineDecoderWrapper::get_decoded_string)
      .def("get_word_alignment", &kaldi::GmmOnlineDecoderWrapper::get_word_alignment);

  // nnet3_wrappers
  py::class_<kaldi::NNet3OnlineModelWrapper>(m, "NNet3OnlineModelWrapper")
      .def(py::init<float, int, int, float, float, int, std::string &, std::string &, std::string &,
                    std::string &, std::string &, std::string &>());

  py::class_<kaldi::NNet3OnlineDecoderWrapper>(m, "NNet3OnlineDecoderWrapper")
      .def(py::init<kaldi::NNet3OnlineDecoderWrapper *>())
      .def("decode", &kaldi::NNet3OnlineDecoderWrapper::decode)
      .def("get_decoded_string", &kaldi::NNet3OnlineDecoderWrapper::get_decoded_string)
      .def("get_word_alignment", &kaldi::NNet3OnlineDecoderWrapper::get_word_alignment);
}
