from pywr.parameters import Parameter

class ElVado_max_relase(Parameter):
    def value(self, timestep, scenario_index):
        if self.model.nodes['el_vado_inflow'].prev_flow[0]>6000*1.983:
            return 6000*1.983
        else:
            return 1000*1.983

    @classmethod
    def load(cls, model, data):
        return cls(model, **data)