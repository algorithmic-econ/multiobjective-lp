#include <pybind11/pybind11.h>
#include <pybind11/stl.h>

#include "methods.hpp"
#include "metrics/metrics.hpp"
#include "metrics/solved_instance.hpp"

PYBIND11_MODULE(muoblpbindings, m) {
  m.def("equal_shares_add1", &equal_shares_add1);
  m.def("equal_shares_utils", &equal_shares_utils);
  m.def("expanding_approvals", &expanding_approvals);
  m.def("single_transferable_vote", &single_transferable_vote);
  m.def("solid_coalition_refinement", &solid_coalition_refinement);

  py::module_ metrics_module =
      m.def_submodule("metrics", "Native metrics over solved instances");
  py::class_<metrics::SolvedInstance>(metrics_module, "SolvedInstance")
      .def(py::init(&metrics::SolvedInstance::from_MuoblpProblem))
      .def_property_readonly(
          "num_voters",
          [](const metrics::SolvedInstance& inst) {
            return inst.voters.size();
          })
      .def_property_readonly("num_candidates",
                             [](const metrics::SolvedInstance& inst) {
                               return inst.candidate_names.size();
                             });
  metrics_module.def("exclusion_ratio",
                     [](const metrics::SolvedInstance& inst) {
                       py::gil_scoped_release release;
                       return metrics::exclusion_ratio(inst);
                     });
  metrics_module.def(
      "ejr_plus",
      [](const metrics::SolvedInstance& inst, bool up_to_one) {
        py::gil_scoped_release release;
        return metrics::ejr_plus(inst, up_to_one);
      },
      py::arg("instance"), py::arg("up_to_one") = true);
}
