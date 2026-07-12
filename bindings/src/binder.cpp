#include <pybind11/pybind11.h>
#include <pybind11/stl.h>

#include "methods.hpp"

PYBIND11_MODULE(muoblpbindings, m) {
  m.def("equal_shares_add1", &equal_shares_add1);
  m.def("equal_shares_utils", &equal_shares_utils);
  m.def("expanding_approvals", &expanding_approvals);
  m.def("single_transferable_vote", &single_transferable_vote);
  m.def("solid_coalition_refinement", &solid_coalition_refinement);
}
