#include "mainloop.h"
#include "mesh.h"
#include "pybind11/pybind11.h"

namespace pybind11 {
    namespace detail {
        template <>
        struct type_caster<glm::vec3> {
            PYBIND11_TYPE_CASTER(glm::vec3, io_name("Sequence[float]", "tuple[float, float, float]"));

            static handle
            cast(const glm::vec3 &vec, return_value_policy poly, handle parent) {
                return pybind11::make_tuple(vec.x, vec.y, vec.z).release();
            }

            bool load(handle src, bool what) {
                if (!pybind11::isinstance<pybind11::sequence>(src)) {
                    return false;
                }

                auto seq = pybind11::reinterpret_borrow<pybind11::sequence>(src);
                if (seq.size() != 3) {
                    return false;
                }

                for (auto item : seq) {
                    if (!pybind11::isinstance<pybind11::float_>(item) && !pybind11::isinstance<pybind11::int_>(item)) {
                        return false;
                    }
                }

                value.x = seq[0].cast<double>();
                value.y = seq[0].cast<double>();
                value.z = seq[0].cast<double>();

                return true;
            }
        };
    }
}

PYBIND11_MODULE(opengl_station, m) {
    pybind11::enum_<LoopReturn>(m, "LoopReturn")
        .value("Nothing", LoopReturn::NOTHING)
        .value("Arm", LoopReturn::ARM)
        .value("Takeoff", LoopReturn::TAKEOFF)
        .value("Step", LoopReturn::STEP)
        .value("Land", LoopReturn::LAND)
        .value("Halt", LoopReturn::HALT);

    pybind11::enum_<DroneState>(m, "DoneState")
        .value("Disconnected", DroneState::DISCONNECTED)
        .value("Connected", DroneState::CONNECTED)
        .value("Armed", DroneState::ARMED);

    m.def("setup", &setup);
    m.def("loop", &loop);
    m.def("cleanup", &cleanup);
    m.def("should_close", &shouldClose);

    m.def("set_expanse", &setExpanse);
    m.def("set_color", &setColor);
    m.def("set_pos", &setPos);
    m.def("set_ip", &setIp);
    m.def("set_state", &setState);
}

