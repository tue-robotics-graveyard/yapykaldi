#include <pybind11/pybind11.h>
#include <string>
#include "gmm_wrappers.h"

namespace py = pybind11;

PYBIND11_MODULE(yapykaldi, m)
{
  py::class_<kaldi::GmmOnlineModelWrapper>(m, "GmmOnlineModelWrapper")
      .def(py::init<float, int, int, float, std::string&, std::string&, std::string&,
                    std::string&>());

  py::class_<kaldi::GmmOnlineDecodeWrapper>(m, "GmmOnlineDecodeWrapper").def(py::init<>);
}
